from collections import defaultdict
from datetime import date, datetime
import os
import re

from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from forms import FoodLogForm, GoalForm, LoginForm, RegisterForm
from models import FoodLog, User, db
import requests
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv(
    'FLASK_SECRET_KEY', 'dev-key-fallback-change-in-prod'
)

db_url = os.getenv('DATABASE_URL', 'sqlite:///database.db')
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


with app.app_context():
    db.create_all()

USDA_API_KEY = os.getenv("API", "")

COMMON_FOODS = [
    {
        'name': 'Chicken Breast (Cooked)',
        'keywords': ['chicken breast cooked', 'grilled chicken breast'],
        'calories_100g': 165.0,
        'protein_100g': 31.0,
        'carbs_100g': 0.0,
        'fats_100g': 3.6,
        'fiber_100g': 0.0,
    },
    {
        'name': 'Whole Egg',
        'keywords': ['whole egg', 'boiled egg', 'fried egg'],
        'calories_100g': 155.0,
        'protein_100g': 13.0,
        'carbs_100g': 1.1,
        'fats_100g': 11.0,
        'fiber_100g': 0.0,
    },
    {
        'name': 'White Rice (Cooked)',
        'keywords': ['cooked white rice', 'white rice'],
        'calories_100g': 130.0,
        'protein_100g': 2.7,
        'carbs_100g': 28.0,
        'fats_100g': 0.3,
        'fiber_100g': 0.4,
    },
]


def search_usda_api(query, limit=8):
    if not USDA_API_KEY:
        return []

    url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={USDA_API_KEY}"
    payload = {
        "query": query,
        "pageSize": limit,
        "dataType": ["Branded", "Survey (FNDDS)", "Foundation"],
    }

    results = []
    try:
        response = requests.post(url, json=payload, timeout=4)
        if response.status_code == 200:
            data = response.json()
            for food in data.get("foods", []):
                name = food.get("description", "Unknown Food")
                brand = food.get("brandOwner", "")
                if brand:
                    name = f"{brand} - {name}"

                nutrients = {
                    n.get("nutrientName", "").lower(): n.get("value", 0)
                    for n in food.get("foodNutrients", [])
                }

                cal = (
                    nutrients.get("energy")
                    or nutrients.get("energy (kcal)")
                    or 0
                )
                protein = nutrients.get("protein", 0)
                carbs = nutrients.get("carbohydrate, by difference", 0)
                fats = nutrients.get("total lipid (fat)", 0)
                fiber = nutrients.get("fiber, total dietary", 0)

                if float(cal) > 0 or float(protein) > 0:
                    results.append({
                        "name": name.title(),
                        "source": "USDA",
                        "calories_100g": round(float(cal), 1),
                        "protein_100g": round(float(protein), 1),
                        "carbs_100g": round(float(carbs), 1),
                        "fats_100g": round(float(fats), 1),
                        "fiber_100g": round(float(fiber), 1),
                    })
    except Exception as e:
        print(f"USDA Search Error: {e}")

    return results


def search_openfoodfacts_api(query, limit=8):
    clean_query = re.sub(r'[_,-]', ' ', query).strip()
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={clean_query}&search_simple=1&action=process&json=1&page_size={limit}&lc=en"

    results = []
    try:
        headers = {'User-Agent': 'MyFitnessApp/1.0'}
        response = requests.get(url, headers=headers, timeout=4)
        if response.status_code == 200:
            data = response.json()
            for item in data.get('products', []):
                p_name = item.get('product_name_en') or item.get(
                    'product_name'
                )
                brand = item.get('brands', '')
                if not p_name:
                    continue

                full_name = f"{brand} - {p_name}" if brand else p_name

                nutriments = item.get('nutriments', {})
                cal = (
                    nutriments.get('energy-kcal_100g')
                    or nutriments.get('energy-kcal')
                    or 0
                )
                protein = (
                    nutriments.get('proteins_100g')
                    or nutriments.get('proteins')
                    or 0
                )
                carbs = (
                    nutriments.get('carbohydrates_100g')
                    or nutriments.get('carbohydrates')
                    or 0
                )
                fats = (
                    nutriments.get('fat_100g') or nutriments.get('fat') or 0
                )
                fiber = (
                    nutriments.get('fiber_100g')
                    or nutriments.get('fiber')
                    or 0
                )

                if float(cal) > 0 or float(protein) > 0:
                    results.append({
                        'name': full_name.title(),
                        'source': 'OpenFoodFacts',
                        'calories_100g': round(float(cal), 1),
                        'protein_100g': round(float(protein), 1),
                        'carbs_100g': round(float(carbs), 1),
                        'fats_100g': round(float(fats), 1),
                        'fiber_100g': round(float(fiber), 1),
                    })
    except Exception as e:
        print(f"OpenFoodFacts Search Error: {e}")

    return results


