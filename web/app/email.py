"""Script that calls SMTP server and sends emails"""
from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from . import mail


def send_async_email(app, msg):
    """
    Sends email asyncronously so as not to slow down app

    Args:
        app: needs app instance to send it correctly,
        else it can't be built yet
        msg: email message
    """
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    """
    Sends email using an SMTP server

    Args:
        to: email recipients
        subject: email subject
        template: txt or html template for the email
        kwargs: Email arguments, such as tokens

    Returns:
        thr: The thread that send_email runs on to
        avoid slowing down the rest of the app
    """
    app = current_app._get_current_object()
    msg = Message(app.config['BACKEND_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=app.config['BACKEND_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr
