from wtforms import StringField, SubmitField
from flask_wtf import FlaskForm

class Search(FlaskForm):
    query = StringField("Search here: ")
    submit = SubmitField("Search ")
