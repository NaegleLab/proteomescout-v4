# from app.database import Base, DBSession
# from sqlalchemy.types import db.String, db.Integer, Enum, Text, db.DateTime
# from sqlalchemy.schema import db.Column, ForeignKey
# from sqlalchemy.orm import relationship
from app import db
import os
# from app.config import settings
from app.utils import crypto
import pickle
import enum
from sqlalchemy import Enum 
import datetime
import time 
from app import current_app
import jwt 


class CachedResult(db.Model):
    __tablename__ = 'cache'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    function = db.Column(db.String(100))
    hash_args = db.Column(db.String(64))
    started = db.Column(db.DateTime)
    finished = db.Column(db.DateTime, nullable=True)

    def __init__(self, fn, args):
        self.function = "%s.%s" % (fn.__module__, fn.__name__)
        repr_args = canonicalize_arguments(args)
        self.hash_args = crypto.md5(repr_args)
        self.started = datetime.datetime.now()
        self.finished = None

    def restart(self):
        self.started = datetime.datetime.now()
        self.finished = None

    # def delete(self):
    #     DBSession.delete(self)

    #     fn = self.get_location()
    #     if(os.path.exists(fn)):
    #         os.remove(fn)


    # def is_expired(self):
    #     delta = datetime.datetime.now() - self.finished
    #     return delta.total_seconds() > settings.cache_expiration_time

    # def get_location(self):
    #     dirpath = os.sep.join([settings.ptmscout_path, settings.cache_storage_directory, self.function])
    #     if not os.path.exists(dirpath):
    #         os.mkdir(dirpath)
    #     return os.sep.join([dirpath, self.hash_args + ".pyp"])

    def load_result(self):
        fn = self.get_location()
        with open(fn, 'rb') as pypfile:
            return pickle.load(pypfile)

    def store_result(self, result):
        fn = self.get_location()
        with open(fn, 'wb') as pypfile:
            pickle.dump(result, pypfile)
        self.finished = datetime.datetime.now()

def canonicalize_arguments(args):
    rargs = []
    for a in args:
        if isinstance(a, list):
            a = sorted(canonicalize_arguments(a))
        else:
            a = repr(a)

        rargs.append(a)
    return repr(rargs)

def getCachedResult(fn, args):
    function_np = "%s.%s" % (fn.__module__, fn.__name__)
    search_args = canonicalize_arguments(args)
    md5_args = crypto.md5(search_args)
    result = CachedResult.query.filter_by(function=function_np, hash_args=md5_args).first()
    return result

class JobStatusEnum(enum.Enum):
    configuration = 'configuration'
    in_queue = 'in queue'
    started = 'started'
    finished = 'finished'
    error = 'error'

class JobTypeEnum(enum.Enum):
    load_experiment = 'load_experiment'
    load_annotations = 'load_annotations'
    load_dataset = 'load_dataset'
    mcam_enrichment = 'mcam_enrichment'
    batch_annotate = 'batch_annotate'


class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    status = db.Column(Enum('configuration', 'in queue', 'started', 'finished', 'error', name = 'jobstatusenum'), 
                       default='configuration')
    failure_reason = db.Column(db.Text, default="")
    
    stage = db.Column(db.String(20))
    progress = db.Column(db.Integer)
    max_progress = db.Column(db.Integer)
    
    status_url = db.Column(db.String(250), nullable=True)
    resume_url = db.Column(db.String(250), nullable=True)
    result_url = db.Column(db.String(250), nullable=True)
    
    name = db.Column(db.String(250))
    type = db.Column(db.Enum('load_experiment','load_annotations','load_dataset','mcam_enrichment','batch_annotate'))
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("User", backref='jobs')
    
    created = db.Column(db.DateTime)
    restarted = db.Column(db.DateTime, nullable=True)
    finished = db.Column(db.DateTime, nullable=True)

    def __init__(self):
        self.created = datetime.datetime.now()
        
        self.max_progress = 0
        self.progress = 0
        self.stage = 'initializing'
        self.status = 'configuration'
        
    def started(self):
        if self.restarted == None:
            return self.created
        return self.restarted
    
    def finished_time(self):
        if self.finished == None:
            return "-"
        return self.finished
    
    def restart(self):
        self.restarted = datetime.datetime.now()
    
    def fail(self, stack_trace):
        self.failure_reason = stack_trace
        self.status = JobStatusEnum.error.value
        self.finished = datetime.datetime.now()

    def is_active(self):
        return self.status not in [JobStatusEnum.error, JobStatusEnum.finished]
    # functions that will be used if we implement a download url token system 
    # instead of emailing downloads directly to the user
    def get_download_token(self, expires_in=3600):
        return jwt.encode(
            {'download': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_download_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['download']
        except:
            return None
        return Job.query.get(id)
    
    # def is_old(self):
    #     if self.finished == None:
    #         return False
    #     delta = datetime.datetime.now() - self.finished
    #     return delta.total_seconds() > settings.JOB_AGE_LIMIT

    def finish(self):
        self.failure_reason = ''
        self.status = JobStatusEnum.finished.value
        self.finished = datetime.datetime.now()
        
    def save(self):
        db.session.add(self)
        db.session.commit()
        
class NoSuchJob(Exception):
    def __init__(self, jid):
        self.jid = jid

    def __str__(self):
        return "No such job: %s" % (str(self.jid))


def get_job_by_id(jid):
    job = Job.query.filter_by(id=jid).first()
    if job is None:
        raise NoSuchJob(jid)
    return job
