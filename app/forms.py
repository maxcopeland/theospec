from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, ValidationError, TextAreaField, \
                    FieldList, FormField, RadioField, SelectField, IntegerField, DecimalField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange
from app.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', 
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', 
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Post')

class UploadForm(FlaskForm):
    material = StringField('Material', validators=[DataRequired()])
    file = FileField(validators=[FileRequired(), FileAllowed(['csv', 'xlsx', 'txt'], 'Only .csv, .txt, or .xlsx files allowed')])
    submit = SubmitField('Upload')

class SimulatorForm(FlaskForm):
    medium = RadioField('Medium', choices = [('Air', 'Air'), ('Water', 'Water')], validators=[DataRequired()])
    active_layers = IntegerField('Number of Active Layers', validators=[DataRequired(), 
                                                              NumberRange(min=1, max=10, 
                                                              message="Number of layers can range from 1 to 10")])
    trench_layers = IntegerField('Number of Trench Layers', validators=[DataRequired(), 
                                                              NumberRange(min=1, max=10, 
                                                              message="Number of layers can range from 1 to 10")])
    pattern_density = DecimalField('Pattern Density', validators=[DataRequired(), 
                                                              NumberRange(min=0, max=1, 
                                                              message="Pattern density can range from 0 to 1")])
    submit = SubmitField('Send to Dashboard')
