"""Handles authentication information for API calls"""
from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth
from . import api_0_1
from .errors import unauthorized, forbidden
from ..models import User, AnonymousUser

# pylint: disable=invalid-name
auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(email_or_token, password):
    """
    Verifies for password or token

    Args:
        email_or_token: used to verify the identity of the user
        password: tthe user's password

    Returns:
        user.verify_password, which returns the verified user's password
    """
    if email_or_token == '':
        g.current_user = AnonymousUser()
        return True
    if password == '':
        g.current_user = User.verify_auth_token(email_or_token)
        g.token_used = True
        return g.current_user is not None
    user = User.query.filter_by(email=email_or_token).first()
    if not user:
        return False
    g.current_user = user
    g.token_used = False
    return user.verify_password(password)


@auth.error_handler
def auth_error():
    """
    Checks token and password, throws error if the token or password fail

    Returns:
        unauthorized, which diplays the message 'Invalid credentials'
    """
    return unauthorized('Invalid credentials')


@api_0_1.before_request
@auth.login_required
def before_request():
    """
    Checks that the API user is signed in before any requests are made

    Returns:
        forbidden, which displays the message 'Not signed in'
    """
    if g.current_user.is_anonymous:
        return forbidden('Not signed in')

    if not g.current_user.confirmed:
        return forbidden('Unconfirmed account')


@api_0_1.route('/token')
def get_token():
    """
    Generates a token, based on the username and password.

    Returns:
        unauthorized, which displays the message 'Invalid credentials'
        jsonify, turns the token into a JSON

    .. :quickref: Token; Get authentication token

    **Example request**:

    Shell command:

    .. sourcecode:: shell

        curl --user <username>:<password> -X GET http://localhost/api/v0.1/token

    Command response:

    .. sourcecode:: http

        GET /api/v0.1/token HTTP/1.1
        Host: 127.0.0.1:5000
        Authorization: Basic <b64 encoded username:password>

    **Example response**:

    .. sourcecode:: http

        HTTP/1.0 200 OK
        Content-Type: application/json

        {
            "expiration": 3600,
            "token":"asdfj34j34i5h38ewi34j0983uerij23ih03-i203riho"
            }

    :reqheader Authorization: use cURL tag with <usrnme>:<psswrd>, or <token>:
    :resheader Content-Type: application/json
    :statuscode 200: Successfully retrieved token
    :statuscode 401: Invalid credentials

    """
    if g.current_user.is_anonymous or g.token_used:
        return unauthorized('Invalid credentials')
    return jsonify({'token': g.current_user.generate_auth_token(
        expiration=3600), 'expiration': 3600})
