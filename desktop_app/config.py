import os

basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    SCHEMA = "http://"
    HOST = "172.16.2.38"
    PORT = 4444

    SECRET_KEY = "123456790"

    DATABASE_FILE = "gsm.db"
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, DATABASE_FILE)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
