"""
__init__ creates a Blueprint component for use in the views and error
files which makes it easier to make different URLs

    Returns:
        main is returned as the Blueprint Component
"""
from flask import Blueprint

# pylint: disable=invalid-name
main = Blueprint('main', __name__)

from . import views, errors
