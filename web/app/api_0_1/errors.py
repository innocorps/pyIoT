"""Error messages, in JSON for API"""
import json
from flask import jsonify, current_app, request
from . import api_0_1
from .. import logger


@api_0_1.errorhandler(400)
# pylint: disable=unused-argument
def bad_request(message):
    """
    Creates 400 Bad Request error response

    Args:
        message: this is the imported error that the program sends to this file

    Returns:
        response of '400 bad request' with message 'Malformed JSON String'
    """
    response = jsonify(
        {'error': '400 bad request',
         'message': 'Malformed JSON String.'})
    response.status_code = 400
    message = (str(message) + ' . IP Address of '
               'sender: ' + str(request.remote_addr))
    current_app.logger.error(message)
    return response


@api_0_1.errorhandler(500)
def server_error(message):  # pragma: no cover
    """
    Creates 500: Internal Server Error response

    Args:
        message: this is the imported error that the program sends to this file

    Returns:
        response of '500 Internal Server Error'
        with message 'There was an error in the server code'
    """
    response = jsonify(
        {'error': '500 Internal Server Error',
         'message': 'There was an error in the server code:'+message})
    response.status_code = 500
    current_app.logger.error(message)
    return response


def not_acceptable(message):
    """
    Creates 406: JSON does not match with hard coded JSON error

    Args:
        message: this is the imported error that the program sends to this file

    Returns:
        '406 error' response with message 'JSON does not match correct format'
    """
    response = jsonify({'406 error': 'JSON does not match correct format',
                        'message': message})
    response.status_code = 406
    json_data = json.loads(request.data.decode("utf-8"))
    try:
        if json_data is None:
            current_app.logger.warning(str(response.data) + '. JSON Message '
                                       'Time and Date: ' +
                                       "None" +
                                       '. IP Address of '
                                       'sender: ' + str(request.remote_addr))
        else:
            current_app.logger.warning(str(response.data) + '. JSON Message '
                                       'Time and Date: ' +
                                       json_data['datetime'] +
                                       '. IP Address of '
                                       'sender: ' + str(request.remote_addr))
    except KeyError:
        current_app.logger.warning(str(response.data) + '. IP Address of '
                                   'sender: ' + str(request.remote_addr))

    return response


def unauthorized(message):
    """
    Creates 401: Unauhtorized Request response

    Args:
        message: this is the imported error that the program sends to this file

    Returns:
        response of '401 error' with message 'unauthorized'
    """
    response = jsonify({'401 error': 'unauthorized', 'message': message})
    response.status_code = 401
    current_app.logger.warning(str(response.data) + '. The IP trying to '
                               'access data: ' +
                               str(request.remote_addr))
    return response


def too_many_requests(message):
    """
    Creates 429: Too Many Requests response

    Args:
        message: this is the imported error that the program sends to this file

    Returns:
        response of '429 error' with message 'too many requests'
    """
    response = jsonify({'429 error': 'too many requests', 'message': message})
    response.status_code = 429
    current_app.logger.warning(str(response.data) + '. The IP trying '
                               'to access data: ' +
                               str(request.remote_addr))
    return response


def forbidden(message):
    """
    Creates 403: Forbidden Request response

    Args:
        message: this is the imported error that the program sends to this file

    Returns:
        response of '403 error' with message 'forbidden'
    """
    # current_app.logger.error(message)
    response = jsonify({'403 error': 'forbidden', 'message': message})
    response.status_code = 403
    current_app.logger.warning(str(response.data) + '. The IP trying '
                               'to access data: ' +
                               str(request.remote_addr))
    return response


@api_0_1.after_request
def after_request(response):
    """
    Logs the requests

    Args:
        response: Imported error is sent to the errors log file

    Returns:
        response and logs it
    """
    if not current_app.config['TESTING'] \
            and not current_app.config['DEBUG']:  # pragma: no cover
        logger.info('%s %s %s %s %s',
                    request.remote_addr,
                    request.method,
                    request.scheme,
                    request.full_path,
                    response.status)
    return response
