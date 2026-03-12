from wtforms import SubmitField, PasswordField
from wtforms.validators import EqualTo, InputRequired, Regexp
from flask_wtf import FlaskForm
from app.config import strings
from app.main.forms.validators.password_validator import SaltedPasswordEqualTo

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField("Current Password")
    new_password = PasswordField("New Password", validators=[InputRequired(strings.failure_reason_form_fields_cannot_be_empty), Regexp('^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[!\"#$%&\'()*+,-./:;<=>?@\\[\]^_`{|}~]).{8,}', message="The new password must be at least 8 characters long and must contain one upper-case, one lower-case, one numeric and one special character"), ])
    confirm_password = PasswordField("Confirm Password", validators=[InputRequired(strings.failure_reason_form_fields_cannot_be_empty), EqualTo('new_password', strings.failure_reason_new_passwords_not_matching)])
    submit = SubmitField("Change Password")

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.old_password.validators = [InputRequired(strings.failure_reason_form_fields_cannot_be_empty), SaltedPasswordEqualTo(self.user), ]