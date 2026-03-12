
# from app.database.permissions import AccessLevelEnum
# from sqlalchemy.schema import db.Column, db.ForeignKey
# from sqlalchemy.types import db.Integer, VARCHAR, PickleType, Enum, Text
# from sqlalchemy.orm import relationship
import enum

from app import db
# class AccessLevelEnum(enum.Enum):
#         view = 'view'
#         owner = 'owner'

class AnnotationPermission(db.Model):
    __tablename__="annotation_permissions"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    annotation_set_id = db.Column(db.Integer, db.ForeignKey('annotation_sets.id'))

    access_level = db.Column('access_level', db.Enum('view','owner'), default='view')

    annotation_set = db.relationship("AnnotationSet", backref='permissions')


class Annotation(db.Model):
    __tablename__ = 'MS_annotations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    MS_id = db.Column(db.Integer, db.ForeignKey('MS.id'))
    type_id = db.Column(db.Integer, db.ForeignKey('annotations.id'))
    
    value = db.Column(db.String(100), nullable=True)


class ClusterEnum(enum.Enum):
    cluster = 'cluster'
    numeric = 'numeric'
    nominative = 'nominative'


class AnnotationType(db.Model):
    __tablename__ = 'annotations'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    set_id = db.Column(db.Integer, db.ForeignKey('annotation_sets.id'))

    name = db.Column(db.String(100), index=True)
    type = db.Column(db.Enum(ClusterEnum))

    order = db.Column(db.Integer)
    
    annotations = db.relationship(Annotation)
    

class AnnotationSet(db.Model):
    __tablename__ = 'annotation_sets'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    name = db.Column(db.String(200))

    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'))
    annotation_types = db.relationship("AnnotationType")


def get_user_annotations(annotation_set_id, exp_id, user):
    return AnnotationSet.query.join(AnnotationPermission).filter(AnnotationSet.experiment_id==exp_id, AnnotationPermission.user_id==user.id, AnnotationSet.id==annotation_set_id).first()
    

def get_user_annotation_sets(exp_id, user):
    return AnnotationSet.query.join(AnnotationPermission).filter(AnnotationSet.experiment_id==exp_id, AnnotationPermission.user_id==user.id).all()


def get_annotation_values(annotation_type_id):
    annotations = Annotation.query.filter_by(type_id=annotation_type_id)
    return annotations.value.distinct()
    

class Subset(db.Model):
    __tablename__ = 'experiment_subsets'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'))
    annotation_set_id = db.Column(db.Integer, db.ForeignKey('annotation_sets.id'))

    name = db.Column(db.String(100), index=True)
    
    foreground_query = db.Column(db.PickleType)
    background_query = db.Column(db.PickleType)

    share_token = db.Column(db.Text)
    
    def copy(self):
        c = Subset()
        c.owner_id = self.owner_id
        c.experiment_id = self.experiment_id
        c.annotation_set_id = self.annotation_set_id

        c.name = self.name

        c.foreground_query = self.foreground_query
        c.background_query = self.background_query
        c.share_token = None
        return c

def get_subset_by_share_token(share_token):
    return Subset.query.filter_by(share_token=share_token).first()

def get_subset_by_name(exp_id, subset_name, user):
    return Subset.query.filter_by(experiment_id=exp_id, owner_id=user.id, name=subset_name).first()

def get_subset_by_id(subset_id, exp_id):
    return Subset.query.filter_by(id=subset_id, experiment_id=exp_id).first()

def get_subsets_for_user(exp_id, user):
    return Subset.query.filter_by(experiment_id=exp_id, owner_id=user.id).all()
