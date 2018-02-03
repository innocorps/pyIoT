#!/usr/bin/env python3
"""Function that runs the entire backend app"""

# pylint: disable=invalid-name
import os
import sys
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
COV = None
if os.environ.get('FLASK_COVERAGE'):  # For checking test coverage
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

# These imports must be below the coverage start function, else
# the coverage misses parts of scripts
# pylint: disable=wrong-import-position
from app import create_app, db
from app.models import User, Machine

try:
    with open('/run/secrets/chamber_of_secrets') as secret_chamber:
        for line in secret_chamber:
            if 'FLASK_CONFIG' in line:
                # Take the VAL part of ARG=VAL, strip newlines
                FLASK_CONFIG = line.split("=")[1].rstrip()
    try:
        FLASK_CONFIG
    except NameError:
        print('CANNOT FIND FLASK_CONFIG IN CHAMBER')
        print('EXITING.')
        sys.exit(-1)
except OSError as e:
    print('CANNOT FIND CHAMBER')
    print(e)
    print('EXITING.')
    sys.exit(-1)
app = create_app(FLASK_CONFIG)
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    """
    Creates custom python shell

    Returns:
        dict, takes the data and formats into a dictionary and indexes by keys
    """
    return dict(app=app, db=db, User=User, Machine=Machine)


manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


# pylint: disable=redefined-outer-name
@manager.command
def test(coverage=False):
    """
    Run the unit tests

    Args:
        coverage=False: The default status of coverage, unless there's a flag.
    """
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        os.environ['FLASK_COVERAGE'] = '1'  # default
        os.execvp(sys.executable, [sys.executable] + sys.argv)
        print('Could not find FLASK_COVERAGE in env variables, using default.')
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:  # Tests the coverage of the unit tests
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version: file://%s/index.html' % covdir)
        COV.erase()


if __name__ == '__main__':
    manager.run()