def search_food(query):
    query_clean = query.lower().strip()
    results = []

    for food in COMMON_FOODS:
        if query_clean in food["name"].lower() or any(
            query_clean == kw for kw in food["keywords"]
        ):
            results.append({
                "name": food["name"],
                "source": "Local",
                "calories_100g": food["calories_100g"],
                "protein_100g": food["protein_100g"],
                "carbs_100g": food["carbs_100g"],
                "fats_100g": food["fats_100g"],
                "fiber_100g": food["fiber_100g"],
            })

    if not results:
        results = search_usda_api(query_clean)

    if not results:
        results = search_openfoodfacts_api(query_clean)

    return results


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_pw = generate_password_hash(
            form.password.data, method='pbkdf2:sha256'
        )

        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_pw,
        )

        db.session.add(user)
        db.session.commit()

        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=True)
            flash('You are logged in!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/goals', methods=['GET', 'POST'])
@login_required
def goals():
    form = GoalForm()
    if form.validate_on_submit():
        current_user.daily_calorie_goal = form.daily_calorie_goal.data
        current_user.daily_protein_goal = form.daily_protein_goal.data
        current_user.daily_carbs_goal = form.daily_carbs_goal.data
        current_user.daily_fat_goal = form.daily_fat_goal.data

        db.session.commit()
        flash('Your goals have been updated!', 'success')
        return redirect(url_for('dashboard'))

    elif request.method == 'GET':
        form.daily_calorie_goal.data = current_user.daily_calorie_goal
        form.daily_protein_goal.data = current_user.daily_protein_goal
        form.daily_carbs_goal.data = current_user.daily_carbs_goal
        form.daily_fat_goal.data = current_user.daily_fat_goal

    return render_template('goals.html', form=form)


@app.route('/tracker', methods=['GET', 'POST'])
@login_required
def tracker():
    form = FoodLogForm()

    if form.validate_on_submit():
        try:
            log_entry = FoodLog(
                user_id=current_user.id,
                date=date.today(),
                food_name=form.food_name.data,
                state=form.state.data,
                grams=float(form.grams.data),
                calories=float(form.calories.data),
                protein=float(form.protein.data),
                carbs=float(form.carbs.data),
                fats=float(form.fats.data),
                fiber=float(form.fiber.data) if form.fiber.data else 0.0,
                notes=form.notes.data or '',
            )
            db.session.add(log_entry)
            db.session.commit()
            flash('Meal logged successfully!', 'success')
            return redirect(url_for('journal'))
        except Exception as e:
            db.session.rollback()
            print("DATABASE SAVE ERROR:", e)

    return render_template('tracker.html', form=form)


@app.route('/journal')
@login_required
def journal():
    all_logs = (
        FoodLog.query.filter_by(user_id=current_user.id)
        .order_by(FoodLog.id.desc())
        .all()
    )

    grouped_journal = defaultdict(
        lambda: {
            'entries': [],
            'total_calories': 0,
            'total_protein': 0,
            'total_carbs': 0,
            'total_fats': 0,
            'total_fiber': 0,
        }
    )

    for log in all_logs:
        entry_date = log.date if log.date else date.today()
        day_key = entry_date.strftime('%Y-%m-%d')

        grouped_journal[day_key]['entries'].append(log)
        grouped_journal[day_key]['total_calories'] += log.calories or 0
        grouped_journal[day_key]['total_protein'] += log.protein or 0
        grouped_journal[day_key]['total_carbs'] += log.carbs or 0
        grouped_journal[day_key]['total_fats'] += log.fats or 0
        grouped_journal[day_key]['total_fiber'] += log.fiber or 0

    for day, data in grouped_journal.items():
        data['total_calories'] = round(data['total_calories'], 1)
        data['total_protein'] = round(data['total_protein'], 1)
        data['total_carbs'] = round(data['total_carbs'], 1)
        data['total_fats'] = round(data['total_fats'], 1)
        data['total_fiber'] = round(data['total_fiber'], 1)

    return render_template('journal.html', journal=dict(grouped_journal))


@app.route('/delete-log/<int:log_id>', methods=['POST'])
@login_required
def delete_log(log_id):
    log = db.session.get(FoodLog, log_id)
    if log and log.user_id == current_user.id:
        db.session.delete(log)
        db.session.commit()
        flash('Meal entry deleted.', 'info')

    return redirect(url_for('journal'))


@app.route('/api/search-food')
@login_required
def api_search_food():
    query = request.args.get('q', '')

    if len(query.strip()) < 2:
        return jsonify([])

    results = search_food(query)
    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=False)