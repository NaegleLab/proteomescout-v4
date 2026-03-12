import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    DEBUG = os.environ.get('DEBUG') or False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    MAIL_SERVER = os.environ.get('SMTP_HOST') #os.environ.get('MAIL_SERVER') #or "smtp.gmail.com" # setting up automated email to new google account for test 
    MAIL_PORT = int(os.environ.get('SMTP_PORT', '587'))  # Default to 587 if SMTP_PORT is not set
    MAIL_USE_SSL = False #os.environ.get('MAIL_USE_SSL') # False is not None
    MAIL_USE_TLS = True #os.environ.get('MAIL_USE_TLS') # True is not None
    MAIL_USERNAME = None #os.environ.get('MAIL_USERNAME')# or "proteomescout3mail@gmail.com"
    MAIL_PASSWORD = os.environ.get('SMTP_CLIENT_SECRET') #os.environ.get('MAIL_PASSWORD')# or "kezmuk-roXsy3-tockec"
    ADMINS = ['proteomescout3mail@gmail.com'] #['your-email@example.com']
    LANGUAGES = ['en', 'es']
    MS_TRANSLATOR_KEY = os.environ.get('MS_TRANSLATOR_KEY')
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'
    POSTS_PER_PAGE = 25
    #CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL').replace('\n', '')
    result_backend = os.environ.get('CELERY_RESULT_BACKEND').replace('\n', '')
    QUEUE_URL = os.environ.get('QUEUE_URL').replace('\n', '')
    CELERY_ACCESS_KEY = os.environ.get('CELERY_ACCESS_KEY').replace('\n', '')
    CELERY_SECRET_ACCESS_KEY = os.environ.get('CELERY_SECRET_ACCESS_KEY').replace('\n', '')

    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or '/Users/bj8th/Documents/GitHub/ProteomeScout-3/flask-proteomescout/proteomescout/app/upload'
   