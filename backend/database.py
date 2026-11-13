"""
NutriLens AI — SQLite Database Module
Manages food nutrition data (IFCT 2017 / ICMR-NIN verified), serving units,
user health profiles, and meal history logs.
"""

import os
import sqlite3
from typing import List, Dict, Optional, Any


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "nutrition.db")


def get_db_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Create and return a thread-safe connection with dict-like row access."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_PATH) -> None:
    """Initialize database tables and seed verified Indian food nutrition data."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # 1. Foods Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS foods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        food_name TEXT UNIQUE NOT NULL,
        display_name TEXT NOT NULL,
        calories_per_100g REAL NOT NULL,
        protein_per_100g REAL NOT NULL,
        carbs_per_100g REAL NOT NULL,
        fat_per_100g REAL NOT NULL,
        fibre_per_100g REAL NOT NULL,
        category TEXT NOT NULL,
        preparation_state TEXT NOT NULL DEFAULT 'cooked',
        default_serving_unit TEXT NOT NULL DEFAULT 'bowl',
        default_serving_weight_g REAL NOT NULL DEFAULT 150.0,
        source TEXT NOT NULL DEFAULT 'IFCT 2017 (ICMR-NIN)'
    )
    """)

    # 2. Serving Units Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS serving_units (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        food_name TEXT NOT NULL,
        unit_name TEXT NOT NULL,
        gram_weight REAL NOT NULL,
        description TEXT,
        FOREIGN KEY (food_name) REFERENCES foods(food_name),
        UNIQUE(food_name, unit_name)
    )
    """)

    # 3. User Health Profile Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT DEFAULT 'User',
        age INTEGER NOT NULL,
        sex TEXT NOT NULL,
        height_cm REAL NOT NULL,
        weight_kg REAL NOT NULL,
        activity_level TEXT NOT NULL,
        goal TEXT NOT NULL DEFAULT 'maintain',
        target_calories REAL,
        target_protein_g REAL,
        target_carbs_g REAL,
        target_fat_g REAL,
        bmi REAL,
        bmr REAL,
        tdee REAL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 4. Meal Entries Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meal_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        meal_type TEXT NOT NULL,
        food_name TEXT NOT NULL,
        quantity REAL NOT NULL,
        unit TEXT NOT NULL,
        weight_g REAL NOT NULL,
        calories REAL NOT NULL,
        protein REAL NOT NULL,
        carbs REAL NOT NULL,
        fat REAL NOT NULL,
        fibre REAL NOT NULL,
        source_image_path TEXT
    )
    """)

    conn.commit()

    # Seed verified 43 Indian Food categories if empty
    cursor.execute("SELECT COUNT(*) FROM foods")
    if cursor.fetchone()[0] == 0:
        _seed_verified_indian_foods(conn)

    conn.close()


