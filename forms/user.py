from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Optional
from flask_wtf import FlaskForm

class SubmitQueryForm(FlaskForm):
    query = StringField("Query ", validators=[DataRequired()])
    context = StringField("AI context ", validators=[DataRequired()])
    log_dir = StringField("Logging Dir Temp", validators=[Optional()])
    n_tokens = IntegerField("Number of tokens (max)", validators=[Optional()])
    model_name = StringField("Model name", validators=[Optional()])
    submit = SubmitField('submit')

