"""
Template for the database. After a change, a database upgrade must be done
"""

# pylint: disable=invalid-name
import collections
import strict_rfc3339
from flask import current_app
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from . import db, login_manager

# pylint: disable=no-member
class User(UserMixin, db.Model):
    """
    Template for the User table

    Attributes:
        __tablename__: table title
        id: User id
        username: Takes the user's username
        email: Takes the user's email
        password_hash: storing the hashed & salted password
    """
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), index=True)
    email = db.Column(db.String(128), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)

    @property
    def password(self):
        """
        Password should not be readable

        Args:
            self: is a class argument

        Raises:
            AttributeError: when the password contains an unreadable attribute
        """
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        """
        Hash password so it is not stored plaintext in the db

        Args:
            self: is a class argument
            password: is the un-hashed password

        Returns:
            self.password_hash, which is now the hashed password
        """
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """
        Verify the hashed password is in the db

        Args:
            self: is a class argument
            password: is the un-hashed password

        Returns:
            check_password_hash which verifies that the
            hashed password is in the database
        """
        return check_password_hash(self.password_hash, password)

    def generate_auth_token(self, expiration):
        """
        Generates the auth token if username and password are given

        Args:
            self: is a class argument
            expiration: how long the token will work for

        Returns:
            s.dumps which generates the auth_token
        """
        s = Serializer(current_app.config['SECRET_KEY'],
                       expires_in=expiration)
        return s.dumps({'id': self.id}).decode('ascii')

    @staticmethod
    def verify_auth_token(token):
        """
        Verifies the auth token

        Args:
            token: user's authentication token

        Returns:
            User.query.get(data['id']), gets user id after token is verified
        """
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except BaseException:
            return None
        return User.query.get(data['id'])

    def generate_confirmation_token(self, expiration=3600):
        """
        Generates the confirmation token used to verify new user

        Args:
            expiration: expiration of token, default 1 hour

        Returns:
            The new token
        """
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        """
        Confirms the confirmation token used to verify new user

        Args:
            token: The confirmation token

        Returns:
            True if the token is valid, False if it is not
        """
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except BaseException:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        db.session.commit()
        return True

    def generate_reset_token(self, expiration=3600):
        """
        Generates a reset token if a user requests a password reset

        Args:
            expiration: The token will expire after an hour

        Returns:
            the reset token
        """
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        """
        Resets the users password after a password reset request

        Args:
            token: The token for authentication
            new_password: The users new password

        Returns:
            True if the token is valid, otherwise False
        """
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except BaseException:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        db.session.commit()
        return True


@login_manager.user_loader
def load_user(user_id):
    """
    Loads user for queries

    Args:
        user_id: user's token verified id

    Results:
        User.query.get(int(user_id)) which loads the user
    """
    return User.query.get(int(user_id))


class AnonymousUser(AnonymousUserMixin):
    """Used as user when they are not signed in"""
    # pylint: disable=no-self-use

    def is_administrator(self):
        """
        If not signed in

        Args:
            self: is a class argument

        Returns:
            Flase which stops the user if the user is not signed in
        """
        return False  # pragma: no cover


login_manager.anonymous_user = AnonymousUser


class Machine(db.Model):
    """Template for the Machine Info table"""
    __tablename__ = 'machine'
    # metadata
    datetime = db.Column(db.String(128), primary_key=True)
    sensor_1 = db.Column(db.String(128))

    @staticmethod
    def flatten(dictionary, parent_key='', sep='__'):
        """
        Flattens nested incoming JSON messages

        Args:
            dictionary: input dictionary.
            parent_key: the key for the nest
            sep: is the characters between each flattened level

        Returns:
            dict, which takes the data and formats it into a
            dictionary and indexes them by keys
        """
        items = []
        for key, value in dictionary.items():
            new_key = parent_key + sep + key if parent_key else key
            if isinstance(value, collections.MutableMapping):
                items.extend(Machine.flatten(value, new_key, sep=sep).items())
            else:
                items.append((new_key, value))
        return dict(items)

    @staticmethod
    def is_valid_datetime(json_post):
        """
        Determines if the datetime is strictly RFC3339

        Args:
            json_post: a json message as a python dict

        Returns:
            True if the value in key=datetime is RFC3339
        """
        try:
            if not strict_rfc3339.validate_rfc3339(json_post["datetime"]):
                return False
            else:
                return True
        except KeyError as e:
            print(e)
            return False

    @staticmethod
    def invalid_data(json_post, accepted_json):
        """
        Analyzes json message for any None values, returns which ones are
        missing.

        Args:
            json_post: a json message stored as a flattened python dict
            accepted_json: a json message that matches the accepted API

        Returns:
            A list of missing data or invalid sensors as a tuple of
            (missing_data, invalid_sensors)
        """

        missing_data = []
        data = Machine.from_json(json_post)
        to_json_data = data.to_json()
        for key, value in to_json_data.items():
            if value == None:
                if not current_app.config['TESTING']:  # pragma: no cover
                    # disable print statement during testing
                    # to avoid filling console with messages
                    print('WARNING: Data missing for the following sensor:',
                          key)
                missing_data.append(key)

        invalid_sensors = []
        for key in json_post.keys():
            if key not in accepted_json:
                if not current_app.config['TESTING']:  # pragma: no cover
                    # disable print statement during testing
                    # to avoid filling console with messages
                    print('WARNING: The following sensor has been '
                          'added and is not in the database:', key)
                    print('Ensure this new sensor is added to the appropriate '
                          'backend functions.')
                invalid_sensors.append(key)
        return missing_data, invalid_sensors

    def to_json(self):
        """
        Converts to JSON for API

        Args:
            self: is a class argument

        Returns:
            json_post which is the converted JSON for API
        """
        json_post = {
            # Metadata
            'datetime': self.datetime,
            'sensor_1': self.sensor_1
        }  # ADD MORE SENSORS HERE
        return json_post

    # pylint: disable=line-too-long
    @staticmethod
    def from_json(json_post):
        """
        Converts from JSON for API

        Args:
            json_post: the converted JSON data for the API

        Results:
            Machine, which is the newly converted JSON data for API

        Raisess:
            ValidationError is date or time are missing
        """
        # Metadata
        datetime = json_post.get('datetime')
        sensor_1 = json_post.get('sensor_1')

        return Machine(datetime=datetime,  # ADD MORE SENSORS HERE
                       sensor_1=sensor_1)
