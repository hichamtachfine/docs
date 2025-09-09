import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'supersecretkey'
    SQLALCHEMY_DATABASE_URI = 'postgresql://flaskuser:zabi@localhost/flaskportal'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
