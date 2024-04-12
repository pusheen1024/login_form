from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired


class DepartmentsForm(FlaskForm):
    title = StringField('Department title', validators=[DataRequired()])
    chief = IntegerField('Chief id', validators=[DataRequired()])
    members = StringField('Members')
    email = StringField('Email')
    submit = SubmitField('Submit')