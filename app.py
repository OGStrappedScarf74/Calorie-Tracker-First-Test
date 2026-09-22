from collections import defaultdict
from datetime import date
import os
import re

import requests
from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from werkzeug.security import check_password_hash, generate_password_hash

from forms import FoodLogForm, GoalForm, LoginForm, RegisterForm
from models import FoodLog, User, db


# ==================================================
# APP CONFIG
# ==================================================

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "FLASK_SECRET_KEY",
    "dev-key-fallback-change-in-prod",
)

database_url = os.getenv(
    "DATABASE_URL",
    "sqlite:///database.db",
)

if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql://",
        1,
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

USDA_API_KEY = os.getenv("API")


# ==================================================
# LOGIN
# ==================================================

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


with app.app_context():
    db.create_all()


# ==================================================
# COMMON FOODS
# ==================================================

COMMON_FOODS = [
    {
        "name": "Chicken Breast (Cooked)",
        "keywords": [
            "chicken breast",
            "chicken breast cooked",
            "grilled chicken breast",
        ],
        "calories_100g": 165.0,
        "protein_100g": 31.0,
        "carbs_100g": 0.0,
        "fats_100g": 3.6,
        "fiber_100g": 0.0,
    },
    {
        "name": "Whole Egg",
        "keywords": [
            "egg",
            "whole egg",
            "boiled egg",
            "fried egg",
        ],
        "calories_100g": 155.0,
        "protein_100g": 13.0,
        "carbs_100g": 1.1,
        "fats_100g": 11.0,
        "fiber_100g": 0.0,
    },
    {
        "name": "White Rice (Cooked)",
        "keywords": [
            "rice",
            "white rice",
            "cooked white rice",
        ],
        "calories_100g": 130.0,
        "protein_100g": 2.7,
        "carbs_100g": 28.0,
        "fats_100g": 0.3,
        "fiber_100g": 0.4,
    },
    {
        "name": "Egg Whites (Liquid or Cooked)",
        "keywords": [
            "egg white",
            "egg whites",
            "liquid egg whites",
        ],
        "calories_100g": 52.0,
        "protein_100g": 10.9,
        "carbs_100g": 0.7,
        "fats_100g": 0.2,
        "fiber_100g": 0.0,
    },
    {
        "name": "Lean Ground Beef (93/7 Cooked)",
        "keywords": [
            "ground beef",
            "lean ground beef",
            "beef 93/7",
            "minced beef",
        ],
        "calories_100g": 172.0,
        "protein_100g": 26.0,
        "carbs_100g": 0.0,
        "fats_100g": 7.5,
        "fiber_100g": 0.0,
    },
    {
        "name": "Salmon (Cooked)",
        "keywords": [
            "salmon",
            "baked salmon",
            "grilled salmon",
        ],
        "calories_100g": 206.0,
        "protein_100g": 22.0,
        "carbs_100g": 0.0,
        "fats_100g": 12.3,
        "fiber_100g": 0.0,
    },
    {
        "name": "Canned Tuna (in Water)",
        "keywords": [
            "tuna",
            "canned tuna",
            "tuna in water",
        ],
        "calories_100g": 116.0,
        "protein_100g": 25.5,
        "carbs_100g": 0.0,
        "fats_100g": 1.0,
        "fiber_100g": 0.0,
    },
    {
        "name": "Whey Protein Powder",
        "keywords": [
            "whey protein",
            "protein powder",
            "whey isolate",
        ],
        "calories_100g": 370.0,
        "protein_100g": 80.0,
        "carbs_100g": 6.0,
        "fats_100g": 3.0,
        "fiber_100g": 0.0,
    },
    {
        "name": "Non-Fat Greek Yogurt",
        "keywords": [
            "greek yogurt",
            "nonfat greek yogurt",
            "0% greek yogurt",
            "plain greek yogurt",
        ],
        "calories_100g": 59.0,
        "protein_100g": 10.0,
        "carbs_100g": 3.6,
        "fats_100g": 0.4,
        "fiber_100g": 0.0,
    },
    {
        "name": "Low-Fat Cottage Cheese (2%)",
        "keywords": [
            "cottage cheese",
            "low fat cottage cheese",
            "2% cottage cheese",
        ],
        "calories_100g": 81.0,
        "protein_100g": 11.0,
        "carbs_100g": 4.7,
        "fats_100g": 2.3,
        "fiber_100g": 0.0,
    },
    {
        "name": "Rolled Oats (Raw)",
        "keywords": [
            "oats",
            "oatmeal",
            "rolled oats",
            "raw oats",
        ],
        "calories_100g": 379.0,
        "protein_100g": 13.2,
        "carbs_100g": 67.7,
        "fats_100g": 6.5,
        "fiber_100g": 10.1,
    },
    {
        "name": "Sweet Potato (Baked)",
        "keywords": [
            "sweet potato",
            "baked sweet potato",
            "yams",
        ],
        "calories_100g": 90.0,
        "protein_100g": 2.0,
        "carbs_100g": 20.7,
        "fats_100g": 0.1,
        "fiber_100g": 3.3,
    },
    {
        "name": "Brown Rice (Cooked)",
        "keywords": [
            "brown rice",
            "cooked brown rice",
        ],
        "calories_100g": 123.0,
        "protein_100g": 2.7,
        "carbs_100g": 25.6,
        "fats_100g": 1.0,
        "fiber_100g": 1.6,
    },
    {
        "name": "Peanut Butter",
        "keywords": [
            "peanut butter",
            "pb",
            "natural peanut butter",
        ],
        "calories_100g": 588.0,
        "protein_100g": 25.0,
        "carbs_100g": 20.0,
        "fats_100g": 50.0,
        "fiber_100g": 6.0,
    },
    {
        "name": "Almonds (Raw)",
        "keywords": [
            "almonds",
            "raw almonds",
            "almond nuts",
        ],
        "calories_100g": 579.0,
        "protein_100g": 21.2,
        "carbs_100g": 21.6,
        "fats_100g": 49.9,
        "fiber_100g": 12.5,
    },
    {
        "name": "Broccoli (Cooked)",
        "keywords": [
            "broccoli",
            "steamed broccoli",
            "cooked broccoli",
        ],
        "calories_100g": 35.0,
        "protein_100g": 2.4,
        "carbs_100g": 7.2,
        "fats_100g": 0.4,
        "fiber_100g": 3.3,
    },
    {
        "name": "Avocado",
        "keywords": [
            "avocado",
            "fresh avocado",
        ],
        "calories_100g": 160.0,
        "protein_100g": 2.0,
        "carbs_100g": 8.5,
        "fats_100g": 14.7,
        "fiber_100g": 6.7,
    },
    {
        "name": "Olive Oil",
        "keywords": [
            "olive oil",
            "extra virgin olive oil",
            "evoo",
        ],
        "calories_100g": 884.0,
        "protein_100g": 0.0,
        "carbs_100g": 0.0,
        "fats_100g": 100.0,
        "fiber_100g": 0.0,
    },
    {
        "name": "Banana",
        "keywords": [
            "banana",
            "raw banana",
        ],
        "calories_100g": 89.0,
        "protein_100g": 1.1,
        "carbs_100g": 22.8,
        "fats_100g": 0.3,
        "fiber_100g": 2.6,
    },
    {
        "name": "Ground Turkey (93/7 Cooked)",
        "keywords": [
            "ground turkey",
            "lean ground turkey",
            "turkey 93/7",
        ],
        "calories_100g": 203.0,
        "protein_100g": 27.0,
        "carbs_100g": 0.0,
        "fats_100g": 10.5,
        "fiber_100g": 0.0,
    },
]


