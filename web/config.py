"""CONFIG file for web"""

# pylint: disable=too-few-public-methods
import os
import sys
import logging
import json
from datetime import timedelta as td
from celery.task.control import rate_limit
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    """
    Sets Config defaults

    Attributes:
        SECRET_KEY: Gets the secret key for Config.
        TRAP_BAD_REQUEST_ERRORS: Establishes that
        bad request errors will be trapped, i.e. TRUE.
        SQLALCHEMY_COMMIT_ON_TEARDOWN: Establishes that
        upon teardown SQLAlchemy will commit.
        POSTS_PER_PAGE: Maximum posts per page.
        REDIS_CACHE_TIMEOUT: Time limit for the Redis cache.
        LOGGING_FORMAT: Establishes logging format.
        ERROR_LOGGING_LOCATION: Establishes where the errors are logged.
        ERROR_LOGGING_LEVEL: Establishes the error level as WARNING.
        ERROR_LOGGING_MAX_BYTES: Maximum amount of bytes for error logging.
        ERROR_LOGGING_BACKUP_COUNT: Number of error log backups.
        OAUTH_CREDENTIALS: Credentials for using Google OAuth
        MAIL_SERVER: Google server for sending emails
        MAIL_PORT: Port that emails are sent over
        MAIL_USE_TLS: Adds email encryption
        MAIL_USERNAME: Gmail username (email)
        MAIL_PASSWORD: Gmail password
        BACKEND_MAIL_SUBJECT_PREFIX: Email subject prefix
        BACKEND_MAIL_SENDER: Email sender shown in email
    """
    try:
        with open('/run/secrets/chamber_of_secrets') as secret_chamber:
            for line in secret_chamber:
                if 'FLASK_SECRET_KEY' in line:
                    # Take the VAL part of ARG=VAL, strip newlines
                    SECRET_KEY = line.split("=")[1].rstrip()
        try:
            SECRET_KEY
        except NameError:
            print('CANNOT FIND FLASK_SECRET_KEY IN CHAMBER')
            print('EXITING.')
            sys.exit(-1)
    except OSError as e:
        print('CANNOT FIND CHAMBER')
        print(e)
        print('EXITING.')
        sys.exit(-1)

    PREFERRED_URL_SCHEME = 'https'
    SESSION_COOKIE_SECURE = True

    CELERY_RESULT_BACKEND = 'redis://redis:6379'
    CELERY_TASK_RESULT_EXPIRES = td(seconds=1800)
    CELERY_BROKER_URL = 'redis://redis:6379'
    CELERY_ACKS_LATE = True
    CELERYD_PREFETCH_MULTIPLIER = 1
    rate_limit = '4/m'

    TRAP_BAD_REQUEST_ERRORS = True
    SQLALCHEMY_COMMIT_ON_TEARDOWN = False

    # Log database requests that take a long time
    SQLALCHEMY_RECORD_QUERIES = True
    # Database query timeout in seconds
    SQLALCHEMY_DATABASE_QUERY_TIMEOUT = 0.05

    POSTS_PER_PAGE = 20
    MAX_API_DATA_PER_REQUEST = 1800  # cannot pull more than an hour for API
    REDIS_CACHE_TIMEOUT = 3600 * 24 * 3
    LOGGING_FORMAT = ('%(asctime)s - %(name)s - %(levelname)s - %(message)s '
                      '[in %(pathname)s: line %(lineno)d]')
    ERROR_LOGGING_LOCATION = 'error_log.log'
    ERROR_LOGGING_LEVEL = logging.WARNING
    ERROR_LOGGING_MAX_BYTES = 25 * 1024 * 1024
    ERROR_LOGGING_BACKUP_COUNT = 7

    try:
        with open('/run/secrets/chamber_of_secrets') as secret_chamber:
            for line in secret_chamber:
                if 'FLASK_OAUTH_CREDENTIALS' in line:
                    # Take the VAL part of ARG=VAL, strip newlines
                    OAUTH_CREDENTIALS = json.loads(line.split("=")[1].rstrip())
        try:
            OAUTH_CREDENTIALS
        except NameError:
            print('CANNOT FIND FLASK_OAUTH_CREDENTIALS IN CHAMBER')
            print('EXITING.')
            sys.exit(-1)
    except OSError as e:
        print('CANNOT FIND CHAMBER')
        print(e)
        print('EXITING.')
        sys.exit(-1)

    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True

    try:
        with open('/run/secrets/chamber_of_secrets') as secret_chamber:
            for line in secret_chamber:
                if 'FLASK_MAIL_USERNAME' in line:
                    # Take the VAL part of ARG=VAL, strip newlines
                    MAIL_USERNAME = line.split("=")[1].rstrip()
        try:
            MAIL_USERNAME
        except NameError:
            print('CANNOT FIND FLASK_MAIL_USERNAME IN CHAMBER')
            print('EXITING.')
            sys.exit(-1)
    except OSError as e:
        print('CANNOT FIND CHAMBER')
        print(e)
        print('EXITING.')
        sys.exit(-1)

    try:
        with open('/run/secrets/chamber_of_secrets') as secret_chamber:
            for line in secret_chamber:
                if 'FLASK_MAIL_DOMAIN' in line:
                    # Take the VAL part of ARG=VAL, strip newlines
                    MAIL_DOMAIN = line.split("=")[1].rstrip()
        try:
            MAIL_DOMAIN
        except NameError:
            print('CANNOT FIND FLASK_MAIL_DOMAIN IN CHAMBER')
            print('EXITING.')
            sys.exit(-1)
    except OSError as e:
        print('CANNOT FIND CHAMBER')
        print(e)
        print('EXITING.')
        sys.exit(-1)

    try:
        with open('/run/secrets/chamber_of_secrets') as secret_chamber:
            for line in secret_chamber:
                if 'FLASK_MAIL_PASSWORD' in line:
                    # Take the VAL part of ARG=VAL, strip newlines
                    MAIL_PASSWORD = line.split("=")[1].rstrip()
        try:
            MAIL_PASSWORD
        except NameError:
            print('CANNOT FIND FLASK_MAIL_PASSWORD IN CHAMBER')
            print('EXITING.')
            sys.exit(-1)
    except OSError as e:
        print('CANNOT FIND CHAMBER')
        print(e)
        print('EXITING.')
        sys.exit(-1)

    BACKEND_MAIL_SUBJECT_PREFIX = '[Backend]'
    BACKEND_MAIL_SENDER = 'Backend Admin'

    @staticmethod
    def init_app(app):
        """
        For configuration specific initialization of the app.

        Args:
            app: The application.
        """
        pass


