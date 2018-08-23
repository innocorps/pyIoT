"""Init file for backend App"""

# pylint: disable=invalid-name
import sys
import logging
import redis
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_bootstrap import WebCDN
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_caching import Cache
from flask_mail import Mail
from config import config, Config
from celery import Celery
from .watchdog import Watchdog
from werkzeug.contrib.fixers import ProxyFix

bootstrap = Bootstrap()
db = SQLAlchemy()
mail = Mail()
cache = Cache(config={
    'CACHE_TYPE': 'redis',
    'CACHE_KEY_PREFIX': 'fcache',
    'CACHE_REDIS_HOST': 'redis',
    'CACHE_REDIS_PORT': '6379',
    'CACHE_REDIS_URL': 'redis://redis:6379'})

celery = Celery(__name__, broker=Config.CELERY_BROKER_URL)

login_manager = LoginManager()
login_manager.session_protection = 'basic'
login_manager.login_view = 'auth.login'

logger = logging.getLogger('backend INFO Logger')
logger.setLevel(logging.INFO)
info_file_handler = RotatingFileHandler(
    filename='info_log.log',
    maxBytes=30 * 1024 * 1024,
    backupCount=7)
info_file_handler.setLevel(logging.INFO)
info_formatter = logging.Formatter('%(asctime)s - %(name)s - '
                                   '%(levelname)s - %(message)s '
                                   '[in %(pathname)s: line %(lineno)d]')
info_file_handler.setFormatter(info_formatter)
logger.addHandler(info_file_handler)

watchdog = Watchdog(timeout=10, cache=cache)

def create_app(config_name):
    """
    Creates an instance of the Backend App

    Args:
        config_name: is the configuration for the type of Backend the
        user wants to run

    Returns:
        Backend, which starts up the app
    """
    app = Flask(__name__)
    # WARNING It is a security issue to use this middleware in a non-proxy
    # setup that enforces using https as it will blindly trust the incoming
    # headers which could be forged by a malicious client. See also the
    # following: http://flask.pocoo.org/docs/1.0/deploying/wsgi-standalone/
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.config.from_object(config[config_name])
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    config[config_name].init_app(app)

    login_manager.init_app(app)
    bootstrap.init_app(app)
    app.extensions['bootstrap']['cdns']['jquery'] = WebCDN(
        '//ajax.googleapis.com/ajax/libs/jquery/3.2.1/'
    )

    mail.init_app(app)
    db.init_app(app)
    cache.init_app(app)
    celery.conf.update(app.config)

    # Clear cache at startup, Redis defaults to clear the whole DB if that
    # happens. NOTE: I am doing this to create a consistent startup
    # state, however, any replicas if they spun back up would clear the
    # cache after initializing, so we may want to do this elsewhere.
    with app.app_context():
        try:
            cache.clear()
        except redis.ConnectionError as e:
            print(e)
            sys.exit(-1)

    # Backend Warning/Error Logger
    if not app.config['TESTING']:
        error_file_handler = RotatingFileHandler(
            filename=app.config['ERROR_LOGGING_LOCATION'],
            maxBytes=app.config['ERROR_LOGGING_MAX_BYTES'],
            backupCount=['ERROR_LOGGING_BACKUP_COUNT'])
        formatter = logging.Formatter(app.config['LOGGING_FORMAT'])
        error_file_handler.setFormatter(formatter)
        app.logger.setLevel(app.config['ERROR_LOGGING_LEVEL'])
        app.logger.addHandler(error_file_handler)


    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .api_0_1 import api_0_1 as api_0_1_blueprint
    app.register_blueprint(api_0_1_blueprint, url_prefix='/api/v0.1')

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    return app