# ==================================================
# FOOD HELPERS
# ==================================================

def format_food(
    name,
    source,
    calories,
    protein,
    carbs,
    fats,
    fiber,
):
    return {
        "name": name,
        "source": source,
        "calories_100g": round(float(calories or 0), 1),
        "protein_100g": round(float(protein or 0), 1),
        "carbs_100g": round(float(carbs or 0), 1),
        "fats_100g": round(float(fats or 0), 1),
        "fiber_100g": round(float(fiber or 0), 1),
    }


def has_nutrition(calories, protein):
    return (
        float(calories or 0) > 0
        or float(protein or 0) > 0
    )


def search_common_foods(query):
    results = []

    for food in COMMON_FOODS:
        name_match = query in food["name"].lower()

        keyword_match = any(
            query in keyword.lower()
            for keyword in food["keywords"]
        )

        if name_match or keyword_match:
            results.append({
                "name": food["name"],
                "source": "Local",
                "calories_100g": food["calories_100g"],
                "protein_100g": food["protein_100g"],
                "carbs_100g": food["carbs_100g"],
                "fats_100g": food["fats_100g"],
                "fiber_100g": food["fiber_100g"],
            })

    return results


# ==================================================
# USDA
# ==================================================

def search_usda_api(query, limit=8):
    if not USDA_API_KEY:
        return []

    url = (
        "https://api.nal.usda.gov/"
        "fdc/v1/foods/search"
    )

    payload = {
        "query": query,
        "pageSize": limit,
        "dataType": [
            "Branded",
            "Survey (FNDDS)",
            "Foundation",
        ],
    }

    try:
        response = requests.post(
            url,
            params={"api_key": USDA_API_KEY},
            json=payload,
            timeout=4,
        )

        response.raise_for_status()

        foods = response.json().get(
            "foods",
            [],
        )

    except requests.RequestException as error:
        print(f"USDA Search Error: {error}")
        return []

    results = []

    for food in foods:
        name = food.get(
            "description",
            "Unknown Food",
        )

        brand = food.get(
            "brandOwner",
            "",
        )

        if brand:
            name = f"{brand} - {name}"

        nutrients = {
            nutrient.get("nutrientName", "").lower():
            nutrient.get("value", 0)
            for nutrient in food.get(
                "foodNutrients",
                [],
            )
        }

        calories = (
            nutrients.get("energy")
            or nutrients.get("energy (kcal)")
            or 0
        )

        protein = nutrients.get(
            "protein",
            0,
        )

        carbs = nutrients.get(
            "carbohydrate, by difference",
            0,
        )

        fats = nutrients.get(
            "total lipid (fat)",
            0,
        )

        fiber = nutrients.get(
            "fiber, total dietary",
            0,
        )

        if not has_nutrition(
            calories,
            protein,
        ):
            continue

        results.append(
            format_food(
                name.title(),
                "USDA",
                calories,
                protein,
                carbs,
                fats,
                fiber,
            )
        )

    return results


