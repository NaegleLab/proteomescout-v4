# from app.database import Base, DBSession
# from sqlalchemy.schema import db.Column, db.ForeignKey
# from sqlalchemy.types import db.Integer, Enum, VARCHAR
# from sqlalchemy.orm import relationship
from app import db
import enum

    
class Permission(db.Model):
    __tablename__="permissions"
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'), primary_key=True)
    access_level = db.Column('access_level', db.Enum('view','owner'), default='view')
    
    def __init__(self, experiment, access_level='view'):
        self.experiment = experiment
        self.access_level = access_level

class Invitation(db.Model):
    __tablename__ = "invitations"
    invited_email = db.Column(db.VARCHAR(50), primary_key=True)
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'), primary_key=True)
    inviting_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    experiment = db.relationship("Experiment")
    
    def __init__(self, invited_email, experiment_id, inviting_user_id):
        self.invited_email = invited_email
        self.experiment_id = experiment_id
        self.inviting_user_id = inviting_user_id
        


def get_invitations_for_user(email):
    return db.session.query(Invitation).filter_by(invited_email=email).all()