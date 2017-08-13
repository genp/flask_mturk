import os
basedir = os.path.abspath(os.path.dirname(__file__))


###
# App Properties
###

WTF_CSRF_ENABLED = True
SECRET_KEY = ''
SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://postgres:...'
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = True
log_file = os.path.join(basedir, 'log/server.log')