def _seed_verified_indian_foods(conn: sqlite3.Connection) -> None:
    """
    Seed initial 43 Indian foods with verified nutritional data
    from IFCT 2017 (Indian Food Composition Tables, ICMR-NIN).
    Strictly differentiates cooked dishes from raw ingredients.
    """
    cursor = conn.cursor()

    # 43 Verified Indian Foods (Values per 100g prepared/cooked dish)
    foods_data = [
        ("aloo_gobi", "Aloo Gobi", 110.0, 2.5, 14.2, 5.0, 2.8, "Curry / Sabji", "cooked", "bowl", 150.0),
        ("aloo_masala", "Aloo Masala", 135.0, 2.1, 19.5, 5.5, 2.4, "Curry / Sabji", "cooked", "bowl", 150.0),
        ("bhindi_masala", "Bhindi Masala", 105.0, 2.3, 11.2, 6.0, 3.6, "Curry / Sabji", "cooked", "bowl", 150.0),
        ("biryani", "Chicken / Mutton Biryani", 195.0, 7.8, 26.5, 6.8, 1.8, "Rice / Grains", "cooked", "plate", 250.0),
        ("burger", "Veg / Chicken Burger", 260.0, 11.0, 30.0, 10.5, 2.2, "Snacks", "cooked", "piece", 180.0),
        ("butter_naan", "Butter Naan", 310.0, 8.5, 52.0, 8.0, 2.5, "Breads", "cooked", "piece", 90.0),
        ("chai", "Masala Chai (with Milk & Sugar)", 75.0, 2.1, 10.5, 2.8, 0.0, "Beverages", "cooked", "cup", 150.0),
        ("chapati", "Chapati / Phulka", 295.0, 9.5, 55.0, 3.5, 9.8, "Breads", "cooked", "roti", 40.0),
        ("chicken_curry", "Indian Chicken Curry", 175.0, 16.5, 5.2, 10.0, 1.2, "Curry / Non-Veg", "cooked", "bowl", 180.0),
        ("chole", "Chole (Chickpea Curry)", 165.0, 7.2, 21.0, 5.8, 6.2, "Curry / Dal", "cooked", "bowl", 150.0),
        ("chole_bhature", "Chole Bhature", 285.0, 6.5, 38.0, 12.5, 4.0, "Meal / Snack", "cooked", "plate", 300.0),
        ("coconut_chutney", "Coconut Chutney", 210.0, 2.8, 8.5, 19.0, 4.2, "Condiments", "cooked", "tbsp", 25.0),
        ("dal_makhani", "Dal Makhani", 145.0, 5.2, 16.0, 7.0, 4.5, "Curry / Dal", "cooked", "bowl", 150.0),
        ("dhokla", "Khaman Dhokla", 160.0, 6.8, 28.0, 2.5, 3.0, "Snacks", "cooked", "piece", 45.0),
        ("dum_aloo", "Dum Aloo", 140.0, 2.4, 18.0, 6.5, 2.2, "Curry / Sabji", "cooked", "bowl", 150.0),
        ("fish_curry", "Fish Curry", 140.0, 15.0, 3.5, 7.2, 0.8, "Curry / Non-Veg", "cooked", "bowl", 180.0),
        ("fried_rice", "Vegetable Fried Rice", 170.0, 3.8, 29.5, 4.2, 1.5, "Rice / Grains", "cooked", "plate", 200.0),
        ("ghevar", "Ghevar (Sweet)", 430.0, 5.2, 58.0, 20.5, 0.8, "Sweets / Desserts", "cooked", "piece", 80.0),
        ("green_chutney", "Mint / Coriander Chutney", 60.0, 2.5, 8.0, 1.8, 3.8, "Condiments", "cooked", "tbsp", 15.0),
        ("gulab_jamun", "Gulab Jamun", 325.0, 4.5, 56.0, 9.5, 0.5, "Sweets / Desserts", "cooked", "piece", 50.0),
        ("idli", "Steamed Idli", 135.0, 4.2, 28.0, 0.6, 1.8, "Breakfast / Snacks", "cooked", "piece", 50.0),
        ("jalebi", "Jalebi", 380.0, 2.2, 76.0, 7.5, 0.4, "Sweets / Desserts", "cooked", "piece", 30.0),
        ("kaathi_rolls", "Kathi Roll (Paneer/Chicken)", 230.0, 9.5, 28.0, 9.0, 2.5, "Snacks", "cooked", "piece", 160.0),
        ("kadai_paneer", "Kadai Paneer", 185.0, 8.5, 8.0, 13.5, 2.4, "Curry / Sabji", "cooked", "bowl", 160.0),
        ("kebab", "Seekh / Shami Kebab", 210.0, 18.0, 6.0, 12.5, 1.5, "Snacks / Non-Veg", "cooked", "piece", 45.0),
        ("kheer", "Rice Kheer", 155.0, 4.0, 24.5, 4.5, 0.5, "Sweets / Desserts", "cooked", "bowl", 150.0),
        ("kulfi", "Malai Kulfi", 220.0, 5.5, 25.0, 11.0, 0.2, "Sweets / Desserts", "cooked", "piece", 80.0),
        ("lassi", "Sweet Lassi", 95.0, 3.2, 14.0, 2.8, 0.0, "Beverages", "cooked", "glass", 250.0),
        ("masala_dosa", "Masala Dosa (with Potato)", 210.0, 4.5, 33.0, 7.0, 2.8, "Breakfast / Meal", "cooked", "piece", 180.0),
        ("modak", "Ukadiche Modak", 260.0, 3.8, 48.0, 6.2, 2.0, "Sweets / Desserts", "cooked", "piece", 45.0),
        ("momos", "Steamed Momos", 180.0, 7.0, 28.5, 4.2, 1.6, "Snacks", "cooked", "piece", 30.0),
        ("mutton_curry", "Mutton Rogan Josh / Curry", 220.0, 18.5, 4.0, 14.5, 1.0, "Curry / Non-Veg", "cooked", "bowl", 180.0),
        ("paani_puri", "Pani Puri / Golgappa", 190.0, 3.5, 32.0, 5.5, 2.2, "Snacks / Chaat", "cooked", "piece", 25.0),
        ("pakode", "Vegetable Pakoda", 280.0, 6.5, 32.0, 14.5, 4.2, "Snacks", "cooked", "piece", 25.0),
        ("palak_paneer", "Palak Paneer", 160.0, 8.2, 6.5, 11.5, 3.2, "Curry / Sabji", "cooked", "bowl", 160.0),
        ("pav_bhaji", "Pav Bhaji (Bhaji only)", 165.0, 4.2, 24.5, 5.8, 3.5, "Meal / Snack", "cooked", "bowl", 150.0),
        ("pizza", "Vegetable / Cheese Pizza", 265.0, 11.5, 32.0, 10.2, 2.4, "Fast Food", "cooked", "piece", 100.0),
        ("poha", "Kanda Poha", 160.0, 3.2, 28.5, 3.8, 2.4, "Breakfast / Snacks", "cooked", "bowl", 150.0),
        ("rajma_curry", "Rajma Masala (Kidney Beans)", 135.0, 5.8, 18.5, 4.2, 5.2, "Curry / Dal", "cooked", "bowl", 160.0),
        ("ras_malai", "Rasmalai", 215.0, 6.8, 27.0, 9.0, 0.4, "Sweets / Desserts", "cooked", "piece", 60.0),
        ("samosa", "Aloo Samosa", 290.0, 5.2, 35.0, 14.5, 3.0, "Snacks", "cooked", "piece", 80.0),
        ("shahi_paneer", "Shahi Paneer", 215.0, 8.8, 9.5, 16.0, 2.0, "Curry / Sabji", "cooked", "bowl", 160.0),
        ("white_rice", "Cooked White Rice (Basmati)", 130.0, 2.7, 28.0, 0.3, 0.4, "Rice / Grains", "cooked", "bowl", 150.0)
    ]

    cursor.executemany("""
    INSERT INTO foods (
        food_name, display_name, calories_per_100g, protein_per_100g,
        carbs_per_100g, fat_per_100g, fibre_per_100g, category,
        preparation_state, default_serving_unit, default_serving_weight_g
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, foods_data)

    # Seed common serving units
    serving_units_data = []
    for food in foods_data:
        fname = food[0]
        def_unit = food[9]
        def_wt = food[10]

        # Standard grams
        serving_units_data.append((fname, "g", 1.0, "Exact weight in grams"))
        
        # Primary common unit
        serving_units_data.append((fname, def_unit, def_wt, f"Standard 1 {def_unit} (~{int(def_wt)}g)"))

        # Additional conversions
        if def_unit == "bowl":
            serving_units_data.append((fname, "cup", 200.0, "1 Standard measuring cup (~200g)"))
            serving_units_data.append((fname, "katori", 150.0, "1 Standard Indian katori (~150g)"))
            serving_units_data.append((fname, "small_katori", 100.0, "1 Small katori (~100g)"))
        elif def_unit == "roti":
            serving_units_data.append((fname, "piece", 40.0, "1 standard roti (~40g)"))
            serving_units_data.append((fname, "large_roti", 60.0, "1 large roti (~60g)"))
        elif def_unit == "plate":
            serving_units_data.append((fname, "half_plate", def_wt * 0.5, f"Half plate (~{int(def_wt*0.5)}g)"))
            serving_units_data.append((fname, "cup", 180.0, "1 measuring cup (~180g)"))
        elif def_unit == "piece":
            serving_units_data.append((fname, "plate", def_wt * 2.0, f"Serving of 2 pieces (~{int(def_wt*2)}g)"))

    cursor.executemany("""
    INSERT OR IGNORE INTO serving_units (food_name, unit_name, gram_weight, description)
    VALUES (?, ?, ?, ?)
    """, serving_units_data)

    conn.commit()


# Database Access Functions
def get_food_by_name(food_name: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM foods WHERE food_name = ? OR LOWER(display_name) = LOWER(?)", (food_name, food_name))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_foods(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM foods ORDER BY category, display_name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_serving_units(food_name: str, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT unit_name, gram_weight, description FROM serving_units WHERE food_name = ?", (food_name,))
    rows = cursor.fetchall()
    conn.close()
    units = [dict(r) for r in rows]
    if not any(u["unit_name"] == "g" for u in units):
        units.insert(0, {"unit_name": "g", "gram_weight": 1.0, "description": "Grams"})
    return units


def update_or_add_food(food_data: Dict[str, Any], db_path: str = DB_PATH) -> bool:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO foods (
        food_name, display_name, calories_per_100g, protein_per_100g,
        carbs_per_100g, fat_per_100g, fibre_per_100g, category,
        preparation_state, default_serving_unit, default_serving_weight_g, source
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(food_name) DO UPDATE SET
        display_name = excluded.display_name,
        calories_per_100g = excluded.calories_per_100g,
        protein_per_100g = excluded.protein_per_100g,
        carbs_per_100g = excluded.carbs_per_100g,
        fat_per_100g = excluded.fat_per_100g,
        fibre_per_100g = excluded.fibre_per_100g,
        category = excluded.category,
        preparation_state = excluded.preparation_state,
        default_serving_unit = excluded.default_serving_unit,
        default_serving_weight_g = excluded.default_serving_weight_g,
        source = excluded.source
    """, (
        food_data["food_name"],
        food_data["display_name"],
        food_data["calories_per_100g"],
        food_data["protein_per_100g"],
        food_data["carbs_per_100g"],
        food_data["fat_per_100g"],
        food_data["fibre_per_100g"],
        food_data.get("category", "Other"),
        food_data.get("preparation_state", "cooked"),
        food_data.get("default_serving_unit", "g"),
        food_data.get("default_serving_weight_g", 100.0),
        food_data.get("source", "User Input")
    ))
    conn.commit()
    conn.close()
    return True
