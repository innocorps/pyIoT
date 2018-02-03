"""Unit tests for the api"""
import unittest
import json
from base64 import b64encode
from flask import url_for, current_app
from redis import RedisError
from app import create_app, db, cache
from app.models import User

class API2TestCase(unittest.TestCase):

    """Tests GET and POST requests via API"""

    def setUp(self):
        """Create test environment"""
        with open('./tests/example.json') as json_data:
            self.EXAMPLE_JSON_MESSAGE = json.load(json_data)
        with open('./tests/example_compact.json') as json_data:
            self.EXAMPLE_COMPACT_JSON_MESSAGE = json.load(json_data)
        self.Backend = create_app('testing')
        self.app_context = self.Backend.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.Backend.test_client()

    def tearDown(self):
        """Clost test environment"""
        try:
            cache.clear()
        except RedisError:
            print('Redis port is closed, the redis server '
                  'does not appear to be running.')
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # HEADER SETUP

    # pylint: disable=no-self-use
    def get_api_headers(self, username, password, new_post=False):
        """To be able to send auth credentials"""
        if new_post is True:
            return {
                'Authorization': 'Basic ' + b64encode(
                    (username + ':' + password).encode('utf-8')).decode('utf-8'),
                'Accept': 'application/json',
                'Content-Type': 'application/json'}
        else:
            return {
                'Authorization': 'Basic ' + b64encode(
                    (username + ':' + password).encode('utf-8')).decode('utf-8'),
                'Accept': 'application/json',
                'Content-type': 'application/json'}

    def header_no_content_type(self, username, password, new_post=False):
        """To be able to send auth credentials, but missing json headers"""
        if new_post is True:
            return {
                'Authorization': 'Basic ' + b64encode(
                    (username + ':' + password).encode('utf-8')).decode('utf-8')}
        else:
            return {
                'Authorization': 'Basic ' + b64encode(
                    (username + ':' + password).encode('utf-8')).decode('utf-8')
            }

    def header_no_content_encoding(self, username, password):
        """To be able to send auth credentials, but missing json headers"""
        return {
            'Authorization': 'Basic ' + b64encode(
                (username + ':' + password).encode('utf-8')).decode('utf-8'),
            'Content-Type': 'application/json'
        }

    def header_wrong_content_encoding(self, username, password):
        """To be able to send auth credentials, but missing json headers"""
        return {
            'Authorization': 'Basic ' + b64encode(
                (username + ':' + password).encode('utf-8')).decode('utf-8'),
            'Content-Type': 'application/json',
            'Content-Encoding': 'br'
        }

    def header_wrong_content_type(self, username, password):
        """To be able to send auth credentials, but missing json headers"""
        return {
            'Authorization': 'Basic ' + b64encode(
                (username + ':' + password).encode('utf-8')).decode('utf-8'),
            'Content-Type': 'application/xml'
        }

    # TEST ERRORS

    def test_404(self):
        """Checking 404 with a bad url"""
        response = self.client.get(
            '/wrong/url',
            headers=self.get_api_headers('email', 'password'))
        self.assertTrue(response.status_code == 404)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['error'] == 'not found')

    def test_400(self):
        """Checking 400 with a non-JSON message"""
        user = User(email='darth.vader@'+current_app.config['MAIL_DOMAIN'],
                    password='Iamyourfather',
                    confirmed=True)
        db.session.add(user)
        db.session.commit()

        # write post
        response = self.client.post(
            url_for('api_0_1.new_post'),
            headers=self.get_api_headers('darth.vader@'+current_app.config['MAIL_DOMAIN'],
                                         'Iamyourfather', True),
            data='lol')
        self.assertTrue(response.status_code == 400)

    # TEST AUTHENTICATION

    def test_no_user(self):
        """Check 401 with a user that is not registered"""
        response = self.client.get(
            url_for('api_0_1.get_posts'),
            headers=self.get_api_headers('wayne.gretzky@'+current_app.config['MAIL_DOMAIN'],
                                         password='thegreatone'))
        self.assertTrue(response.status_code == 401)

    def test_no_auth(self):
        """Check 403 by not sending credentials"""
        response = self.client.get(url_for('api_0_1.get_posts'),
                                   content_type='application/json')
        self.assertTrue(response.status_code == 403)

    def test_bad_auth(self):
        """Checl 401 with wrong password"""
        # add user
        user = User(email='santa.claus@'+current_app.config['MAIL_DOMAIN'],
                    password='hohoho',
                    confirmed=True)
        db.session.add(user)
        db.session.commit()

        # authenticate with bad password
        response = self.client.get(
            url_for('api_0_1.get_posts'),
            headers=self.get_api_headers('santa.claus@'+current_app.config['MAIL_DOMAIN'],
                                         password='hahaha'))
        self.assertTrue(response.status_code == 401)

    def test_unconfirmed_account(self):
        """Checks users with unconfirmed accounts can't use the api"""
        user = User(email='indianajones@'+current_app.config['MAIL_DOMAIN'],
                    password='junior',
                    confirmed=False)
        db.session.add(user)
        db.session.commit()

        response = self.client.get(
            url_for('api_0_1.get_posts'),
            headers=self.get_api_headers(
                'indianajones@'+current_app.config['MAIL_DOMAIN'],
                'junior'))
        self.assertTrue(response.status_code == 403)
        self.assertTrue(b'Unconfirmed account' in response.data)


    def test_bad_token_auth(self):
        """Check 401 with bad token"""
        # add user
        user = User(email='james.bond@'+current_app.config['MAIL_DOMAIN'],
                    password='007',
                    confirmed=True)
        db.session.add(user)
        db.session.commit()

        # issue request with a bad token
        response = self.client.get(
            url_for('api_0_1.get_posts'),
            headers=self.get_api_headers('bad-token', ''))
        self.assertTrue(response.status_code == 401)


    def test_good_token_auth(self):
        """Check tokens are working correctly"""
        # add user
        user = User(email='michael.schumacher@'+current_app.config['MAIL_DOMAIN'],
                    password='ferrari',
                    confirmed=True)
        db.session.add(user)
        db.session.commit()

        # get token
        response = self.client.get(
            url_for('api_0_1.get_token'),
            headers=self.get_api_headers('michael.schumacher@'+current_app.config['MAIL_DOMAIN'],
                                         password='ferrari'))
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIsNotNone(json_response.get('token'))
        token = json_response['token']

        # issue a request with the token
        response = self.client.get(
            url_for('api_0_1.get_posts'),
            headers=self.get_api_headers(token, ''))
        self.assertTrue(response.status_code == 200)

        # use token to get new token, not allowed
        response = self.client.get(
            url_for('api_0_1.get_token'),
            headers=self.get_api_headers(token, ''))
        self.assertTrue(response.status_code == 401)


    # TEST HEADERS

    def test_missing_json_header(self):
        """Test that error will be caught if the message json header is forgotten"""
        # add user
        user = User(email='fred.flinstone@'+current_app.config['MAIL_DOMAIN'],
                    password='Wilmaaaaaaaaaa',
                    confirmed=True)
        db.session.add(user)
        db.session.commit()

        response = self.client.post(
            url_for('api_0_1.new_post'),
            headers=self.header_no_content_type('fred.flinstone@'+current_app.config['MAIL_DOMAIN'],
                                                'Wilmaaaaaaaaaa', True),
            data=json.dumps(self.EXAMPLE_JSON_MESSAGE))
        self.assertTrue(response.status_code == 400)

    # TEST POSTS

    def test_posts(self):
        """Test posts are working correctly, and they can also be retrieved"""
        # add user
        user = User(email='bill.nye@'+current_app.config['MAIL_DOMAIN'],
                    password='TheScienceGuy',
                    confirmed=True)
        db.session.add(user)
        db.session.commit()

        # write three posts to check time loop api get
        response = self.client.post(
            url_for('api_0_1.new_post'),
            headers=self.get_api_headers('bill.nye@'+current_app.config['MAIL_DOMAIN'],
                                         'TheScienceGuy', True),
            data=json.dumps(self.EXAMPLE_JSON_MESSAGE))
        self.assertTrue(response.status_code == 201)

        example_json = self.EXAMPLE_JSON_MESSAGE
        example_json["datetime"] = "2017-09-13T13:01:58Z"

        response = self.client.post(
            url_for('api_0_1.new_post'),
            headers=self.get_api_headers('bill.nye@'+current_app.config['MAIL_DOMAIN'],
                                         'TheScienceGuy', True),
            data=json.dumps(example_json))
        self.assertTrue(response.status_code == 201)

        example_json = self.EXAMPLE_JSON_MESSAGE
        latest_datetime = "2017-09-13T13:03:00Z"
        example_json["datetime"] = latest_datetime

        response = self.client.post(
            url_for('api_0_1.new_post'),
            headers=self.get_api_headers('bill.nye@'+current_app.config['MAIL_DOMAIN'],
                                         'TheScienceGuy', True),
            data=json.dumps(example_json))
        self.assertTrue(response.status_code == 201)

        # Check data of post
        response = self.client.get(
            url_for('api_0_1.new_post'),
            headers=self.get_api_headers('bill.nye@'+current_app.config['MAIL_DOMAIN'],
                                         'TheScienceGuy'))
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['data'][0]['datetime'] ==
                        latest_datetime
                        )

        # Test getting a specific number of posts (between two time slots)
        response = self.client.get(
            url_for('api_0_1.get_post',
                    start_time='2017-09-13T13:01:57Z',
                    end_time='2017-09-13T13:01:59Z'),
            headers=self.get_api_headers('bill.nye@'+current_app.config['MAIL_DOMAIN'],
                                         password='TheScienceGuy'))
        self.assertTrue(b'2017-09-13T13:01:58Z' in response.data)
        self.assertTrue(b'Could not find data.' in response.data)

    def test_too_many_requests_get_posts(self):
        """Test too many seconds  are requested for get posts"""
        # add user
        user = User(email='bill.nye@'+current_app.config['MAIL_DOMAIN'],
                    password='TheScienceGuy',
                    confirmed=True)
        db.session.add(user)
        db.session.commit()
        response = self.client.get(
            url_for('api_0_1.get_post',
                    start_time='2017-09-13T13:01:57Z',
                    end_time='2018-09-13T13:01:59Z'),
            headers=self.get_api_headers('bill.nye@'+current_app.config['MAIL_DOMAIN'],
                                         password='TheScienceGuy'))
        self.assertTrue(b'Request is above 3600' in response.data)

    def test_compact_posts(self):
        """same as test_posts but using example_compact.json"""
        # add user
        user = User(email='bill.nye@'+current_app.config['MAIL_DOMAIN'],
                    password='TheScienceGuy',
                    confirmed=True)
        db.session.add(user)
        db.session.commit()

        response = self.client.post(
            url_for('api_0_1.new_post'),
            headers=self.get_api_headers('bill.nye@'+current_app.config['MAIL_DOMAIN'],
                                         'TheScienceGuy', True),
            data=json.dumps(self.EXAMPLE_COMPACT_JSON_MESSAGE))
        self.assertTrue(response.status_code == 201)

        # Check data of post
        response = self.client.get(
            url_for('api_0_1.new_post'),
            headers=self.get_api_headers('bill.nye@'+current_app.config['MAIL_DOMAIN'],
                                         'TheScienceGuy'))
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['data'][0]['datetime'] == self.EXAMPLE_COMPACT_JSON_MESSAGE["datetime"])

    def test_empty_posts(self):
        """Send empty body message"""
        # add user
        email = 'too.cool.fo.school@'+current_app.config['MAIL_DOMAIN']
        password = 'Billy Madison'
        user = User(email=email, password=password, confirmed=True)
        db.session.add(user)
        db.session.commit()

        response = self.client.post(
            url_for('api_0_1.new_post'),
            headers=self.get_api_headers(email, password, True),
            data=json.dumps(''))
        self.assertTrue(response.status_code == 400)

    def test_wrong_type_headers(self):
        """Send a message with wrong Content-Type: application/xml header"""
        # add user
        email = 'Tony@'+current_app.config['MAIL_DOMAIN']
        password = 'Stark'
        user = User(email=email, password=password, confirmed=True)
        db.session.add(user)
        db.session.commit()

        response = self.client.post(
            url_for('api_0_1.new_post'),
            headers=self.header_wrong_content_type(email, password),
            data=json.dumps(self.EXAMPLE_JSON_MESSAGE))
        self.assertTrue(response.status_code == 400)

    def test_pagination(self):
        """Test pagination works correctly with a large number of posts"""
        user = User(email='Connor.schentag@'+current_app.config['MAIL_DOMAIN'],
                    password='TheIntern',
                    confirmed=True)
        db.session.add(user)
        db.session.commit()
        i = 2000

        example_json = self.EXAMPLE_JSON_MESSAGE
        example_json["datetime"] = "2017-09-13T13:02:00Z"
        # Make enough posts to cause pagination
        for _ in range(current_app.config['POSTS_PER_PAGE'] + 2):
            example_json["datetime"] = "%s-09-13T13:02:00Z" % i

            response = self.client.post(
                url_for('api_0_1.new_post'),
                headers=self.get_api_headers('Connor.schentag@'+current_app.config['MAIL_DOMAIN'],
                                             'TheIntern', True),
                data=json.dumps(example_json))
            self.assertTrue(response.status_code == 201)
            i += 1

        # Check that the next page url is not none
        response = self.client.get(
            url_for('api_0_1.get_posts'),
            headers=self.get_api_headers('Connor.schentag@'+current_app.config['MAIL_DOMAIN'],
                                         'TheIntern'))
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['next'] is not None)

        # After moving to the next page, check that the url is now none
        response = self.client.get(
            json_response['next'],
            headers=self.get_api_headers('Connor.schentag@'+current_app.config['MAIL_DOMAIN'],
                                         'TheIntern'))
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['next'] is None)

    def test_heartbeat(self):
        """Test a heartbeat message is successfully responded to"""
        user = User(email='brent.leroy@'+current_app.config['MAIL_DOMAIN'],
                    password='cornergandtherub',
                    confirmed=True)
        db.session.add(user)
        db.session.commit()

        heartbeat_json = {"datetime":"2017-08-11T18:39:45Z","heartbeat":"beep"}

        response = self.client.post(
            url_for('api_0_1.new_post'),
            headers=self.get_api_headers('brent.leroy@'+current_app.config['MAIL_DOMAIN'],
                                         'cornergandtherub', True),
            data=json.dumps(heartbeat_json))
        self.assertTrue(response.status_code == 200)
        self.assertTrue(b'Heartbeat received' in response.data)

    # TEST MISSING DATA

    def test_sensors_missing(self):
        """Test warning is sent if None values in return JSON"""
        user = User(email='jim.halpert@'+current_app.config['MAIL_DOMAIN'],
                    password='BigTuna',
                    confirmed=True)
        db.session.add(user)
        db.session.commit()

        #example_json_with_removed_item = self.EXAMPLE_JSON_MESSAGE
        example_json_with_removed_item = {"datetime":"2017-08-11T18:39:45Z"}
        response = self.client.post(
            url_for('api_0_1.new_post'),
            headers=self.get_api_headers('jim.halpert@'+current_app.config['MAIL_DOMAIN'],
                                         'BigTuna', True),
            data=json.dumps(example_json_with_removed_item))
        self.assertTrue(response.status_code == 406)

    def test_sensors_added(self):
        """Test warning is sent if extra items are found in JSON"""
        user = User(email='michael.scott@'+current_app.config['MAIL_DOMAIN'],
                    password='AgentMichaelScarn',
                    confirmed=True)
        db.session.add(user)
        db.session.commit()

        example_json_with_added_item = self.EXAMPLE_JSON_MESSAGE
        example_json_with_added_item['extra_sensor'] = 'dog'

        response = self.client.post(
            url_for('api_0_1.new_post'),
            headers=self.get_api_headers('michael.scott@'+current_app.config['MAIL_DOMAIN'],
                                         'AgentMichaelScarn', True),
            data=json.dumps(example_json_with_added_item))
        self.assertTrue(response.status_code == 406)

    # TEST DATETIME/UNIQUE KEY ERRORS

    def test_missing_datetime(self):
        """Missing datetime is caught seperately"""
        user = User(email='hank.yarbo@'+current_app.config['MAIL_DOMAIN'],
                    password='dogriver',
                    confirmed=True)
        db.session.add(user)
        db.session.commit()

        response = self.client.post(
            url_for('api_0_1.new_post'),
            headers=self.get_api_headers('hank.yarbo@'+current_app.config['MAIL_DOMAIN'],
                                         'dogriver', True),
            data=json.dumps({"date-tme": "2017-08-11T18:39:45Z"}))
        self.assertTrue(b'Datetime is not in the correct ' in response.data)

    def test_bad_datetime_formatting(self):
        """Test error is thrown if datetime is not in rfc3339 format."""
        user = User(email='luke.skywalker@'+current_app.config['MAIL_DOMAIN'],
                    password='ThatsImpossible',
                    confirmed=True)
        db.session.add(user)
        db.session.commit()

        bad_datetime_json = self.EXAMPLE_JSON_MESSAGE
        bad_datetime_json["datetime"] = "201709-13T13:01:58Z"

        response = self.client.post(
            url_for('api_0_1.new_post'),
            headers=self.get_api_headers('luke.skywalker@'+current_app.config['MAIL_DOMAIN'],
                                         'ThatsImpossible', True),
            data=json.dumps(bad_datetime_json))
        self.assertTrue(response.status_code == 406)
        self.assertTrue(b'Datetime is not in the correct' in response.data)

    def test_same_post_cache(self):
        """
        Check that an error will be thrown if the
        datetime primary key is already in the database
        """
        user = User(email='yoda@'+current_app.config['MAIL_DOMAIN'],
                    password='DoOrDoNot',
                    confirmed=True)
        db.session.add(user)
        db.session.commit()

        response = self.client.post(
            url_for('api_0_1.new_post'),
            headers=self.get_api_headers('yoda@'+current_app.config['MAIL_DOMAIN'],
                                         'DoOrDoNot', True),
            data=json.dumps(self.EXAMPLE_JSON_MESSAGE))
        self.assertTrue(response.status_code == 201)

        response = self.client.post(
            url_for('api_0_1.new_post'),
            headers=self.get_api_headers('yoda@'+current_app.config['MAIL_DOMAIN'],
                                         'DoOrDoNot', True),
            data=json.dumps(self.EXAMPLE_JSON_MESSAGE))
        self.assertTrue(b'This datetime is already in cache' in response.data)
        self.assertTrue(response.status_code == 406)

    def test_same_post_database(self):
        """
        Check that an error will be thrown if the
        datetime primary key is already in the database
        """
        user = User(email='yoda@'+current_app.config['MAIL_DOMAIN'],
                    password='DoOrDoNot',
                    confirmed=True)
        db.session.add(user)
        db.session.commit()

        response = self.client.post(
            url_for('api_0_1.new_post'),
            headers=self.get_api_headers('yoda@'+current_app.config['MAIL_DOMAIN'],
                                         'DoOrDoNot', True),
            data=json.dumps(self.EXAMPLE_JSON_MESSAGE))
        self.assertTrue(response.status_code == 201)

        try:
            cache.clear()
        except RedisError:
            print('Redis port is closed, the redis server '
                  'does not appear to be running.')

        response = self.client.post(
            url_for('api_0_1.new_post'),
            headers=self.get_api_headers('yoda@'+current_app.config['MAIL_DOMAIN'],
                                         'DoOrDoNot', True),
            data=json.dumps(self.EXAMPLE_JSON_MESSAGE))
        self.assertTrue(b'This datetime is already in the database.' in response.data)
        self.assertTrue(response.status_code == 406)
