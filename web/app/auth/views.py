"""login, logout and register view functions"""
from flask import render_template, redirect, \
    request, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from .forms import LoginForm, RegistrationForm, ChangePasswordForm, \
    PasswordResetRequestForm, PasswordResetForm
from .oauth import OAuthSignIn
from .. import db, logger
from ..models import User
from ..email import send_email
# pylint: disable=no-member


@auth.before_app_request
def before_request():
    """
    Before each request, this makes sure the user is
    authenticated and the account is confirmed

    Returns:
        redirects to /unconfirmed if the user is not confirmed
    """
    if (current_user.is_authenticated and not
            current_user.confirmed and request.endpoint[:5] != 'auth.'):
        return redirect(url_for('auth.unconfirmed'))


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login form which decides whether to allow a user to login

    Returns:
        render_template, creates a login form template for the user to login
    """
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        try:
            if user is not None and user.verify_password(form.password.data):
                login_user(user, form.remember_me.data)
                if (not current_app.config['TESTING'] and not
                        current_app.config['DEBUG']):  # pragma: no cover
                    logger.info(str(user.username) +
                                ' signed In. IP Address: ' +
                                str(request.remote_addr))
                return redirect(request.args.get('next')
                                or url_for('main.index'))
            flash('Invalid username or password.')
        except BaseException:
            flash('Invalid username or password.')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    """
    Logout redirect which runs after the user logs out

    Returns:
        redirect, which sends the user to page which notifys them that
        they have been logged out
    """
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))


@auth.route('/oauth/<provider>')
def oauth_authorization(provider):
    """Starts the oauth process by calling the authorizate function

    Args:
        provider: The provider (ie. Google, Facebook) that is
        being used to perform the authentication.

    Returns:
        redirects to index if the user is already signed in,
        therwise calls the authorize function to begin authorizing

    """
    if not current_user.is_anonymous:  # checks if user is already signed in
        return redirect(url_for('main.index'))
    # gets provider to call correct auth function
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@auth.route('/oauth_callback/<provider>')
def oauth_callback(provider):
    """

    Args:
        provider: The provider (ie. Google, Facebook)
        that is being used to perform the authentication.

    Returns:
        redirects to index if the authentication fails, or to the login screen
        if the user uses an email that is not allowed.
        If the authentication is successful, it redirects to index.
    """
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    # gets provider to call correct auth function
    oauth = OAuthSignIn.get_provider(provider)
    username, email = oauth.callback()
    if email is None:  # need an email to complete authentication
        flash('Authentication failed.')
        return redirect(url_for('main.index'))
    user = User.query.filter_by(email=email).first()
    if not user:
        if username is None or username == "":
            # if a username is not found, it pulls t from the email
            username = email.split('@')[0]
        # checks for correct domain email, fails if it isn't
        if email.split('@')[1] != current_app.config['MAIL_DOMAIN']:
            flash('You cannot login with this email.')
            return redirect(url_for('auth.login'))
        # confirmed is True, Google sign in doesn't require confirmation
        user = User(username=username, email=email, confirmed=True)
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    """
    Registration form which allows the user to register their email,
    password, and username into the system

    Returns:
        render-template, which takes the user to a pgae notifying them that
        they have registered and can now login
    """
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        # pylint: disable=no-member
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        response = send_email(user.email, 'Confirm Your Account',
                              'auth/email/confirm', user=user, token=token)
        flash('A confirmation email has been sent to you by email.')
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    """
    Confirms the authentication token. This is mainly done in models.py,
    so this just calls that function.

    Args:
        token: Confirmation token

    Returns:
        redirects to main.index
    """
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('You have confirmed your account.')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('main.index'))


@auth.route('/unconfirmed')
def unconfirmed():
    """
    Displays webpage if the user is unconfirmed

    Returns:
        renders html template for unconfirmed user
    """
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/confirm')
@login_required
def resend_confirmation():
    """
    If the users confirmation token is no longer valid,
    this is called to send another

    Returns:
        redirects to main.index after the email has been sent.
    """
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account',
               'auth/email/confirm', user=current_user, token=token)
    flash('A new confirmation token has been sent to you by email.')
    return redirect(url_for('main.index'))


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """
    Change the users password if the user so chooses.
    First checks if the user is signed into a
    google account, and redirects if True.

    Returns:
        redirects to main.index after form submission
    """
    user_id = current_user.get_id()
    user = User.query.filter_by(id=user_id).first()
    # if password_hash is empty, they are using a google account
    if user.password_hash is None:
        # they can not change their google password here
        flash('You cannot change your password when signed '
              'in with a Google account.')
        return redirect(url_for('main.index'))
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()
            flash('Your password has been updated.')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid password.')
    return render_template("auth/change_password.html", form=form)


@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    """
    If the user forgets their password, they may request a password reset.

    Returns:
        redirects to auth.login if the email is sent,
        else renders the reset_password page
    """
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.password_hash is None:
            flash('This email is associated with a Google account, '
                  'the password cannot be reset here.')
            return redirect(url_for('auth.login'))
        token = user.generate_reset_token()
        response = send_email(user.email, 'Reset Your Password',
                              'auth/email/reset_password',
                              user=user, token=token,
                              next=request.args.get('next'))
        flash('An email with instructions to reset your password has been '
              'sent to you.')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    """
    The user is taken here after they click the link
    in the password reset email

    Returns:
        redirects to either auth.login (if successful) or
        main.index (if unsuccessful)
    """
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user.reset_password(token, form.password.data):
            flash('Your password has been updated.')
            return redirect(url_for('auth.login'))
        flash('The password reset link is invalid or has expired.')
        return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)
