"""Creates HTML webforms, using WTForms"""
from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField, BooleanField
from wtforms.validators import Required


class JSONForm(FlaskForm):
    """
    JSONForm is a single box HTML Form used to send user
    messages to other parts of the app

    Attributes:
        json_message (obj): Allows user to input message into a TextAreaField.
        submit (obj): Takes the message from the TextAreaField and relays it.
    """
    json_message = TextAreaField("JSON Message", validators=[Required()])
    submit = SubmitField('Submit')


class SearchEnableForm(FlaskForm):
    search_enable = BooleanField(
        "Enable search (disables table auto-update)",
        default=False)
    submit = SubmitField('Submit')