# ==================================================
# OPEN FOOD FACTS
# ==================================================

def search_openfoodfacts_api(
    query,
    limit=8,
):
    query = re.sub(
        r"[_,-]",
        " ",
        query,
    ).strip()

    url = (
        "https://world.openfoodfacts.org/"
        "cgi/search.pl"
    )

    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": limit,
        "lc": "en",
    }

    headers = {
        "User-Agent": "MyFitnessApp/1.0",
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=4,
        )

        response.raise_for_status()

        products = response.json().get(
            "products",
            [],
        )

    except requests.RequestException as error:
        print(
            f"OpenFoodFacts Search Error: {error}"
        )
        return []

    results = []

    for product in products:
        name = (
            product.get("product_name_en")
            or product.get("product_name")
        )

        if not name:
            continue

        brand = product.get(
            "brands",
            "",
        )

        full_name = (
            f"{brand} - {name}"
            if brand
            else name
        )

        nutrients = product.get(
            "nutriments",
            {},
        )

        calories = (
            nutrients.get(
                "energy-kcal_100g"
            )
            or nutrients.get(
                "energy-kcal"
            )
            or 0
        )

        protein = (
            nutrients.get(
                "proteins_100g"
            )
            or nutrients.get(
                "proteins"
            )
            or 0
        )

        carbs = (
            nutrients.get(
                "carbohydrates_100g"
            )
            or nutrients.get(
                "carbohydrates"
            )
            or 0
        )

        fats = (
            nutrients.get(
                "fat_100g"
            )
            or nutrients.get("fat")
            or 0
        )

        fiber = (
            nutrients.get(
                "fiber_100g"
            )
            or nutrients.get("fiber")
            or 0
        )

        if not has_nutrition(
            calories,
            protein,
        ):
            continue

        results.append(
            format_food(
                full_name.title(),
                "OpenFoodFacts",
                calories,
                protein,
                carbs,
                fats,
                fiber,
            )
        )

    return results


# ==================================================
# FOOD SEARCH
# ==================================================

def search_food(query):
    query = query.strip().lower()

    # Local foods are instant.
    results = search_common_foods(query)

    if results:
        return results

    # USDA first.
    results = search_usda_api(query)

    if results:
        return results

    # OpenFoodFacts fallback.
    return search_openfoodfacts_api(query)


# ==================================================
# MAIN PAGES
# ==================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route(
    "/register",
    methods=["GET", "POST"],
)
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(
                form.password.data,
                method="pbkdf2:sha256",
            ),
        )

        db.session.add(user)
        db.session.commit()

        flash(
            "Account created successfully! "
            "You can now log in.",
            "success",
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html",
        form=form,
    )


@app.route(
    "/login",
    methods=["GET", "POST"],
)
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(
            email=form.email.data
        ).first()

        if user and check_password_hash(
            user.password_hash,
            form.password.data,
        ):
            login_user(
                user,
                remember=True,
            )

            flash(
                "You are logged in!",
                "success",
            )

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid email or password",
            "danger",
        )

    return render_template(
        "login.html",
        form=form,
    )


