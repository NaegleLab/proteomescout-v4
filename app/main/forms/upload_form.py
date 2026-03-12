from wtforms import StringField, TextAreaField, SubmitField, RadioField
from flask_wtf import FlaskForm

class ParentExperiment(object):
    def __init__(self, message=None):
        self.radio = radio
        if not message:
            message = "Required field 'Parent Experiment' cannot be empty."
        def __call__(self, form, field):
            data = field.data
            pass
            
            



class UploadForm(FlaskForm):
    upload_type = RadioField('Upload Type', choices=[
        ('new_dataset', 'New'), 
        ('append_dataset', 'Append'), 
        ('reload_dataset', 'Reload'),
        ('extend_dataset', 'Extendsion')])
    parent_experiment = StringField('Parent Experiment')
    title = StringField('Extension Title')
    description = TextAreaField('Description')
    submit = SubmitField('Search')

    
