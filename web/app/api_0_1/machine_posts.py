"""api endpoints"""
import cProfile
import pstats
import io
import sqlalchemy
import json
from sqlalchemy import desc
from datetime import datetime, timedelta
from flask import jsonify, request, url_for, current_app
from flask_sqlalchemy import get_debug_queries
from redis import RedisError
from .. import db, cache, watchdog, celery
from . import api_0_1
from .errors import not_acceptable, bad_request, too_many_requests, server_error
from ..accepted_json_message import ACCEPTED_JSON
from ..models import Machine
import strict_rfc3339

@api_0_1.after_request
def after_request(response):
    """
    Logs queries that took a long time
    https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xvi-debugging-testing-and-profiling
    """
    for query in get_debug_queries():
        if query.duration >= current_app.config['SQLALCHEMY_DATABASE_QUERY_TIMEOUT']:
            current_app.logger.warning(
                f"SLOW SQL QUERY: {query.statement} PARAMETERS: {query.parameters} DURATION: {query.duration}s CONTEXT: {query.context}")
    return response


@api_0_1.route('/posts/')
def get_posts():
    """
    Get all posts in the database. The result will be paginated if there
    are many results.

    Returns:
        jsonify, whose data has now been paginated

    .. :quickref: All Data; Get all data

    **Example request**:

    Shell command:

    *with email/password:*

    .. sourcecode:: shell

        curl --user <email>:<password> -X GET https://localhost/api/v0.1/posts/

    *with token:*

    .. sourcecode:: shell

        curl --user <token>: -X GET https://localhost/api/v0.1/posts/

    Command response:

    .. sourcecode:: http

        GET /api/v0.1/posts/ HTTP/1.1
        Host: localhost
        Authorization: Basic <b64 encoded email:password or token:>

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "count": 127,
            "next": "http://localhost/api/v0.1/posts/?page=2",
            "prev": null,
            "data": [
                {
                "datetime": "2017-08-17T21:27:34Z",
                "sensor_1": "10.0"
                }
                ]
            }

    *(JSON cut for length)*

   :reqheader Authorization: use cURL tag with <email>:<psswrd>, or <token>:
   :resheader Content-Type: application/json
   :statuscode 200: Successfully retrieved data
   :statuscode 401: Invalid credentials
   :statuscode 403: Not signed in

    """
    page = request.args.get('page', 1, type=int)
    # paginate response
    pagination = db.session.query(Machine).order_by(desc(Machine.datetime)).paginate(
        page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    page_items = pagination.items
    prev_pg = None
    if pagination.has_prev:  # shows link to previous page
        prev_pg = url_for('api_0_1.get_posts', page=page - 1, _external=True)
    next_pg = None
    if pagination.has_next:  # shows linke to next page
        next_pg = url_for('api_0_1.get_posts', page=page + 1, _external=True)
    return jsonify({
        'data': [item.to_json() for item in page_items],
        'prev': prev_pg,
        'next': next_pg,
        'count': pagination.total
    })


@api_0_1.route('/posts/<start_time>/<end_time>')
def get_post(start_time, end_time):
    """
    Get a single post and convert to json.

    Args:
        start_time: Beginning time of window of data being queried
        end_time: End time of window of data being queried

    Returns:
        Data for a specific period of time. It will output a list of jsons,
        outputting the data if found and outputting 'data not found' if
        that time was not found in database.


    .. :quickref: Data Window; Get window of data

    **Example request**:

    Shell command:

    *with email/password:*

    .. sourcecode:: shell

        curl --user <email>:<password> -X GET https://localhost/api/v0.1/posts/2017-09-13T13:01:57Z/2017-09-13T13:01:59Z

    *or with token:*

    .. sourcecode:: shell

        curl --user <token>: -X GET https://localhost/api/v0.1/posts/2017-09-13T13:01:57Z/2017-09-13T13:01:59Z

    Command response:

    .. sourcecode:: http

        GET /api/v0.1/posts/2017-09-13T13:01:57Z/2017-09-13T13:01:59Z HTTP/1.1
        localhost
        Authorization: Basic <b64 encoded email:password or token:>

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        [
            {
                "JSON_message":"goes_here"
                },
            {
                "next_JSON_message":"goes_here"
                }
        ]

    *(JSON cut for length)*

   :query start_time: Beginning time of window of data being queried
   :query end_time: End time of window of data being queried
   :reqheader Authorization: use cURL tag with <email>:<psswrd>, or <token>:
   :resheader Content-Type: application/json
   :statuscode 200: Successfully retrieved data
   :statuscode 401: Invalid credentials
   :statuscode 403: Not signed in

    """
    time_format = '%Y-%m-%dT%H:%M:%SZ'
    start_time_stripped = datetime.strptime(start_time, time_format)
    end = datetime.strptime(end_time, time_format)
    time_delta = datetime.strptime(end_time, time_format) \
        - datetime.strptime(start_time, time_format)

    if not (strict_rfc3339.validate_rfc3339(start_time) and
            strict_rfc3339.validate_rfc3339(end_time)):
        print("Error: datetimes are not RFC 3339")
        return bad_request('Error: Datetimes are not RFC 3339')

    start_time_epoch = strict_rfc3339.rfc3339_to_timestamp(start_time)
    end_time_epoch = strict_rfc3339.rfc3339_to_timestamp(end_time)
    # print("start_time_epoch: {} end_time_epoch: {}".format(start_time_epoch,
    # end_time_epoch))
    if (end_time_epoch < start_time_epoch):
        print("Error: end time is before start time")
        return bad_request('Error: End time is before start time')

    MAX_API_DATA_S = current_app.config['MAX_API_DATA_PER_REQUEST']

    if time_delta > timedelta(seconds=MAX_API_DATA_S):
        return too_many_requests(
            'Request is above {} seconds of data.'.format(MAX_API_DATA_S))

    end = start_time_stripped + time_delta
    data = []
    while start_time_stripped <= end:
        # Until we change to 24hr time
        strtime = start_time_stripped.strftime(time_format)
        try:
            cache.get(strtime)
            no_redis_connection = False
        except RedisError:
            no_redis_connection = True

        if not no_redis_connection:
            if cache.get(strtime) is None:
                data_query = Machine.query.filter_by(
                    datetime=strtime).first()
                if data_query is not None:
                    try:
                        raw_data = data_query.to_json()
                        data.append(raw_data)
                        cache.set(strtime, raw_data, timeout=0)
                    except BaseException:
                        data.append({"Error": "Could not find data."})
            else:
                data.append(cache.get(strtime))
        else:
            data_query = Machine.query.filter_by(datetime=strtime).first()
            if data_query is not None:
                try:
                    raw_data = data_query.to_json()
                    data.append(raw_data)
                except BaseException:
                    data.append({"Error": "Could not find data."})
        start_time_stripped += timedelta(seconds=1)

    return jsonify(data)

@api_0_1.route('/posts/', methods=['POST'])
def new_post():
    """
    Deflates json and creates a new post.

    Returns:
        bad_request if the response data is not json found or empty

        bad_request if no JSON is found with message
        'There was no JSON found in the request.
        Likely the application/json'\'header was missing.'

        not_acceptable if data is missing with message
        'JSON has sensor data missing. '\ 'Sensor(s) may have been removed from network. ' and displays missing data

        not_acceptable if extra sensor data is found with message
        'JSON has extra sensor data, '\'sensor(s) may have been added to the network. '\
        'Sensor(s) not found in the database: ' and displays new sensors

        jsonify, which commits and caches the sensor data

    .. :quickref: New Data; Post new JSON message

    **Example request**:

    Shell command:

    *with email/password:*

    .. sourcecode:: shell

        curl --user <email>:<password> -X POST https://localhost/api/v0.1/posts/ -H 'Content-Type: application/json' -d 'JSON DATA GOES HERE'

    *or with token:*

    .. sourcecode:: shell

        curl --user <token>: -X POST https://localhost/api/v0.1/posts/ -H 'Content-Type: application/json' -d 'JSON DATA GOES HERE'

    Command line output of cUrl:

    .. sourcecode:: http

        POST /api/v0.1/posts/ HTTP/1.1
        Host: localhost
        Authorization: Basic <b64 encoded email:password or token:>
        Content-Type: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 201 CREATED
        Content-Type: application/json

        {
            "response": "201 data created",
            "message": "Data was successfully posted!"
        }

   :reqheader Authorization: use cURL tag with <email>:<psswrd>, or <token>:
   :reqheader Content-Type: application/json
   :resheader Content-Type: application/json
   :statuscode 200: Successfully retrieved data
   :statuscode 401: Invalid credentials
   :statuscode 403: Not signed in
   :statuscode 400: Malformed JSON
   :statuscode 406: Data does not match correct format (sensor deleted/added)

    """
    watchdog.pet()
    try:
        if request.headers['Content-Type'] != 'application/json':
            print('Content-Type: application/json not found.')
            current_app.logger.error(
                'Content-Type: application/json not found.')
            return bad_request('Content-Type: application/json not found.')
    except KeyError as e:
        print(e)
        current_app.logger.error(
            'Missing Content-Type: application/json header')
        return bad_request('Missing Content-Type: application/json header')
    try:
        json_data = json.loads(request.data.decode("utf-8"))
        if isinstance(json_data, str):
            print("JSON message is improperly formatted.")
            json_data = None
    except (json.decoder.JSONDecodeError) as e:
        print(e)
        json_data = None

    if json_data is None:
        print('There was no JSON found in the request. '
              'Likely the application/json is missing.')
        current_app.logger.error('JSON Error: '
                                 'There was no JSON decoded and found.')
        return bad_request('There was no JSON found in the request. '
                           'Likely the application/json '
                           'header was missing.')

    if 'heartbeat' in json_data:
        return jsonify(
            {'response': '200 OK', 'message': 'Heartbeat received.'}), 200

    json_post = Machine.flatten(json_data)
    flattened_accepted_json = Machine.flatten(ACCEPTED_JSON)
    data = Machine.from_json(json_post)
    to_json_data = data.to_json()

    if not Machine.is_valid_datetime(json_post):
        return not_acceptable('Datetime is not in the correct format.'
                              ' It could be missing orneeds to be in the '
                              'form \'YYYY-MM-DD\'T\'HH:MM:SS\'Z '
                              '(eg. 2017-09-13T13:01:57Z)')

    missing_data, invalid_sensors = Machine.invalid_data(
        json_post, flattened_accepted_json)
    if len(missing_data) > 0:
        return not_acceptable('JSON has sensor data missing. '
                              'Sensor(s) may have been removed from network. '
                              'Sensor(s) with missing '
                              'data: ' + str(missing_data))

    if len(invalid_sensors) > 0:
        return not_acceptable('JSON has extra sensor data, '
                              'sensor(s) may have been added to network. '
                              'Sensor(s) not found in the '
                              'database: ' + str(invalid_sensors))

    """
    Set datetime key in cache if it doesn't already exist.
    Try to commit it to the database if it wasn't in cache already.
    """
    try:
        if cache.get(json_post['datetime']) is None:
            cache.set(json_post['datetime'], to_json_data,
                      timeout=0)
            try:
                db.session.add(data)
                db.session.commit()
            except sqlalchemy.exc.IntegrityError:
                return not_acceptable(
                    'A unique id error was returned. '
                    'This datetime is already in the database.')
        else:
            return not_acceptable('This datetime is already in cache.')
    except RedisError as e:
        print(e)
        print('Redis port may be closed, the redis server does '
              'not appear to be running.')

    return jsonify(
        {'response': '201 data created',
         'message': 'Data was successfully posted!'}), 201


@api_0_1.route('/statistics/<start_time>/<end_time>', methods=['GET'])
def statistics_of_data(start_time, end_time):
    """
    API Endpoint to run statistical analysis, which calls the async
    background function.
    Args:
        start_time: Beginning time of window of data being queried
        end_time: End time of window of data being queried
    """
    task = async_statistics.delay(start_time, end_time)
    return jsonify({}), 202, {'Location': url_for('api_0_1.statistics_status',
                                                  task_id=task.id)}


@api_0_1.route('/statistics/status/<task_id>')
def statistics_status(task_id):
    """
    Return status or result of statistical analysis being done in the background
    https://blog.miguelgrinberg.com/post/using-celery-with-flask
    """
    try:
        task = async_statistics.AsyncResult(task_id)
        if task.result is None: # Task has not been handed off to a process yet
            # TODO: Better way of checking this? Checking status of a task that
            # is non-existent or invalid will still technically behave the same
            result = 'Task is pending, possibly waiting for other tasks to finish'
            response = jsonify({'result': result})
            response.status_code = 202
            return response
        result = task.result['result']
        status = task.result['status']
        if (task.state in ('PENDING', 'STARTED', 'PROGRESS', 'SUCCESS')) and (status in (200, 202, 204)):
            # task was created, in various stages of completion
            response = jsonify(result)
            response.status_code = status
        # check known error cases (state would technically be successful)
        elif status == 400:
            # Task returned Bad Request Error
            return bad_request(result)
        elif status == 500:
            # Task returned Sever Error
            return server_error(result)
        elif task.state == 'FAILURE':
            # Task failed, unknown reason
            response = jsonify({
                'state': task.state,
                'status': task.info.get('status', '')
            })
            # response.status_code = 500
        else:
            # something went wrong in the background job, unknown result
            response = jsonify({
                'state': task.state,
                'status': str(task.info),  # this is the exception raised
            })
            # response.status_code = 500

    except RuntimeError:
        # RuntimeError raised when asynchronous tasks disabled (during testing)
        response = jsonify({'result': 'RuntimeError',
                            'status': '500'})
        response.status_code = 500
        return response
    except Exception as e:
        # Unkown Exception raised
        print(e)
        response = jsonify({'result': str(e),
                            'task_id': task_id,
                            'task_info': str(task.info),
                            'status': '500'})
        response.status_code = 500
        return response
    return response


@celery.task(bind=True)
def async_statistics(self, start_time, end_time):
    """
    Gets a specific set of statistically analyzed data from the database to be used in Statistical Analysis.

    Args:
        start_time: Beginning time of window of data being queried
        end_time: End time of window of data being queried

    Returns:
        response: the trimmed blower data, or a status report
        This async function will output a primitive dict of shape:
            {
                result:
                status:
            }
        Where, if successful, 'result' is also a primitive dict containing
        start_time, end_time, and a list of trimmed json blower data (or an
        empty dict if blower wasn't on). If not successful, 'result' will be a
        string containing a status message. 'status' will always be an int,
        referring to an HTTP status code.

        When returned, the statistics_status endpoint handles the primitive result,
        and returns a jsonified output to the user.

    **Example request**:

    Shell command:

    *with email/password:*

    .. sourcecode:: shell

        curl --user <email>:<password> -X GET https://localhost/api/v0.1/statistics/2017-09-13T13:01:57Z/2017-09-13T13:01:59Z

    *or with token:*

    .. sourcecode:: shell

        curl --user <token>: -X GET https://localhost/api/v0.1/statistics/2017-09-13T13:01:57Z/2017-09-13T13:01:59Z

    Command response:

    .. sourcecode:: http

        GET /api/v0.1/statistics/2017-09-13T13:01:57Z/2017-09-13T13:01:59Z HTTP/1.1
        localhost
        Authorization: Basic <b64 encoded email:password or token:>


   :query start_time: Beginning time of window of data being queried
   :query end_time: End time of window of data being queried
   :reqheader Authorization: use cURL tag with <email>:<psswrd>, or <token>:
   :resheader Content-Type: application/json
   :statuscode 200: Successfully retrieved data
   :statuscode 204: No content
   :statuscode 401: Invalid credentials
   :statuscode 403: Not signed in
   """
    #pr = cProfile.Profile()
    #pr.enable()

    self.update_state(state='STARTED',
                        meta={'result': "Gathering data for statistical analysis.",
                              'status': 202})

    # TODO We should define that you cannot run statistics over a super long
    # period since this is not an asynchronous request.
    MAX_API_DATA_S = current_app.config['MAX_API_DATA_PER_REQUEST']
    # issue with collecting more than a half hour at a time
    delta_t_chunk_size = MAX_API_DATA_S
    # Checking and setting up the start and end times

    if not (strict_rfc3339.validate_rfc3339(start_time) and
            strict_rfc3339.validate_rfc3339(end_time)):
        print("Error: datetimes are not RFC 3339")
        response = {'result': "Bad request; datetimes are not RFC 3339.",
                    'status': 400}
        # API will return bad_request
        return response

    start_time_epoch = strict_rfc3339.rfc3339_to_timestamp(start_time)
    end_time_epoch = strict_rfc3339.rfc3339_to_timestamp(end_time)
    if (end_time_epoch < start_time_epoch):
        print("Error: end time is before start time")
        response = {'result': "Bad request; end time is before start time",
                    'status': 400}
        # API will return bad_request
        return response

    temp_start_time_epoch = start_time_epoch
    # Add chunk time to temp time values only if request time exceeds 30 min
    if end_time_epoch - start_time_epoch >= 1800:
        temp_end_time_epoch = start_time_epoch + delta_t_chunk_size
    else:
        temp_end_time_epoch = end_time_epoch

    # Do stuff

    self.update_state(state='PROGRESS',
                        meta={'result': "Finished gathering data, running stats.",
                              'status': 202})

    # @TODO update whatever the actual response is
    response = {'result': {'start_time' : start_time, 'end_time' : end_time,
                           'data': 'here is data'},
                'status': '200'}

    #pr.disable()
    #s = io.StringIO()
    #ps = pstats.Stats(pr, stream=s).sort_stats('tottime')
    #ps.print_stats()
    #print(s.getvalue())

    if response is None:
        # An error occured in Statistics.py, couldn't process request
        response = {'result': "Processing Failure; Statistics returned nothing.",
                    'status': 500}
        return response
    else:
        # successfully returned data
        return response
