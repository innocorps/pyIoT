"""
    __init__ creates a Blueprint component for use in the machine_posts,
    errors, and authentification files which makes it easier to make different
    URLs

    Returns:
        api is returned as the Blueprint Component
"""
from flask import Blueprint

# pylint: disable=invalid-name
api_0_1 = Blueprint('api_0_1', __name__)

from . import machine_posts, errors, authentication
