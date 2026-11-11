"""
NutriVision AI — Health Calculation Module
Calculates BMI, BMR (Mifflin-St Jeor), TDEE, and daily caloric targets.
Important Notice: These values are mathematical estimates for nutritional planning,
not medical diagnoses or clinical prescriptions.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


ACTIVITY_FACTORS: Dict[str, float] = {
    "sedentary": 1.2,        # Little or no exercise, desk job
    "light": 1.375,          # Light exercise 1-3 days/week
    "moderate": 1.55,        # Moderate exercise 3-5 days/week
    "very_active": 1.725,    # Hard exercise 6-7 days/week
    "extra_active": 1.9      # Very hard exercise, physical job or training twice a day
}

ACTIVITY_DESCRIPTIONS: Dict[str, str] = {
    "sedentary": "Sedentary (little to no exercise + desk work)",
    "light": "Lightly Active (light exercise 1–3 days/week)",
    "moderate": "Moderately Active (exercise 3–5 days/week)",
    "very_active": "Very Active (intense exercise 6–7 days/week)",
    "extra_active": "Extra Active (hard physical labor or athletic training 2x/day)"
}


@dataclass
class HealthProfileResult:
    age: int
    sex: str
    height_cm: float
    weight_kg: float
    activity_level: str
    goal: str
    bmi: float
    bmi_category: str
    bmi_description: str
    bmr: float
    tdee: float
    target_calories: float
    target_protein_g: float
    target_carbs_g: float
    target_fat_g: float
    disclaimer: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "age": self.age,
            "sex": self.sex,
            "height_cm": self.height_cm,
            "weight_kg": self.weight_kg,
            "activity_level": self.activity_level,
            "goal": self.goal,
            "bmi": round(self.bmi, 2),
            "bmi_category": self.bmi_category,
            "bmi_description": self.bmi_description,
            "bmr": round(self.bmr, 1),
            "tdee": round(self.tdee, 1),
            "target_calories": round(self.target_calories, 1),
            "target_protein_g": round(self.target_protein_g, 1),
            "target_carbs_g": round(self.target_carbs_g, 1),
            "target_fat_g": round(self.target_fat_g, 1),
            "disclaimer": self.disclaimer
        }


def calculate_bmi(weight_kg: float, height_cm: float) -> tuple[float, str, str]:
    """
    Calculate Body Mass Index (BMI).
    Formula: BMI = weight (kg) / (height (m))^2
    Includes Asian-Indian specific cardiovascular risk thresholds (ICMR / WHO guidelines).
    """
    if height_cm <= 0 or weight_kg <= 0:
        raise ValueError("Height and weight must be greater than zero.")

    height_m = height_cm / 100.0
    bmi = weight_kg / (height_m ** 2)

    if bmi < 18.5:
        category = "Underweight"
        desc = "Your BMI is below normal range. Consider nutrient-dense, healthy caloric intake."
    elif 18.5 <= bmi < 23.0:
        category = "Normal (Healthy Asian Range)"
        desc = "Your BMI is within the healthy range for Indian and South Asian adults."
    elif 23.0 <= bmi < 25.0:
        category = "Overweight (Mild Risk)"
        desc = "Your BMI indicates mild overweight status under ICMR South-Asian cutoffs."
    elif 25.0 <= bmi < 30.0:
        category = "Pre-Obese (Moderate Risk)"
        desc = "Your BMI indicates increased risk. Moderate caloric deficit and activity recommended."
    else:
        category = "Obese (High Risk)"
        desc = "Your BMI is in the obese category. Prioritize medical guidance and gradual lifestyle changes."

    return bmi, category, desc


def calculate_bmr(weight_kg: float, height_cm: float, age: int, sex: str) -> float:
    """
    Calculate Basal Metabolic Rate (BMR) using the Mifflin-St Jeor equation.
    Male:   BMR = 10 * weight + 6.25 * height - 5 * age + 5
    Female: BMR = 10 * weight + 6.25 * height - 5 * age - 161
    """
    sex_norm = sex.strip().lower()
    base = 10.0 * weight_kg + 6.25 * height_cm - 5.0 * age

    if sex_norm in ["male", "m"]:
        bmr = base + 5.0
    elif sex_norm in ["female", "f"]:
        bmr = base - 161.0
    else:
        # Neutral average if unspecified
        bmr = base - 78.0

    return max(500.0, bmr)


def calculate_tdee(bmr: float, activity_level: str) -> float:
    """
    Calculate Total Daily Energy Expenditure (TDEE).
    TDEE = BMR * Activity Factor
    """
    act_norm = activity_level.strip().lower()
    factor = ACTIVITY_FACTORS.get(act_norm, 1.2)
    return bmr * factor


def compute_health_profile(
    age: int,
    sex: str,
    height_cm: float,
    weight_kg: float,
    activity_level: str = "sedentary",
    goal: str = "maintain"
) -> HealthProfileResult:
    """
    Compute full health assessment including BMI, BMR, TDEE, and macro targets.
    Goals:
      - 'maintain': target = TDEE
      - 'lose_weight': target = TDEE - 500 kcal (approx 0.5 kg loss/week)
      - 'gain_weight': target = TDEE + 400 kcal
    """
    bmi, bmi_cat, bmi_desc = calculate_bmi(weight_kg, height_cm)
    bmr = calculate_bmr(weight_kg, height_cm, age, sex)
    tdee = calculate_tdee(bmr, activity_level)

    goal_norm = goal.strip().lower()
    if goal_norm in ["lose", "lose_weight", "deficit"]:
        target_calories = max(bmr, tdee - 500.0)
    elif goal_norm in ["gain", "gain_weight", "surplus"]:
        target_calories = tdee + 400.0
    else:
        target_calories = tdee

    # Macronutrient breakdown for the target calories:
    # Protein: 1.6 g per kg of body weight (healthy standard for body composition)
    protein_g = min(weight_kg * 1.8, target_calories * 0.30 / 4.0)
    protein_cal = protein_g * 4.0

    # Fat: 25% of target calories
    fat_cal = target_calories * 0.25
    fat_g = fat_cal / 9.0

    # Carbohydrates: Remainder of calories
    carbs_cal = max(0.0, target_calories - protein_cal - fat_cal)
    carbs_g = carbs_cal / 4.0

    disclaimer = (
        "Note: BMI, BMR, and TDEE equations provide scientific estimates for guidance. "
        "They do not constitute medical advice, diagnosis, or clinical prescriptions. "
        "Consult a certified dietitian or physician before major dietary interventions."
    )

    return HealthProfileResult(
        age=age,
        sex=sex,
        height_cm=height_cm,
        weight_kg=weight_kg,
        activity_level=activity_level,
        goal=goal,
        bmi=bmi,
        bmi_category=bmi_cat,
        bmi_description=bmi_desc,
        bmr=bmr,
        tdee=tdee,
        target_calories=target_calories,
        target_protein_g=protein_g,
        target_carbs_g=carbs_g,
        target_fat_g=fat_g,
        disclaimer=disclaimer
    )
