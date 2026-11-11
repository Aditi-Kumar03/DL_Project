"""
NutriVision AI — Meal Service Module
Coordinates database logging of meals, calculates daily summaries,
tracks calorie deficits and surpluses, and maintains user health profiles.
"""

from datetime import datetime, date
from typing import List, Dict, Optional, Any
from backend.database import get_db_connection, DB_PATH
from backend.nutrition_engine import calculate_food_nutrition


class MealService:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def log_meal_items(
        self,
        meal_type: str,
        items: List[Dict[str, Any]],
        meal_date: Optional[str] = None,
        image_path: Optional[str] = None
    ) -> List[int]:
        """
        Log multiple food items for a specific meal (Breakfast, Lunch, Dinner, Snack).
        Each item: {"food_name": str, "quantity": float, "unit": str, "custom_weight_g": Optional[float]}
        """
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()

        date_str = meal_date or date.today().isoformat()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry_ids = []

        for it in items:
            food_name = it["food_name"]
            quantity = float(it.get("quantity", 1.0))
            unit = it.get("unit", "g")
            custom_weight = it.get("custom_weight_g")

            nutr = calculate_food_nutrition(food_name, quantity, unit, custom_weight)
            if not nutr:
                continue

            cursor.execute("""
            INSERT INTO meal_entries (
                date, timestamp, meal_type, food_name, quantity,
                unit, weight_g, calories, protein, carbs, fat, fibre, source_image_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                date_str,
                now_str,
                meal_type,
                nutr.display_name,
                quantity,
                unit,
                nutr.weight_g,
                nutr.calories,
                nutr.protein_g,
                nutr.carbs_g,
                nutr.fat_g,
                nutr.fibre_g,
                image_path
            ))
            entry_ids.append(cursor.lastrowid)

        conn.commit()
        conn.close()
        return entry_ids

    def add_meal_entry(
        self,
        meal_type: str,
        food_name: str,
        quantity: float,
        unit: str,
        weight_g: float,
        calories: float,
        protein: float,
        carbs: float,
        fat: float,
        fibre: float,
        meal_date: Optional[str] = None,
        image_path: Optional[str] = None
    ) -> int:
        """Log a single pre-calculated meal entry directly into the database."""
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()

        date_str = meal_date or date.today().isoformat()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
        INSERT INTO meal_entries (
            date, timestamp, meal_type, food_name, quantity,
            unit, weight_g, calories, protein, carbs, fat, fibre, source_image_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            date_str,
            now_str,
            meal_type,
            food_name,
            float(quantity),
            unit,
            float(weight_g),
            float(calories),
            float(protein),
            float(carbs),
            float(fat),
            float(fibre),
            image_path
        ))
        entry_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return entry_id

    def get_daily_summary(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve total consumed calories, macros, and meal breakdown for a given day.
        """
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()

        date_str = target_date or date.today().isoformat()

        cursor.execute("""
        SELECT 
            COUNT(*) as total_items,
            COALESCE(SUM(calories), 0.0) as total_calories,
            COALESCE(SUM(protein), 0.0) as total_protein,
            COALESCE(SUM(carbs), 0.0) as total_carbs,
            COALESCE(SUM(fat), 0.0) as total_fat,
            COALESCE(SUM(fibre), 0.0) as total_fibre
        FROM meal_entries
        WHERE date = ?
        """, (date_str,))
        totals_row = cursor.fetchone()

        # Breakdown by meal type
        cursor.execute("""
        SELECT 
            meal_type,
            COUNT(*) as item_count,
            COALESCE(SUM(calories), 0.0) as meal_calories,
            COALESCE(SUM(protein), 0.0) as meal_protein,
            COALESCE(SUM(carbs), 0.0) as meal_carbs,
            COALESCE(SUM(fat), 0.0) as meal_fat
        FROM meal_entries
        WHERE date = ?
        GROUP BY meal_type
        """, (date_str,))
        meal_rows = cursor.fetchall()

        # Fetch all individual items logged today
        cursor.execute("""
        SELECT * FROM meal_entries WHERE date = ? ORDER BY timestamp DESC
        """, (date_str,))
        item_rows = cursor.fetchall()

        conn.close()

        meal_breakdown = {
            r["meal_type"]: {
                "items": r["item_count"],
                "calories": round(r["meal_calories"], 1),
                "protein": round(r["meal_protein"], 1),
                "carbs": round(r["meal_carbs"], 1),
                "fat": round(r["meal_fat"], 1)
            }
            for r in meal_rows
        }

        # User profile target
        profile = self.get_user_profile()
        target_cal = profile.get("target_calories", 2000.0) if profile else 2000.0
        tot_cal = round(totals_row["total_calories"], 1)
        calorie_balance = round(tot_cal - target_cal, 1)

        return {
            "date": date_str,
            "total_items": totals_row["total_items"],
            "total_calories": tot_cal,
            "total_protein": round(totals_row["total_protein"], 1),
            "total_carbs": round(totals_row["total_carbs"], 1),
            "total_fat": round(totals_row["total_fat"], 1),
            "total_fibre": round(totals_row["total_fibre"], 1),
            "target_calories": target_cal,
            "calorie_balance": calorie_balance,
            "status": "surplus" if calorie_balance > 0 else "deficit",
            "meal_breakdown": meal_breakdown,
            "entries": [dict(r) for r in item_rows]
        }

    def get_meal_history(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve historical logged meals with optional date filtering."""
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM meal_entries WHERE 1=1"
        params = []

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def delete_meal_entry(self, entry_id: int) -> bool:
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM meal_entries WHERE id = ?", (entry_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    def save_user_profile(self, profile_data: Dict[str, Any]) -> int:
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()

        # Check if profile exists
        cursor.execute("SELECT id FROM user_profiles LIMIT 1")
        existing = cursor.fetchone()

        if existing:
            profile_id = existing[0]
            cursor.execute("""
            UPDATE user_profiles SET
                name = ?, age = ?, sex = ?, height_cm = ?, weight_kg = ?,
                activity_level = ?, goal = ?, target_calories = ?,
                target_protein_g = ?, target_carbs_g = ?, target_fat_g = ?,
                bmi = ?, bmr = ?, tdee = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """, (
                profile_data.get("name", "User"),
                profile_data["age"],
                profile_data["sex"],
                profile_data["height_cm"],
                profile_data["weight_kg"],
                profile_data["activity_level"],
                profile_data.get("goal", "maintain"),
                profile_data.get("target_calories", 2000.0),
                profile_data.get("target_protein_g", 75.0),
                profile_data.get("target_carbs_g", 250.0),
                profile_data.get("target_fat_g", 55.0),
                profile_data.get("bmi"),
                profile_data.get("bmr"),
                profile_data.get("tdee"),
                profile_id
            ))
        else:
            cursor.execute("""
            INSERT INTO user_profiles (
                name, age, sex, height_cm, weight_kg, activity_level, goal,
                target_calories, target_protein_g, target_carbs_g, target_fat_g,
                bmi, bmr, tdee
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                profile_data.get("name", "User"),
                profile_data["age"],
                profile_data["sex"],
                profile_data["height_cm"],
                profile_data["weight_kg"],
                profile_data["activity_level"],
                profile_data.get("goal", "maintain"),
                profile_data.get("target_calories", 2000.0),
                profile_data.get("target_protein_g", 75.0),
                profile_data.get("target_carbs_g", 250.0),
                profile_data.get("target_fat_g", 55.0),
                profile_data.get("bmi"),
                profile_data.get("bmr"),
                profile_data.get("tdee")
            ))
            profile_id = cursor.lastrowid

        conn.commit()
        conn.close()
        return profile_id

    def get_user_profile(self) -> Optional[Dict[str, Any]]:
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_profiles ORDER BY updated_at DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
