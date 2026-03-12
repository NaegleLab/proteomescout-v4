from app import db
# from app.config import settings as config
from app.database.permissions import Permission
from app.config import settings as config

import datetime

import enum


experiment_PTM = db.Table('experiment_PTM', 
                    db.Column('id', db.Integer, primary_key=True, autoincrement=True),
                    db.Column('experiment_id', db.Integer, db.ForeignKey('experiment.id')),
                    db.Column('PTM_id', db.Integer, db.ForeignKey('PTM.id')))


class PermissionException(Exception):
    def __init__(self, msg=''):
        self.msg = msg

    def __repr__(self):
        return self.msg


class ExperimentError(db.Model):
    __tablename__ = 'experiment_error'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    experiment_id = db.Column(db.Integer, db.ForeignKey("experiment.id"))
    line = db.Column(db.Integer)

    accession = db.Column(db.String(45))
    peptide = db.Column(db.String(150))
    
    message = db.Column(db.Text)


class ExperimentTypeEnum(enum.Enum):
    cell = 'cell'
    tissue = 'tissue'
    drug = 'drug'
    stimulus = 'stimulus'
    environment = 'environment'


class ExperimentCondition(db.Model):
    __tablename__ = 'experiment_condition'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    type = db.Column(db.Enum('cell','tissue','drug','stimulus','environment'))
    value = db.Column(db.String(100))
    
    experiment_id = db.Column(db.Integer, db.ForeignKey("experiment.id"))


# class DataTypeEnum(enum.Enum):
#     data = 'data'
#     stdev = 'stddev'


class ExperimentData(db.Model):
    __tablename__ = 'MS_data'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    type = db.Column(db.Enum('data','stddev'), default='data')
    units = db.Column(db.String(20), default='time')
    run = db.Column(db.String(20), default='average')
    label = db.Column(db.String(45), default='')
    
    priority = db.Column(db.Integer, default=0)
    value = db.Column(db.Float)
    
    MS_id = db.Column(db.Integer, db.ForeignKey('MS.id'))
    MS = db.relationship("MeasuredPeptide")
        
    def __format_name(self):
        return "%s:%s:%s" % (self.run, self.type, self.label)
    
    formatted_label = property(__format_name)
    

# class MonthEnum(enum.Enum):
#     blank = ''
#     january = 'january'
#     february = 'february'
#     march = 'march'
#     april = 'april'
#     may = 'may'
#     june = 'june'
#     july = 'july'
#     august = 'august'
#     september = 'september'
#     october = 'october'
#     november = 'november'
    # december = 'december'


# class ExperimentEnum(enum.Enum):
#     compendia = 'compendia'
#     experiment = 'experiment'
#     dataset = 'dataset'


