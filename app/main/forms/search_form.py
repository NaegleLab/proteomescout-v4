from wtforms import StringField, BooleanField, SubmitField
from flask_wtf import FlaskForm

class ProteinSearchForm(FlaskForm):
    protein = StringField('Protein')
    peptide = StringField('Peptide')
    species = StringField('Species')
    protein_names = BooleanField('Search Protein Names')
    submit = SubmitField('Search')