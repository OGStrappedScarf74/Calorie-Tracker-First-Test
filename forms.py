from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    IntegerField,
    FloatField,
    TextAreaField,
    SelectField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    EqualTo,
    ValidationError,
    Optional,
    InputRequired,
    NumberRange,
    Regexp,
)
from models import User


# ==================================================
# REGISTRATION
# ==================================================

class RegisterForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(
                min=3,
                max=20,
                message="Username must be between 3 and 20 characters.",
            ),
            Regexp(
                r"^[A-Za-z0-9_.-]+$",
                message=(
                    "Username can only contain letters, numbers, "
                    "underscores, periods, and hyphens."
                ),
            ),
        ],
    )

    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email(),
        ],
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(
                min=8,
                max=20,
                message="Password must be between 8 and 20 characters.",
            ),
        ],
    )

    submit = SubmitField("Sign Up")

    def validate_username(self, username):
        user = User.query.filter_by(
            username=username.data
        ).first()

        if user:
            raise ValidationError(
                "That username is taken."
            )

    def validate_email(self, email):
        user = User.query.filter_by(
            email=email.data
        ).first()

        if user:
            raise ValidationError(
                "That email is already registered."
            )


# ==================================================
# LOGIN
# ==================================================

class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email(),
        ],
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(
                max=20,
                message="Password cannot exceed 20 characters.",
            ),
        ],
    )

    submit = SubmitField("Login")


# ==================================================
# GOALS
# ==================================================

class GoalForm(FlaskForm):
    daily_calorie_goal = IntegerField(
        "Daily Calorie Goal",
        validators=[
            DataRequired(),
            NumberRange(
                min=1,
                max=100000,
                message="Enter a valid calorie goal.",
            ),
        ],
    )

    daily_protein_goal = IntegerField(
        "Protein Goal (g)",
        validators=[
            DataRequired(),
            NumberRange(
                min=0,
                max=10000,
                message="Enter a valid protein goal.",
            ),
        ],
    )

    daily_carbs_goal = IntegerField(
        "Carbs Goal (g)",
        validators=[
            DataRequired(),
            NumberRange(
                min=0,
                max=10000,
                message="Enter a valid carbs goal.",
            ),
        ],
    )

    daily_fat_goal = IntegerField(
        "Fat Goal (g)",
        validators=[
            DataRequired(),
            NumberRange(
                min=0,
                max=10000,
                message="Enter a valid fat goal.",
            ),
        ],
    )

    submit = SubmitField("Update Goals")


# ==================================================
# FOOD LOG
# ==================================================

class FoodLogForm(FlaskForm):
    food_name = StringField(
        "Food Name",
        validators=[
            DataRequired(),
            Length(
                max=200,
                message="Food name is too long.",
            ),
        ],
    )

    state = SelectField(
        "State",
        choices=[
            ("as_is", "As Is / Any"),
            ("raw", "Raw"),
            ("cooked", "Cooked"),
        ],
        default="as_is",
    )

    grams = FloatField(
        "Grams",
        validators=[
            InputRequired(),
            NumberRange(
                min=0.1,
                max=100000,
                message="Enter a valid amount of grams.",
            ),
        ],
    )

    calories = FloatField(
        "Calories",
        validators=[
            InputRequired(),
            NumberRange(
                min=0,
                max=1000000,
                message="Enter a valid calorie value.",
            ),
        ],
    )

    protein = FloatField(
        "Protein (g)",
        validators=[
            InputRequired(),
            NumberRange(
                min=0,
                max=100000,
                message="Enter a valid protein value.",
            ),
        ],
    )

    carbs = FloatField(
        "Carbs (g)",
        validators=[
            InputRequired(),
            NumberRange(
                min=0,
                max=100000,
                message="Enter a valid carbs value.",
            ),
        ],
    )

    fats = FloatField(
        "Fats (g)",
        validators=[
            InputRequired(),
            NumberRange(
                min=0,
                max=100000,
                message="Enter a valid fats value.",
            ),
        ],
    )

    fiber = FloatField(
        "Fiber (g)",
        validators=[
            Optional(),
            NumberRange(
                min=0,
                max=100000,
                message="Enter a valid fiber value.",
            ),
        ],
    )

    notes = TextAreaField(
        "Notes",
        validators=[
            Optional(),
            Length(
                max=1000,
                message="Notes cannot exceed 1000 characters.",
            ),
        ],
    )

    submit = SubmitField("Add Entry")