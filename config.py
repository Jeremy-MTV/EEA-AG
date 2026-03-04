import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'eea_ag_v3.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail Config (For future use)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Other Config
    BACKUP_DIR = os.path.join(basedir, 'backups')
    NAS_BACKUP_PATH_MEMBERS = os.environ.get('NAS_BACKUP_PATH_MEMBERS')
    NAS_BACKUP_PATH_AG = os.environ.get('NAS_BACKUP_PATH_AG')
    GSHEET_URL_MEMBERS = os.environ.get('GSHEET_URL_MEMBERS')
    GSHEET_URL_AG = os.environ.get('GSHEET_URL_AG')