class LocalConfig(Config):
    """
    Local defaults

    Attributes:
        DEBUG: Sets  DEBUG status for error log while in local (True or False).
        SQLALCHEMY_DATABASE_URI: Sets the path to the databse.
    """
    DEBUG = True
    try:
        with open('/run/secrets/chamber_of_secrets') as secret_chamber:
            for line in secret_chamber:
                if 'FLASK_LOCAL_DATABASE' in line:
                    # Take the VAL part of ARG=VAL, strip newlines
                    SQLALCHEMY_DATABASE_URI = line.split("=")[1].rstrip()
        try:
            SQLALCHEMY_DATABASE_URI
        except NameError:
            print('CANNOT FIND FLASK_LOCAL_DATABASE IN CHAMBER')
            print('EXITING.')
            sys.exit(-1)
    except OSError as e:
        print('CANNOT FIND CHAMBER')
        print(e)
        print('EXITING.')
        sys.exit(-1)


class DevelopmentConfig(Config):
    """
    Dev defaults

    Attributes:
        DEBUG: Sets  DEBUG status for error log while in Dev (True or False).
        SQLALCHEMY_DATABASE_URI: Sets the path to the databse.
    """
    DEBUG = True
    try:
        with open('/run/secrets/chamber_of_secrets') as secret_chamber:
            for line in secret_chamber:
                if 'FLASK_DEV_DATABASE' in line:
                    # Take the VAL part of ARG=VAL, strip newlines
                    SQLALCHEMY_DATABASE_URI = line.split("=")[1].rstrip()
        try:
            SQLALCHEMY_DATABASE_URI
        except NameError:
            print('CANNOT FIND FLASK_DEV_DATABASE IN CHAMBER')
            print('EXITING.')
            sys.exit(-1)
    except OSError as e:
        print('CANNOT FIND CHAMBER')
        print(e)
        print('EXITING.')
        sys.exit(-1)


class TestingConfig(Config):
    """
    Test defaults

    Attributes:
        TESTING: Sets TESTING status for error log while Testing (True/False).
        WTF_CSRF_ENABLED: Sets status for CSRF during testing (True or False).
        SQLALCHEMY_DATABASE_URI: Sets the path to the database.
    """
    TESTING = True
    WTF_CSRF_ENABLED = False
    CELERY_ALWAYS_EAGER = True
    try:
        with open('/run/secrets/chamber_of_secrets') as secret_chamber:
            for line in secret_chamber:
                if 'FLASK_TEST_DATABASE' in line:
                    # Take the VAL part of ARG=VAL, strip newlines
                    SQLALCHEMY_DATABASE_URI = line.split("=")[1].rstrip()
        try:
            SQLALCHEMY_DATABASE_URI
        except NameError:
            print('CANNOT FIND FLASK_TEST_DATABASE IN CHAMBER')
            print('EXITING.')
            sys.exit(-1)
    except OSError as e:
        print('CANNOT FIND CHAMBER')
        print(e)
        print('EXITING.')
        sys.exit(-1)


class ProductionConfig(Config):
    """
    Production defaults

    Attributes:
        SQLALCHEMY_DATABASE_URI: Sets the path to the database.
    """
    try:
        with open('/run/secrets/chamber_of_secrets') as secret_chamber:
            for line in secret_chamber:
                if 'FLASK_PRODUCTION_DATABASE' in line:
                    # Take the VAL part of ARG=VAL, strip newlines
                    SQLALCHEMY_DATABASE_URI = line.split("=")[1].rstrip()
        try:
            SQLALCHEMY_DATABASE_URI
        except NameError:
            print('CANNOT FIND FLASK_PRODUCTION_DATABASE IN CHAMBER')
            print('EXITING.')
            sys.exit(-1)
    except OSError as e:
        print('CANNOT FIND CHAMBER')
        print(e)
        print('EXITING.')
        sys.exit(-1)


# pylint: disable=invalid-name
config = {
    'local': LocalConfig,
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}
