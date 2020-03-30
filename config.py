from os import environ


class DevelopConfig:
    """Set Flask configuration vars from .env file."""

    # General
    TESTING = environ.get('TESTING', False)
    FLASK_DEBUG = environ.get('FLASK_DEBUG', True)
    SECRET_KEY = environ.get('SECRET_KEY', '123456')

    # Database
    SQLALCHEMY_DATABASE_URI = environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:////tmp/test.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = environ.get('SQLALCHEMY_TRACK_MODIFICATIONS', False)


class TestConfig:
    # General
    TESTING = True
    FLASK_DEBUG = True
    SECRET_KEY = 'test'

    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/test.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False