import logging
from logging.handlers import SMTPHandler, TimedRotatingFileHandler
import os
from flask import Flask, request, current_app
from flask.logging import default_handler
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from .celery_utils import init_celery
from kombu.utils.url import safequote
from flask_mail import Mail
# from flask_bootstrap import Bootstrap
# from flask_moment import Moment
# from flask_babel import Babel, lazy_gettext as _l
# from elasticsearch import Elasticsearch
# import rq
from config import Config
from celery import Celery

access_key = Config.CELERY_ACCESS_KEY
secret_key = Config.CELERY_SECRET_ACCESS_KEY
queue_url = Config.QUEUE_URL
broker_transport_options = {
    'predefined_queues': {
        'celery': {
            'url': queue_url,
            'access_key_id': access_key,
            'secret_access_key': secret_key,
        }
    }
}

def make_celery(app_name=__name__):
    result_backend = Config.result_backend
    aws_access_key = safequote(access_key)
    aws_secret_key = safequote(secret_key)
    broker_url = "sqs://{aws_access_key}:{aws_secret_key}@".format(
        aws_access_key=aws_access_key, aws_secret_key=aws_secret_key,
    )
    celery = Celery(app_name, backend=result_backend, broker=broker_url, )
    return celery

celery = make_celery()
celery.conf['broker_transport_options']=broker_transport_options
#db = SQLAlchemy() # altering this to use the engine_options parameter to set pool_recycle and pool_pre_ping to ensure connection 
db = SQLAlchemy(engine_options={"pool_recycle": 3600, "pool_pre_ping": True})
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Please log in to access this page.'

logger = logging.getLogger()

logFormatter = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s %(threadName)s : %(module)s >>> %(message)s")

# Create and add a console handler to root logger
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)

# Create and add a rotating file handler to root logger
# if os.path.exists("logs/proteomescout.log")==False:
#     os.makedirs('logs')
#     with open('logs/proteomescout.log', 'w') as fp:
#         pass
# creating mail 
mail = Mail() 
fileHandler = TimedRotatingFileHandler("logs/proteomescout.log", backupCount=100, when="midnight")
fileHandler.setFormatter(logFormatter)
fileHandler.namer = lambda name: name.replace(".log", "") + ".log"
logger.addHandler(fileHandler) 

def create_app(config_class=Config, celery=celery):
    app = Flask(__name__)
    app.config.from_object(config_class)

    init_celery(celery, app)
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    # configure_logging(app)
    mail.init_app(app) # adding mail to app 
    # bootstrap.init_app(app)
    # moment.init_app(app)
    # babel.init_app(app)
    # app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) \
    #     if app.config['ELASTICSEARCH_URL'] else None
    # app.redis = Redis.from_url(app.config['REDIS_URL'])
    # app.task_queue = rq.Queue('proteomescout-tasks', connection=app.redis)

    if (app.config['DEBUG']):
        app.debug = True
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    app.logger.setLevel(log_level)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.main.views.info import bp as info_bp
    app.register_blueprint(info_bp)

    from app.main.views.accounts import bp as accounts_bp
    app.register_blueprint(accounts_bp, url_prefix='/account')

    from app.main.views.proteins import bp as protein_bp
    app.register_blueprint(protein_bp, url_prefix = '/proteins')

    from app.main.views.batch import bp as batch_bp
    app.register_blueprint(batch_bp, url_prefix = '/batch')

    from app.main.views.experiments import bp as exp_bp
    app.register_blueprint(exp_bp, url_prefix = '/experiments')

    from app.main.views.upload import bp as upload_bp
    app.register_blueprint(upload_bp, url_prefix = '/upload')

    from app.main.views.files import bp as  compendia_bp
    app.register_blueprint(compendia_bp, url_prefix = '/compendia')

    from app.main.views.kstar import bp as kstar_bp
    app.register_blueprint(kstar_bp, url_prefix = '/kstar')


    # from app.api import bp as api_bp
    # app.register_blueprint(api_bp, url_prefix='/api')
    
    # if not app.debug and not app.testing:
    #     if app.config['MAIL_SERVER']:
    #         auth = None
    #         if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
    #             auth = (app.config['MAIL_USERNAME'],
    #                     app.config['MAIL_PASSWORD'])
    #         secure = None
    #         if app.config['MAIL_USE_TLS']:
    #             secure = ()
    #         mail_handler = SMTPHandler(
    #             mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
    #             fromaddr='no-reply@' + app.config['MAIL_SERVER'],
    #             toaddrs=app.config['ADMINS'], subject='Microblog Failure',
    #             credentials=auth, secure=secure)
    #         mail_handler.setLevel(logging.ERROR)
    #         app.logger.addHandler(mail_handler)

    #     if app.config['LOG_TO_STDOUT']:
    #         stream_handler = logging.StreamHandler()
    #         stream_handler.setLevel(logging.INFO)
    #         app.logger.addHandler(stream_handler)
    #     else:
    #         if not os.path.exists('logs'):
    #             os.mkdir('logs')
    #         file_handler = RotatingFileHandler('logs/proteomescout.log',
    #                                            maxBytes=10240, backupCount=10)
    #         file_handler.setFormatter(logging.Formatter(
    #             '%(asctime)s %(levelname)s: %(message)s '
    #             '[in %(pathname)s:%(lineno)d]'))
    #         file_handler.setLevel(logging.INFO)
    #         app.logger.addHandler(file_handler)

    #     app.logger.setLevel(logging.INFO)
    app.logger.info('Proteomescout startup')

    return app

# def configure_logging(app):
    
#     app.logger.removeHandler(default_handler)

#     logFormatter = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s %(threadName)s : %(module)s >>> %(message)s")

#     # Create and add a console handler to root logger
#     consoleHandler = logging.StreamHandler()
#     consoleHandler.setFormatter(logFormatter)
#     app.logger.addHandler(consoleHandler)

#     # Create and add a rotating file handler to root logger
#     fileHandler = TimedRotatingFileHandler("logs/proteomescout.log", backupCount=100, when="midnight")
#     fileHandler.setFormatter(logFormatter)
#     fileHandler.namer = lambda name: name.replace(".log", "") + ".log"
#     app.logger.addHandler(fileHandler)    

app = create_app()

# mail = Mail()
# bootstrap = Bootstrap()
# moment = Moment()
# babel = Babel()

# @babel.localeselector
# def get_locale():
#     return request.accept_languages.best_match(current_app.config['LANGUAGES'])


# import worker files here if you want them to show up in celery as registered tasks
from app.main.views.proteins.search import perform_queries
from proteomescout_worker import notify_tasks, export_tasks
from app.utils.email import send_email_with_logs
from app.database import user

# except Exception as ex:
#         app.log_exception(ex)
#         print(ex)
#         raise ex

# try:
#       return make_response(jsonify("User block request      submitted"), 200)
# except Exception as ex:
#             app.log_exception(ex)
#             return make_response(jsonify(
#                 {
#                     "status": "error",
#                     "message": "Couldn't handle user block request: "+str(ex)
#                 }
#), 400)