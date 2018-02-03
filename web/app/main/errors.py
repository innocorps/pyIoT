"""Calls webpage error templates, checks if JSON is needed first"""
from flask import render_template, request, jsonify, current_app
from . import main
from .. import logger
# pylint: disable=invalid-name


@main.app_errorhandler(404)
def page_not_found(e):
    """
    Creates 404 Page not found error for an error, e, that classifies as such.

    Args:
        e: This is the imported error that the program sends to this file.

    Returns:
        response of error not found
        render_template('404.html')
    """
    current_app.logger.warning(e)
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'not found'})
        response.status_code = 404
        return response
    return render_template('404.html'), 404


@main.app_errorhandler(500)
def internal_server_error(e):
    """
    Creates 500 Server error for an error, e, that classifies as such.

    Args:
        e: This is the imported error that the program sends to this file.

    Returns:
        render_template('500.html')
    """
    current_app.logger.error(e)  # pragma: no cover
    return render_template('500.html'), 500  # pragma: no cover


@main.app_errorhandler(405)
def method_not_allowed_error(e):
    """
    Creates 405 Method not allowed error for an error, e,
    that classifies as such

    Args:
        e: This is the imported error that the program sends to this file

    Returns:
        render_template('405.html')
    """
    current_app.logger.warning(e)
    return render_template('405.html'), 405


@main.after_request
def after_request(response):
    """
    Responds to the user, checking through the errors built into the program

    Args:
        response: This is an object used to address errors in the program

    Returns:
        response
    """
    if (not current_app.config['TESTING'] and not
            current_app.config['DEBUG']):  # pragma: no cover
        logger.info('%s %s %s %s %s',
                    request.remote_addr,
                    request.method,
                    request.scheme,
                    request.full_path,
                    response.status)
    return response
