from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import InputRequired
from flask_wtf import FlaskForm

# form template class utilized for batch protein search
class BatchSearchForm(FlaskForm):
    accessions = TextAreaField('Protein Accessions', validators=[InputRequired(message="You must enter at least one accession number"), ])
    # need to come back to this to link the terms of use
    terms_of_use = BooleanField('I have read and agree to the terms of use', validators=[InputRequired(message="You must agree to the ProteomeScout terms of use"), ])
    submit = SubmitField('Submit Job')