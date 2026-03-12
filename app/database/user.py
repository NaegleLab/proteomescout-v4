from app import db, login
from app.utils import crypto
import datetime
import enum
import jwt
from time import time 
from app import current_app

from flask_login import UserMixin

class UserAccessLevelEnum(enum.Enum):
    reviewer = 'reviewer'
    researcher = 'researcher'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # credentials
    username = db.Column(db.String(30), unique=True)
    salted_password = db.Column(db.String(64))
    salt = db.Column(db.String(10))
    
    # user data
    name = db.Column(db.String(50))
    email = db.Column(db.String(50), unique=True)
    institution = db.Column(db.String(100))
    date_created = db.Column(db.DateTime, default = datetime.datetime.utcnow())
    
    # activation data
    active = db.Column(db.Integer, default=0)
    activation_token = db.Column(db.String(50))
    
    access_level = db.Column(db.Enum('reviewer','researcher'))
    expiration = db.Column(db.DateTime)

    permissions = db.relationship("Permission", backref="user")
    # annotation_sets = db.relationship("AnnotationPermission")

    # def __repr__(self):
    #     return 'users:%d' % (self.id)

    def __init__(self, username="", name="", email="", institution="", access_level='researcher'):
        self.username = username
        self.name = name
        self.email = email
        self.institution = institution
        self.access_level = access_level
        # self.permissions = []
    

    def check_password(self, password):
        _, salted_password = crypto.saltedPassword(password, self.salt)
        return salted_password == self.salted_password

    def set_password(self, password):
        self.salt, self.salted_password = crypto.saltedPassword(password)

    # def can_view_annotations(self, annotation_set_id):
    #     return reduce(bool.__or__, [ap.annotation_set_id == annotation_set_id for ap in self.annotation_sets], False)

    def is_expired(self):
        if self.expiration != None:
            now = datetime.datetime.now()
            if self.expiration < now:
                return True
        return False    
        
    def set_expiration(self, delta):
        n = datetime.datetime.now()
        d = datetime.timedelta(delta)
        self.expiration = n + d
        
    # def save_user(self):
    #     DBSession.add(self)
    #     DBSession.flush()
        
    def set_active(self):
        self.active = 1
        
    def create_user(self, password):
        self.salt, self.salted_password = crypto.saltedPassword(password)
        self.activation_token = crypto.generateActivationToken()
        
    def my_experiments(self):
        return [ permission.experiment \
                    for permission in self.permissions \
                        if permission.access_level == 'owner' and permission.experiment.is_experiment() ]
        
    # def my_datasets(self):
    #     return [ permission.experiment \
    #                 for permission in self.permissions \
    #                     if permission.access_level == 'owner' and not permission.experiment.isExperiment() ]

        
    def experiment_owner(self, exp):
        result = [ permission.experiment \
                        for permission in self.permissions \
                            if permission.access_level == 'owner' and permission.experiment.id == exp.id]
        return len(result) > 0
    
    def all_experiments(self):
        return [ permission.experiment for permission in self.permissions ]

    
    def process_invitations(self):
        pass
    #     invites = permissions.getInvitationsForUser(self.email)
        
    #     for invite in invites:
    #         np = permissions.Permission(invite.experiment)
    #         np.user_id = self.id
    #         self.permissions.append(np)
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return db.session.query(User).get(id)
    
    
        
    
    
        
# class NoSuchUser(Exception):
#     def __init__(self, uid=None, username=None, email=None):
#         self.uid = uid
#         self.username = username
#         self.email = email
#     def __str__(self):
#         value = ""
#         if self.uid != None:
#             value = str(self.uid)
#         if self.username != None:
#             value = str(self.username)
#         if self.email != None:
#             value = str(self.email)
        
#         return "Could not find user %s" % value

# def getUserByRequest(request):
#     username = security.authenticated_userid(request)
#     if username is not None:
#         try:
#             return getUserByUsername(username)
#         except NoSuchUser:
#             return None
#     return None

# def getUsernameByRequest(request):
#     return security.authenticated_userid(request)

class NoSuchUser(Exception):
    def __init__(self, uid):
        self.uid = uid

    def __str__(self):
        return "No such user: %s" % (str(self.uid))

def get_user_by_id(jid):
    job = User.query.filter_by(id=jid).first()
    if job is None:
        raise NoSuchUser(jid)
    return job

def load_user_by_username(username):
    return User.query.filter_by(username=username).first()

def load_user_by_email(email):
    return User.query.filter_by(email=email).first()
    
@login.user_loader
def load_user_by_id(uid):
    return User.query.filter_by(id=uid).first()
     
def count_users():
    return User.query.count()
