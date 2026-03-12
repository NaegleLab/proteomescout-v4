from wtforms import StringField, TextAreaField, BooleanField, SubmitField, validators
from wtforms.validators import InputRequired
from flask_wtf import FlaskForm


class EmailForm(FlaskForm):
    email = StringField('Email', validators=[validators.DataRequired(), validators.Email()])
    submit = SubmitField('Request Password Reset')


class DownloadForm(FlaskForm):
    annotate = BooleanField('Annotate', default=True)
    submit = SubmitField('Request Download')