from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, FloatField, DateField, TextAreaField ,SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional, InputRequired ,NumberRange
from models import User , db

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=30)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class GoalForm(FlaskForm):
    daily_calorie_goal = IntegerField('Daily Calorie Goal', validators=[DataRequired()])
    daily_protein_goal = IntegerField('Protein Goal (g)', validators=[DataRequired()])
    daily_carbs_goal = IntegerField('Carbs Goal (g)', validators=[DataRequired()])
    daily_fat_goal = IntegerField('Fat Goal (g)', validators=[DataRequired()])
    submit = SubmitField('Update Goals')

class FoodLogForm(FlaskForm):
    food_name = StringField('Food Name', validators=[DataRequired()])
    state = SelectField('State', choices=[('as_is', 'As Is / Any'), ('raw', 'Raw'), ('cooked', 'Cooked')],
                        default='as_is')

    # Use InputRequired() for all numbers so 0 or 0.0 is accepted!
    grams = FloatField('Grams', validators=[InputRequired(), NumberRange(min=0.1)])
    calories = FloatField('Calories', validators=[InputRequired(), NumberRange(min=0)])
    protein = FloatField('Protein (g)', validators=[InputRequired(), NumberRange(min=0)])
    carbs = FloatField('Carbs (g)', validators=[InputRequired(), NumberRange(min=0)])
    fats = FloatField('Fats (g)', validators=[InputRequired(), NumberRange(min=0)])

    fiber = FloatField('Fiber (g)', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Add Entry')