class Experiment(db.Model):
    __tablename__ = 'experiment'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    name = db.Column(db.Text)
    author = db.Column(db.Text)
    date = db.Column(db.DateTime)
    
    description = db.Column(db.Text)
    contact = db.Column(db.String(45))
    
    PMID = db.Column(db.Integer)
    URL = db.Column(db.Text)
    published = db.Column(db.Integer)
    
    ambiguity = db.Column(db.Integer)
    experiment_id = db.Column(db.Integer, db.ForeignKey("experiment.id"), default=None)
    
    dataset = db.Column(db.Text)
    
    volume = db.Column(db.Integer)
    page_start = db.Column(db.String(10))
    page_end = db.Column(db.String(10))
    journal = db.Column(db.String(45))
    publication_year = db.Column(db.Integer)
    publication_month = db.Column(db.Enum('','january','february','march','april','may','june','july','august','september','october','november','december'))
    
    public = db.Column(db.Integer, default=0)
    
    job_id = db.Column(db.Integer)
    submitter_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    modified_residues = db.Column(db.String(40), default="")
    type = db.Column(db.Enum('compendia', 'experiment', 'dataset'), default='experiment')
  
    version_number = db.Column(db.Integer)

    def __repr__(self):
        return 'experiment:%d:%d' % (self.id, self.version_number)

    def __get_job(self):
        from app.database import jobs

        if self.job_id is None:
            return None

        if not hasattr(self, '__job_obj'):
            self.__job_obj = jobs.get_job_by_id(self.job_id)
        
        return self.__job_obj
        
    job = property(__get_job)
    
    errors = db.relationship("ExperimentError", cascade="all,delete-orphan")
    conditions = db.relationship("ExperimentCondition", cascade="all,delete-orphan")
    permissions = db.relationship("Permission", backref="experiment", cascade="all,delete-orphan")
    measurements = db.relationship("MeasuredPeptide")
    modifications = db.relationship("PTM", secondary=experiment_PTM)

    parent = db.relationship("Experiment", backref='children', remote_side=[id])
    
    def __init__(self):
        self.date = datetime.datetime.now()
        self.version_number = 0

    def save_experiment(self):
        db.session.add(self)
        self.version_number += 1
        db.session.commit()
       # to remove temporary experiments (ie batch search) 
    def delete(self):
        db.session.delete(self)
        db.session.commit()
        
    def copy_data(self, exp):
        self.name = exp.name
        self.author = exp.author
        self.date = exp.date
        
        self.description = exp.description
        self.contact = exp.contact
        
        self.PMID = exp.PMID
        self.URL = exp.URL
        self.published = exp.published
        
        self.ambiguity = exp.ambiguity
        self.experiment_id = exp.experiment_id
        
        self.dataset = exp.dataset
        
        self.volume = exp.volume
        self.page_start = exp.page_start
        self.page_end = exp.page_end
        self.journal = exp.journal
        self.publication_year = exp.publication_year
        self.publication_month = exp.publication_month
        
        self.public = exp.public
        self.type = exp.type
        
        self.submitter_id = exp.submitter_id
        self.job_id = None
        
        self.conditions = []
        for c in exp.conditions:
            expc = ExperimentCondition()
            expc.type = c.type
            expc.value = c.value
            
            self.conditions.append(expc)
            
    def is_experiment(self):
        return self.type in set(['compendia', 'experiment'])
            
    def clear_errors(self):
        self.errors = []

    def get_citation_string(self):
        string = ""
        if self.published == 1:
            if self.journal != "" and self.journal is not None:
                string += self.journal + ". "
            if self.publication_year is not None:
                string += str(self.publication_year)
                if self.publication_month is not None:
                    string += "-" + self.publication_month.capitalize()
                string += ". "
            if self.volume != "" and self.volume is not None:
                string += "Vol " + str(self.volume) + ". "
            if self.page_start is not None:
                string += self.page_start

                if self.page_end is not None and self.page_end != self.page_start:
                    if len(self.page_start) == len(self.page_end):
                        string += "-" + self.__getPageEndFormatted()
                    else:
                        string += "-" + self.page_end

                string += "."
        return string
    
    def __getPageEndFormatted(self):
        i = 0
        while(self.page_start[i] == self.page_end[i]):
            i += 1
        return self.page_end[i:]
    
    def get_long_citation_string(self):
        cite_string = ""
        if self.published == 1:
            if self.author != "":
                cite_string += self.author + ". "
            if self.journal != "":
                cite_string += self.journal + ". "
            if self.publication_year is not None:
                cite_string += str(self.publication_year)
                if self.publication_month is not None:
                    cite_string += "-" + self.publication_month.capitalize()
                cite_string += ". "
            if self.volume is not None:
                cite_string += "Vol " + str(self.volume)+". "
            if self.page_start is not None:
                cite_string += self.page_start

                if self.page_end is not None and self.page_end != self.page_start:
                    if len(self.page_start) == len(self.page_end):
                        cite_string += "-" + self.__getPageEndFormatted()
                    else:
                        cite_string += "-" + self.page_end

                cite_string += "."
        return cite_string
   
    def has_PMID(self):
        return self.PMID is not None

    def get_pubmed_url(self):
        return config.pubmedUrl % (self.PMID)

    def get_url(self):
        url = self.URL
        if url == "NA":
            url = None
        
        if url is not None:
            return url
        elif self.PMID is not None:
            return self.get_pubmed_url()
        
        return None
    
    def grant_permission(self, user, level):
        found = False
        for p in self.permissions:
            if p.user_id == user.id:
                p.access_level = level
                found = True
        
        if not found:
            p = Permission(self, level)
            p.user = user
            p.access_level = level
            self.permissions.append(p)

    def revoke_permission(self, user):
        perm = None
        for p in self.permissions:
            if p.user_id == user.id:
                perm = p
        if perm is not None:
            self.permissions.remove(perm)

    def __get_status(self):
        if self.job is None:
            return 'configuration'
        return self.job.status
    
    def __get_stage(self):
        if self.job is None:
            return ''
        return self.job.stage
    
    status = property(__get_status)
    loading_stage = property(__get_stage)
    
    def ready(self):
        if self.job is not None:
            return self.job.status == 'finished'  
        return False
        
    def makePublic(self):
        if self.experiment_id is not None:
            if self.parent.public != 1:
                raise PermissionException()
        self.public = 1
        
    def make_private(self):
        for child in self.children:
            if child.public == 1:
                raise PermissionException()
        self.public = 0
        
    def is_owner(self, user):
        if user is None:
            return False
        
        owner_users = [p.user_id for p in self.permissions if p.access_level == 'owner']
        return user.id in owner_users
        
    def check_permissions(self, user):
        if self.public == 1:
            return True
        
        if user is None:
            return False
        
        allowed_users = [p.user_id for p in self.permissions]
        return user.id in allowed_users
    
    def has_experiment_condition(self, ctype, value):
        for cond in self.conditions:
            if cond.type == ctype and cond.value == value:
                return True    
        return False
    
    def add_experiment_condition(self, ctype, value):
        if self.has_experiment_condition(ctype, value):
            return 
        
        condition = ExperimentCondition()
        condition.type = ctype
        condition.value = value
        self.conditions.append(condition)

    def get_clickable(self, request, new_window=False):
        url = None
        if self.type == 'experiment':
            url = request.route_url('experiment', id=self.id)
        elif self.URL and self.URL != '':
            url = self.URL

        if url:
            return '<a href="%s" %s>%s</a>' % ( url, 'target="_blank"' if new_window else '', self.name)

        return self.name


