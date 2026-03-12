from wtforms import ValidationError

class SaltedPasswordEqualTo(object):

    def __init__(self, user, message=None):
        if not message:
            message = "The password you have entered does not match our records"
        self.message = message
        self.user = user

    def __call__(self, form, field):
        data = field.data
        if not self.user.check_password(data):
            raise ValidationError(self.message)