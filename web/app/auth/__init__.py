"""
    __init__ creates a Blueprint component for use
    in the views file which makes it easier to make different URLs

    Returns:
        auth is returned as the Blueprint Component
"""
from flask import Blueprint

# pylint: disable=invalid-name
auth = Blueprint('auth', __name__)

from . import views