class NoSuchExperiment(Exception):
    def __init__(self, eid):
        self.eid = eid
    
    def __str__(self):
        return "No such experiment: %d" % (self.eid)


class ExperimentAccessForbidden(Exception):
    def __init__(self, eid):
        self.eid = eid
    
    def __str__(self):
        return "Current user does not have access privileges to experiment %d" % (self.eid)


class ExperimentNotAvailable(Exception):
    def __init__(self, eid):
        self.eid = eid
    
    def __str__(self):
        return "Experiment %d is still being processed for upload" % (self.eid)
    

def get_experiment_by_id(experiment_id, user=None, check_ready=True, secure=True):
    value = Experiment.query.filter_by(id=experiment_id).first()
    if value is None:
        raise NoSuchExperiment(experiment_id)

    if secure and not value.check_permissions(user):
        raise ExperimentAccessForbidden(experiment_id)
    
    if check_ready and not value.ready():
        raise ExperimentNotAvailable(experiment_id)
    
    return value


def get_all_experiments(current_user, filter_compendia=True, filter_datasets=True):
    
    exps = [ exp for exp in db.session.query(Experiment).all() if exp.check_permissions(current_user) and exp.ready() ]

    if filter_compendia:
        exps = [exp for exp in exps if exp.type != 'compendia']

    if filter_datasets:
        exps = [exp for exp in exps if exp.type != 'dataset']

    return sorted(exps, key=lambda item: item.name)


def recursive_append(exp, tree, experiments, lp=None):
    available = exp in experiments

    if available:
        tree.append(exp)
        if lp is not None:
            exp.experiment_id = lp.id
        else:
            exp.experiment_id = None

        lp = exp
        experiments.remove(exp)

    for child in exp.children:
        recursive_append(child, tree, experiments, lp=lp)


def get_experiment_tree(current_user):
    experiments = get_all_experiments(current_user)
    root_experiments = [ exp for exp in experiments if exp.experiment_id is None ]
    experiment_tree = []

    while len(root_experiments) > 0:
        exp = root_experiments.pop(0)
        recursive_append(exp, experiment_tree, experiments)

    return experiment_tree
    
def get_values_for_field(field_name):
    results = ExperimentCondition.query.filter(ExperimentCondition.type==field_name).distinct()
    return sorted([ r.value for r in results ])

def count_errors_for_experiment(exp_id):
    return ExperimentError.query.filter_by(experiment_id=exp_id).count()

def create_experiment_error(exp_id, line, accession, peptide, message):
    err = ExperimentError()
    err.experiment_id = exp_id
    err.line = line
    err.accession = accession
    err.peptide = peptide
    err.message = message
    
    # DBSession.add(err)

def errors_for_accession(exp_id, accession):
    return ExperimentError.query.filter_by(experiment_id=exp_id, accession=accession).all()

# def searchExperiments(text_search=None, conditions={}, user=None, page=None):
#     q = Experiment.id.outerjoin(Experiment.conditions).outerjoin(Experiment.permissions)

#     filter_clauses = [ Experiment.type != 'dataset' ]
#     if user:
#         filter_clauses.append( or_( Experiment.public==1, Permission.user_id==user.id ) )
#     else:
#         filter_clauses.append( Experiment.public == 1 )

#     if text_search:
#         text_search = '%' + str(text_search) + '%'
#         filter_clauses.append( or_( Experiment.name.like(text_search), Experiment.description.like(text_search) ) )

#     for cond_type in conditions:
#         for cond_value in conditions[cond_type]:
#             filter_clauses.append( and_( ExperimentCondition.type==cond_type, ExperimentCondition.value==cond_value ) )

#     if len(filter_clauses) > 0:
#         filter_clause = and_(*filter_clauses)
#     else:
#         filter_clause = filter_clauses[0]

#     q = q.filter( filter_clause ).distinct().order_by( Experiment.name )

#     if page==None:
#         sq = q.subquery()
#     else:
#         limit, offset = page
#         sq = q.limit(limit).offset(offset).subquery()

#     fq = DBSession.query(Experiment).join(sq, Experiment.id == sq.c.id)
#     return q.count(), fq.all()

def count_experiments():
    exps = [ exp for exp in Experiment.query.all() if exp.ready() ]

    compendia = len([ exp for exp in exps if exp.type == 'compendia' and exp.public==1 ])
    experiments = len([ exp for exp in exps if exp.type == 'experiment' and exp.public==1 ])
    datasets = len([ exp for exp in exps if exp.type == 'dataset' ])

    return compendia, experiments, datasets

