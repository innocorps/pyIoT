"""WTForms webpage forms for registration and logins"""
from sqlalchemy import func
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Email, Length, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User
from flask import current_app


class LoginForm(FlaskForm):
    """
    Login to the website

    Attributes:
        email: takes the user's email from the StringField from wtforms
        password: takes the user's password from the PasswordField from wtforms
        remember_me: takes account of the user's to remain logged in, or not
        submit: takes the user's decision to 'Log In'
    """
    email = StringField('Email', validators=[Required(),
                                             Length(1, 64),
                                             Email()])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')


class RegistrationForm(FlaskForm):
    """
    Registers a new user

    Attributes:
        email: takes the user's email from the StringField from wtforms
        username: takes the user's username from the StringField from wtforms
        password: takes the user's password from the PasswordField from wtforms
        password2: takes the user's password from the PasswordField from
        wtforms a second time for password verification
        submit: takes the user's decision to 'Register'
    """
    email = StringField('Email', validators=[
        Required(), Length(1, 64), Email(),
        Regexp('^([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})*$',
               0, 'Invalid email address.')])
    username = StringField('Username', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$',
                                          0, 'Usernames must have only '
                                          'letters, '
                                          'numbers, dots or underscores.')])
    password = PasswordField('Password', validators=[
        Required(), Length(8, 64),
        EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm password', validators=[Required()])
    submit = SubmitField('Register')

    # pylint: disable=no-self-use
    def validate_email(self, field):
        """
        Check that the email isn't already registered, and is the right email domain
        as per config

        Args:
            self: is a class argument
            field: is the email

        Returns:
            ValidationError, only if the email is already registered,
            or is not a company email
        """
        email = field.data.lower()
        if User.query.filter(func.lower(User.email) == email).first():
            raise ValidationError('Email already in use.')
        if current_app.config['MAIL_DOMAIN'] not in email:
            raise ValidationError('Not an allowed email domain')

    def validate_username(self, field):
        """
        Check that the username isn't already used

        Args:
            self: is a class argument
            field: is the username

        Returns:
            ValidationError, only if username is already in use.
            Check is case-insensitive.
        """
        username = field.data.lower()
        if User.query.filter(func.lower(User.username) == username).first():
            raise ValidationError('Username already in use.')


class ChangePasswordForm(FlaskForm):
    """
    Change the users password

    Attributes:
        old_password: User must enter their old password first for verification
        password: The new password
        password2: Check of the new password
        submit: Button that submits the request
    """
    old_password = PasswordField('Old password', validators=[Required()])
    password = PasswordField('New password', validators=[
        Required(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm new password', validators=[Required()])
    submit = SubmitField('Update Password')


class PasswordResetRequestForm(FlaskForm):
    """
    Request a password reset

    Attributes:
        email: enter the email that the reset link will be sent to
        submit: Submit the request
    """
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    submit = SubmitField('Reset Password')

    # pylint: disable=no-self-use
    def validate_email(self, field):
        """
        Checks if the email is in the database

        Args:
            field: Contains the email

        Returns:
            ValidationError if the email cannot be found
        """
        email = field.data.lower()
        if User.query.filter(func.lower(User.email) == email).first() is None:
            raise ValidationError('Unknown email address.')


class PasswordResetForm(FlaskForm):
    """
    Reset a users password

    Attributes:
        email: the users email that will be changing the password
        password: new password
        password2: check the new password
        submit: submit the request
    """
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    password = PasswordField('New Password', validators=[
        Required(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm password', validators=[Required()])
    submit = SubmitField('Reset Password')

    # pylint: disable=no-self-use
    def validate_email(self, field):
        """
        Checks if the email is in the database

        Args:
            field: Contains the email

        Returns:
            ValidationError if the email cannot be found
        """
        email = field.data.lower()
        if User.query.filter(func.lower(User.email) == email).first() is None:
            raise ValidationError('Unknown email address.')


class SetAppPasswordRequestForm(FlaskForm):
    """
    Request to set an app password.

    Attributes:
        email: enter the email that the reset link will be sent to
        submit: Submit the request
    """
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    submit = SubmitField('Set App Password')

    # pylint: disable=no-self-use
    def validate_email(self, field):
        """
        Checks if the email is in the database

        Args:
            field: Contains the email

        Returns:
            ValidationError if the email cannot be found
        """
        email = field.data.lower()
        if User.query.filter(func.lower(User.email) == email).first() is None:
            raise ValidationError('Unknown email address.')


class SetAppPasswordForm(FlaskForm):
    """
    Set a user's app password

    Attributes:
        email: the users email that will be setting the password
        password: new password
        password2: check the new password
        submit: submit the request
    """
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    password = PasswordField('New Password', validators=[
        Required(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm password', validators=[Required()])
    submit = SubmitField('Set App Password')

    # pylint: disable=no-self-use
    def validate_email(self, field):
        """
        Checks if the email is in the database

        Args:
            field: Contains the email

        Returns:
            ValidationError if the email cannot be found
        """
        email = field.data.lower()
        if User.query.filter(func.lower(User.email) == email).first() is None:
            raise ValidationError('Unknown email address.')
