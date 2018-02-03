"""Takes JSON files from all the sensors and also shows it on the website"""

# pylint: disable=invalid-name
# pylint: disable=superfluous-parens
# pylint: disable=no-member
import json
import sqlalchemy
from sqlalchemy import desc
from flask import request, render_template, current_app
from flask_login import login_required
from redis import RedisError
from .forms import JSONForm, SearchEnableForm
from . import main
from .. import db, cache, watchdog
from ..accepted_json_message import ACCEPTED_JSON
from ..models import Machine


@main.route('/')
def index():
    """
    Sets up homepage

    Returns:
        render_template using index.html to set up the webpage
    """
    return render_template('index.html')


@main.route("/viewdata", methods=['GET', 'POST'])
@login_required
def show_machine_data():
    """
    Outputs all table data to an HTML table

    Returns:
        render_template, which allows a user to view all the data on
        the website via viewdata.html.
    """
    alive = watchdog.is_alive()

    machine_columns = Machine.__table__.columns.keys()  # Grabs column headers
    page = request.args.get('page', 1, type=int)
    pagination = db.session.query(Machine).order_by(desc(Machine.datetime)).paginate(  # paginates response
        page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    page_items = pagination.items
    # need to convert the sql query to something iterable in the table
    # no coverage here but is tested via same function in api_0_1.machine_post
    dict_list = []
    for item in page_items:
        d = {}
        for column in item.__table__.columns:
            d[column.name] = str(getattr(item, column.name))
        dict_list.append(d)
    data = []
    for item in dict_list:
        data.append(list((item).values()))
    return render_template('viewdata.html', data=data,
                           machine_columns=machine_columns,
                           pagination=pagination, alive=alive)


@main.route("/manualjsonpostdata", methods=['GET', 'POST'])
@login_required
def manual_json_post():
    """
    Put data in database via JSON

    Returns:
        render_template which puts all the data in the website
        database via json_pot.html.
    """
    form = JSONForm()
    is_dict = None
    dict_error = None
    if request.method == 'POST':
        parsed_dict = json_post_to_dict(form)

        if parsed_dict is None:
            dict_error = "JSON message was improperly formatted."
            is_dict = False
            current_app.logger.warning('JSON Form Message '
                                       'Exception: %s', dict_error)
            return render_template('json_post.html',
                                   form=form,
                                   is_dict=is_dict,
                                   error=dict_error)

        json_post = Machine.flatten(parsed_dict)
        flattened_accepted_json = Machine.flatten(ACCEPTED_JSON)
        data = Machine.from_json(json_post)
        to_json_data = data.to_json()

        if not Machine.is_valid_datetime(json_post):
            dict_error = ("Missing datetime or Datetime is not "
                          "in the correct format.")
            is_dict = False
            current_app.logger.warning('JSON Form Message '
                                       'Exception: %s', dict_error)
            return render_template('json_post.html',
                                   form=form,
                                   is_dict=is_dict,
                                   error=dict_error)

        missing_data, invalid_sensors = Machine.invalid_data(
            json_post, flattened_accepted_json)

        if len(missing_data) > 0:
            dict_error = ("Missing data from sensors. "
                          "A sensor may have been removed from the network. "
                          "Missing data: " + str(missing_data))
            is_dict = False
            current_app.logger.warning('JSON Form Message '
                                       'Exception: %s', dict_error)
            return render_template('json_post.html',
                                   form=form,
                                   is_dict=is_dict,
                                   error=dict_error)

        if len(invalid_sensors) > 0:
            dict_error = ("Invalid or extra sensors. "
                          "A sensor may have been added to the network. "
                          "Invalid: " + str(invalid_sensors))
            is_dict = False
            current_app.logger.warning('JSON Form Message '
                                       'Exception: %s', dict_error)
            return render_template('json_post.html',
                                   form=form,
                                   is_dict=is_dict,
                                   error=dict_error)

        """
        Set datetime key in cache if it doesn't already exist.
        Try to commit it to the database if it wasn't in cache already.
        """
        try:
            if cache.get(json_post['datetime']) is None:
                cache.set(json_post['datetime'], to_json_data,
                          timeout=current_app.config['REDIS_CACHE_TIMEOUT'])
                try:
                    db.session.add(data)
                    db.session.commit()
                except sqlalchemy.exc.IntegrityError:
                    is_dict = False
                    dict_error = (
                        "There was a unique constraint error,"
                        " this datetime already appears in the database.")
                    return render_template('json_post.html',
                                           form=form,
                                           is_dict=is_dict,
                                           error=dict_error)
            else:
                is_dict = False
                dict_error = ("The datetime already appears in the cache."
                              " There was a unique constraint error.")
                return render_template('json_post.html',
                                       form=form,
                                       is_dict=is_dict,
                                       error=dict_error)
        except RedisError as e:
            print(e)
            print('Redis port may be closed, the redis server does '
                  'not appear to be running.')
            is_dict = False
            dict_error = ("Redis port may be closed.")
            return render_template('json_post.html',
                                   form=form,
                                   is_dict=is_dict,
                                   error=dict_error)

        dict_error = None
        is_dict = True
        return render_template('json_post.html',
                               form=form,
                               is_dict=is_dict,
                               error=dict_error)

    return render_template('json_post.html',
                           form=form,
                           is_dict=is_dict,
                           error=dict_error)


def json_post_to_dict(form):
    """
    Takes the JSONs out of the messy HTML format and
    splits them into individual dicts.

    Args:
        form: the JSON data.

    Returns:
        parsed_dicts which further organizes and seperates the flattened JSON.
    """
    message = str(form.json_message.data)
    try:
        dict_post = json.loads(message)
        if isinstance(dict_post, str):
            print("JSON Message is improperly formatted.")
            dict_post = None
    except json.decoder.JSONDecodeError as e:
        print("json_post_to_dict: json decoder failed to parse message")
        print(e)
        return None
    return dict_post
