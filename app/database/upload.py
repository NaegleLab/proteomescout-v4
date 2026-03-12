# from app.database import Base, DBSession
# from sqlalchemy.schema import db.Column, db.ForeignKey
# from sqlalchemy.types import db.Integer, db.VARCHAR, Enum, Text, DateTime
# from sqlalchemy.orm import relationship

from app import db
import datetime
import enum

# class SessionTypeEnum(enum.Enum):
#     hidden = 'hidden'
#     data = 'data'
#     stddev = 'stddev'
#     accession = 'accession'
#     peptide = 'peptide'
#     sites = 'sites'
#     speciese = 'species'
#     modification = 'modification'
#     run = 'run'
#     none = 'none'
#     numeric = 'numeric'
#     nominative = 'nominative'
#     cluster = 'cluster'


class SessionColumn(db.Model):
    __tablename__ = 'session_columns'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'))
    
    type = db.Column(db.Enum('hidden','data','stddev','accession','peptide','sites','species','modification','run', 'none','numeric','nominative','cluster'), default='none')
    label = db.Column(db.VARCHAR(45), default='')
    column_number = db.Column(db.Integer)


# class ResourceTypeEnum(enum.Enum):
#     experiment = 'experiment'
#     annotations = 'annotations'
#     dataset = 'dataset'

# class LoadTypeEnum(enum.Enum):
#     new = 'new'
#     reload = 'reload'
#     append = 'append'
#     extension = 'extension'

# class SessionStageEnum(enum.Enum):
#     config = 'config'
#     metadata = 'metadata'
#     confirm = 'confirm'
#     condition = 'condition'
#     complete = 'complete'


class Session(db.Model):
    __tablename__ = 'session'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    data_file = db.Column(db.VARCHAR(100))
    
    resource_type = db.Column(db.Enum('experiment','annotations','dataset'))
    load_type = db.Column(db.Enum('new','reload','append','extension'))
    
    parent_experiment = db.Column(db.Integer, db.ForeignKey('experiment.id'))
    change_name = db.Column(db.Text)
    change_description = db.Column(db.Text)
    units = db.Column(db.VARCHAR(20), default='')
    
    stage = db.Column(db.Enum('config','metadata','confirm','condition', 'complete'))
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'))
    date = db.Column(db.DateTime)
    
    columns = db.relationship("SessionColumn", cascade="all,delete-orphan", lazy="joined")
        
    def __init__(self):
        self.date = datetime.datetime.now()
    
    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        sb.session.commit()
        
    def get_ancestor(self):
        ancestors = db.session.query(Session).filter(Session.experiment_id==self.parent_experiment).all()
        ancestors.sort(key=lambda session: session.date, reverse=True)
        return ancestors[0]

    def get_columns(self, tp):
        found_columns = []
        for col in self.columns:
            if col.type == tp:
                found_columns.append(col)
        
        return found_columns
            
class NoSuchSession(Exception):
    pass


class SessionAccessForbidden(Exception):
    pass

def get_most_recent_session(exp_id):
    ancestors = db.session.query(Session).filter(Session.experiment_id==exp_id).all()
    ancestors.sort(key=lambda session: session.date, reverse=True)
    return ancestors[0]

def get_session_by_id(session_id, user=None, secure=True):
    session = db.session.query(Session).filter_by(id=session_id).first()
    
    if session is None:
        raise NoSuchSession()
    
    if secure and (user is None or session.user_id != user.id):
        raise SessionAccessForbidden()
         
    
    return session
