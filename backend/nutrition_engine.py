"""
NutriVision AI — Nutrition Engine
Calculates nutritional amounts, serving conversions, and meal totals
based on verified nutrient values per 100g.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from backend.database import get_food_by_name, get_serving_units


@dataclass
class MealItemNutrition:
    food_name: str
    display_name: str
    quantity: float
    unit: str
    weight_g: float
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fibre_g: float
    category: str
    source: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "food_name": self.food_name,
            "display_name": self.display_name,
            "quantity": self.quantity,
            "unit": self.unit,
            "weight_g": round(self.weight_g, 1),
            "calories": round(self.calories, 1),
            "protein_g": round(self.protein_g, 1),
            "carbs_g": round(self.carbs_g, 1),
            "fat_g": round(self.fat_g, 1),
            "fibre_g": round(self.fibre_g, 1),
            "category": self.category,
            "source": self.source
        }


@dataclass
class MealTotalNutrition:
    total_weight_g: float
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    total_fibre_g: float
    macro_percentages: Dict[str, float]  # % of calories from protein, carbs, fat
    items: List[MealItemNutrition] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_weight_g": round(self.total_weight_g, 1),
            "total_calories": round(self.total_calories, 1),
            "total_protein_g": round(self.total_protein_g, 1),
            "total_carbs_g": round(self.carbs_g, 1) if hasattr(self, "carbs_g") else round(self.total_carbs_g, 1),
            "total_fat_g": round(self.total_fat_g, 1),
            "total_fibre_g": round(self.total_fibre_g, 1),
            "macro_percentages": self.macro_percentages,
            "items": [item.to_dict() for item in self.items]
        }


def calculate_food_nutrition(
    food_name: str,
    quantity: float,
    unit: str = "g",
    custom_weight_g: Optional[float] = None
) -> Optional[MealItemNutrition]:
    """
    Calculate nutrient amounts for a given food and quantity.
    Formula: Nutrient amount = (Quantity in grams / 100) * Nutrient value per 100g
    """
    food = get_food_by_name(food_name)
    if not food:
        return None

    # Calculate actual gram weight
    if custom_weight_g is not None and custom_weight_g > 0:
        actual_weight_g = float(custom_weight_g)
    elif unit.lower() in ["g", "gram", "grams"]:
        actual_weight_g = float(quantity)
    else:
        # Look up conversion for unit
        units = get_serving_units(food_name)
        unit_map = {u["unit_name"].lower(): u["gram_weight"] for u in units}
        gram_multiplier = unit_map.get(unit.lower(), food["default_serving_weight_g"])
        actual_weight_g = float(quantity) * gram_multiplier

    # Scaling factor
    factor = actual_weight_g / 100.0

    calories = factor * food["calories_per_100g"]
    protein = factor * food["protein_per_100g"]
    carbs = factor * food["carbs_per_100g"]
    fat = factor * food["fat_per_100g"]
    fibre = factor * food["fibre_per_100g"]

    return MealItemNutrition(
        food_name=food["food_name"],
        display_name=food["display_name"],
        quantity=quantity,
        unit=unit,
        weight_g=actual_weight_g,
        calories=calories,
        protein_g=protein,
        carbs_g=carbs,
        fat_g=fat,
        fibre_g=fibre,
        category=food["category"],
        source=food["source"]
    )


def calculate_meal_totals(item_inputs: List[Dict[str, Any]]) -> MealTotalNutrition:
    """
    Aggregate nutrition across multiple meal items.
    Each item input: {"food_name": str, "quantity": float, "unit": str, "custom_weight_g": Optional[float]}
    """
    items: List[MealItemNutrition] = []
    tot_weight = 0.0
    tot_cal = 0.0
    tot_prot = 0.0
    tot_carbs = 0.0
    tot_fat = 0.0
    tot_fibre = 0.0

    for inp in item_inputs:
        item = calculate_food_nutrition(
            food_name=inp["food_name"],
            quantity=inp.get("quantity", 1.0),
            unit=inp.get("unit", "g"),
            custom_weight_g=inp.get("custom_weight_g")
        )
        if item:
            items.append(item)
            tot_weight += item.weight_g
            tot_cal += item.calories
            tot_prot += item.protein_g
            tot_carbs += item.carbs_g
            tot_fat += item.fat_g
            tot_fibre += item.fibre_g

    # Macronutrient caloric distribution:
    # Protein: 4 kcal/g, Carbs: 4 kcal/g, Fat: 9 kcal/g
    cal_from_prot = tot_prot * 4.0
    cal_from_carbs = tot_carbs * 4.0
    cal_from_fat = tot_fat * 9.0
    sum_macro_cal = cal_from_prot + cal_from_carbs + cal_from_fat

    if sum_macro_cal > 0:
        macro_percentages = {
            "protein_pct": round((cal_from_prot / sum_macro_cal) * 100.0, 1),
            "carbs_pct": round((cal_from_carbs / sum_macro_cal) * 100.0, 1),
            "fat_pct": round((cal_from_fat / sum_macro_cal) * 100.0, 1)
        }
    else:
        macro_percentages = {"protein_pct": 0.0, "carbs_pct": 0.0, "fat_pct": 0.0}

    return MealTotalNutrition(
        total_weight_g=tot_weight,
        total_calories=tot_cal,
        total_protein_g=tot_prot,
        total_carbs_g=tot_carbs,
        total_fat_g=tot_fat,
        total_fibre_g=tot_fibre,
        macro_percentages=macro_percentages,
        items=items
    )