@app.route("/logout")
@login_required
def logout():
    logout_user()

    flash(
        "You have been logged out.",
        "info",
    )

    return redirect(
        url_for("login")
    )


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template(
        "dashboard.html"
    )


# ==================================================
# GOALS
# ==================================================

@app.route(
    "/goals",
    methods=["GET", "POST"],
)
@login_required
def goals():
    form = GoalForm()

    if form.validate_on_submit():
        current_user.daily_calorie_goal = (
            form.daily_calorie_goal.data
        )

        current_user.daily_protein_goal = (
            form.daily_protein_goal.data
        )

        current_user.daily_carbs_goal = (
            form.daily_carbs_goal.data
        )

        current_user.daily_fat_goal = (
            form.daily_fat_goal.data
        )

        db.session.commit()

        flash(
            "Your goals have been updated!",
            "success",
        )

        return redirect(
            url_for("dashboard")
        )

    if request.method == "GET":
        form.daily_calorie_goal.data = (
            current_user.daily_calorie_goal
        )

        form.daily_protein_goal.data = (
            current_user.daily_protein_goal
        )

        form.daily_carbs_goal.data = (
            current_user.daily_carbs_goal
        )

        form.daily_fat_goal.data = (
            current_user.daily_fat_goal
        )

    return render_template(
        "goals.html",
        form=form,
    )


# ==================================================
# TRACKER
# ==================================================

@app.route(
    "/tracker",
    methods=["GET", "POST"],
)
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
                grams=float(
                    form.grams.data
                ),
                calories=float(
                    form.calories.data
                ),
                protein=float(
                    form.protein.data
                ),
                carbs=float(
                    form.carbs.data
                ),
                fats=float(
                    form.fats.data
                ),
                fiber=float(
                    form.fiber.data or 0
                ),
                notes=form.notes.data or "",
            )

            db.session.add(log_entry)
            db.session.commit()

            flash(
                "Meal logged successfully!",
                "success",
            )

            return redirect(
                url_for("journal")
            )

        except Exception as error:
            db.session.rollback()

            print(
                f"Database Save Error: {error}"
            )

            flash(
                "Something went wrong while "
                "saving your meal.",
                "danger",
            )

    return render_template(
        "tracker.html",
        form=form,
    )


# ==================================================
# JOURNAL
# ==================================================

@app.route("/journal")
@login_required
def journal():
    logs = (
        FoodLog.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            FoodLog.id.desc()
        )
        .all()
    )

    grouped_journal = defaultdict(
        lambda: {
            "entries": [],
            "total_calories": 0,
            "total_protein": 0,
            "total_carbs": 0,
            "total_fats": 0,
            "total_fiber": 0,
        }
    )

    for log in logs:
        day = log.date or date.today()
        day_key = day.strftime(
            "%Y-%m-%d"
        )

        journal_day = (
            grouped_journal[day_key]
        )

        journal_day["entries"].append(
            log
        )

        journal_day["total_calories"] += (
            log.calories or 0
        )

        journal_day["total_protein"] += (
            log.protein or 0
        )

        journal_day["total_carbs"] += (
            log.carbs or 0
        )

        journal_day["total_fats"] += (
            log.fats or 0
        )

        journal_day["total_fiber"] += (
            log.fiber or 0
        )

    nutrients = (
        "total_calories",
        "total_protein",
        "total_carbs",
        "total_fats",
        "total_fiber",
    )

    for data in grouped_journal.values():
        for nutrient in nutrients:
            data[nutrient] = round(
                data[nutrient],
                1,
            )

    return render_template(
        "journal.html",
        journal=dict(grouped_journal),
    )


@app.route(
    "/delete-log/<int:log_id>",
    methods=["POST"],
)
@login_required
def delete_log(log_id):
    log = db.session.get(
        FoodLog,
        log_id,
    )

    if log and log.user_id == current_user.id:
        db.session.delete(log)
        db.session.commit()

        flash(
            "Meal entry deleted.",
            "info",
        )

    return redirect(
        url_for("journal")
    )


# ==================================================
# FOOD SEARCH API
# ==================================================

@app.route("/api/search-food")
@login_required
def api_search_food():
    query = request.args.get(
        "q",
        "",
    ).strip()

    if len(query) < 2:
        return jsonify([])

    return jsonify(
        search_food(query)
    )


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":
    app.run(debug=False)
