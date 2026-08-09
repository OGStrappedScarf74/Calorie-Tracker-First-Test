from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    # Custom daily goals
    daily_calorie_goal = db.Column(db.Integer, default=2000)
    daily_protein_goal = db.Column(db.Integer, default=150)
    daily_carbs_goal = db.Column(db.Integer, default=200)
    daily_fat_goal = db.Column(db.Integer, default=65)

    logs = db.relationship('FoodLog', backref='author', lazy=True, cascade="all, delete-orphan")


class FoodLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)

    food_name = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(20), default='cooked') 
    grams = db.Column(db.Float, nullable=False)
    calories = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    fats = db.Column(db.Float, nullable=False)
    fiber = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text, nullable=True)