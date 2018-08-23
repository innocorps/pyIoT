#!/usr/bin/env python3
"""
Set up a flask app for context to run a background Celery worker.
See also: https://blog.miguelgrinberg.com/post/celery-and-the-flask-application-factory-pattern
"""
import sys
from app import celery, create_app

try:
    with open('/run/secrets/chamber_of_secrets') as secret_chamber:
        for line in secret_chamber:
            if 'FLASK_CONFIG' in line:
                FLASK_CONFIG = line.split("=")[1].rstrip()
    try:
        FLASK_CONFIG
    except NameError:
        print("CANNOT FIND FLASK_CONFIG IN CHAMBER WHILE SETTING UP CELERY.")
        print("EXITING")
        sys.exit(-1)
except OSError as e:
    print("CANNOT FIND CHAMBER WHILE SETTING UP CELERY.")
    print(e)
    print("EXITING.")
    sys.exit(-1)
app = create_app(FLASK_CONFIG)
app.app_context().push()
