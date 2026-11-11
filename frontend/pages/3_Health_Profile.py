"""
NutriLens — Page 3: Personal Health Profile & BMI Analysis
Matches PDF Mockup: Let us get to know you
About you form, Where you stand Indian ICMR-NIN BMI table,
and bottom 3 cards: Eat more of, Go easy on, Daily target.
Starts blank by default until user enters their measurements.
Features 2030 futuristic animated liquid background & rich shaded styling.
"""

import os
import sys

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import streamlit as st
from frontend.utils import (
    apply_custom_theme,
    get_meal_service,
    render_top_navigation,
    render_clean_html
)
from backend.health_calculator import compute_health_profile

st.set_page_config(
    page_title="Health Profile — NutriLens",
    page_icon="👤",
    layout="wide",
    initial_sidebar_state="collapsed"
)
apply_custom_theme()

svc = get_meal_service()
profile = svc.get_user_profile()

render_top_navigation("Health Profile", profile)

# Page Header
render_clean_html("""
<div>
    <div class="nl-headline">Let us get to know you</div>
    <div class="nl-subtitle">A few details so every food tip is made for your body.</div>
</div>
""")

# Top Row: About you (Left) & Where you stand (Right)
col_form, col_stand = st.columns(2, gap="medium")

# Pre-fill values ONLY if user has a saved profile, otherwise start blank!
def_age = int(profile["age"]) if profile and "age" in profile else None
def_ht = float(profile["height_cm"]) if profile and "height_cm" in profile else None
def_wt = float(profile["weight_kg"]) if profile and "weight_kg" in profile else None
def_goal = profile.get("goal", "lose_weight") if profile else "lose_weight"

with col_form:
    with st.container(border=True):
        render_clean_html('<div class="nl-card-title">About you</div>')

        with st.form("profile_form"):
            age_in = st.number_input("Age", min_value=12, max_value=105, value=def_age, step=1, placeholder="Years")
            ht_in = st.number_input("Height (cm or ft and in)", min_value=100.0, max_value=240.0, value=def_ht, step=1.0, placeholder="e.g. 170 cm")
            wt_in = st.number_input("Weight (kg or lbs)", min_value=30.0, max_value=250.0, value=def_wt, step=0.5, placeholder="e.g. 76 kg")
            
            goal_map = {
                "Lose weight": "lose_weight",
                "Maintain weight": "maintain",
                "Build muscle / gain weight": "gain_weight"
            }
            inv_goal_map = {v: k for k, v in goal_map.items()}
            def_choice = inv_goal_map.get(def_goal, "Lose weight")
            
            goal_choice = st.selectbox("Your goal", list(goal_map.keys()), index=list(goal_map.keys()).index(def_choice) if def_choice in goal_map else 0)
            
            save_btn = st.form_submit_button("Save my profile", type="primary")

            if save_btn:
                if age_in is None or ht_in is None or wt_in is None:
                    st.error("Please enter your age, height, and weight to calculate your BMI.")
                else:
                    selected_goal = goal_map[goal_choice]
                    calc_res = compute_health_profile(
                        age=int(age_in),
                        sex=profile.get("sex", "male") if profile else "male",
                        height_cm=float(ht_in),
                        weight_kg=float(wt_in),
                        activity_level="moderately_active",
                        goal=selected_goal
                    )
                    prof_dict = calc_res.to_dict()
                    prof_dict["name"] = profile.get("name", "Friend") if profile else "Friend"
                    svc.save_user_profile(prof_dict)
                    st.success("Calculated and saved your personal health profile!")
                    st.rerun()


with col_stand:
    with st.container(border=True):
        has_bmi = profile and "bmi" in profile

        if has_bmi:
            cur_bmi = float(profile["bmi"])
            is_under = cur_bmi < 18.5
            is_normal = 18.5 <= cur_bmi <= 22.9
            is_mild = 23.0 <= cur_bmi <= 24.9
            is_mod = 25.0 <= cur_bmi <= 29.9
            is_obese = cur_bmi >= 30.0
        else:
            cur_bmi = None
            is_under = is_normal = is_mild = is_mod = is_obese = False

        def row_style(is_here: bool) -> str:
            if is_here:
                return 'background: linear-gradient(135deg, #EDE9FE 0%, #DDD6FE 100%); border-radius: 10px; font-weight: 750; color: #1E1B4B; box-shadow: 0 2px 8px rgba(99, 102, 241, 0.15);'
            return 'border-bottom: 1px solid #F8FAFC;'

        you_badge = '<span style="background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%); color: #FFFFFF; font-size: 0.70rem; font-weight: 750; padding: 3px 9px; border-radius: 9999px; box-shadow: 0 2px 6px rgba(79, 70, 229, 0.35); margin-left: 8px;">YOU ARE HERE</span>'

        if has_bmi:
            footnote_text = f"We use Indian ICMR-NIN cutoffs. Your calculated BMI is <strong>{cur_bmi:.1f}</strong>."
        else:
            footnote_text = "We use Indian ICMR-NIN cutoffs, not Western ones. Enter your info on the left to calculate your BMI."

        table_html = f"""
        <div>
            <div class="nl-card-title">Where you stand</div>
            
            <div style="margin-top: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; {row_style(is_under)}">
                    <span style="font-size: 0.90rem;">Below 18.5</span>
                    <span style="font-size: 0.90rem;">Underweight {you_badge if is_under else ''}</span>
                </div>
                
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; {row_style(is_normal)}">
                    <span style="font-size: 0.90rem;">18.5 to 22.9</span>
                    <span style="font-size: 0.90rem;">Healthy {you_badge if is_normal else ''}</span>
                </div>
                
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; {row_style(is_mild)}">
                    <span style="font-size: 0.90rem;">23.0 to 24.9</span>
                    <span style="font-size: 0.90rem;">Mild overweight {you_badge if is_mild else ''}</span>
                </div>
                
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; {row_style(is_mod)}">
                    <span style="font-size: 0.90rem;">25.0 to 29.9</span>
                    <span style="font-size: 0.90rem;">Moderate overweight {you_badge if is_mod else ''}</span>
                </div>
                
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; {row_style(is_obese)}">
                    <span style="font-size: 0.90rem;">30.0 and above</span>
                    <span style="font-size: 0.90rem;">Obese, high risk {you_badge if is_obese else ''}</span>
                </div>
            </div>

            <div style="font-size: 0.82rem; color: #64748B; margin-top: 14px;">
                {footnote_text}
            </div>
        </div>
        """
        render_clean_html(table_html)


# Bottom Row: 3 Cards with rich shaded gradient backgrounds
col_b1, col_b2, col_b3 = st.columns(3, gap="medium")

# Card 1: Eat more of (Rich shaded emerald tint)
with col_b1:
    if profile and "bmi" in profile:
        bmi_num = float(profile["bmi"])
        if bmi_num >= 23.0:
            eat_msg = "Leafy greens, steamed idli, moong dal, cucumber salad."
        elif bmi_num < 18.5:
            eat_msg = "Paneer, full-fat curd, nuts, whole grains, lentils."
        else:
            eat_msg = "Wholesome seasonal vegetables, dal, sprouts, fresh fruits."
    else:
        eat_msg = "Save your profile on the left to see personalized foods that fit your weight goals."

    eat_more_html = f"""
    <div style="background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%); border: 1px solid #BBF7D0; box-shadow: 0 4px 16px rgba(22, 101, 52, 0.08); border-radius: 18px; padding: 24px; min-height: 180px;">
        <div style="font-size: 1.12rem; font-weight: 750; color: #166534; margin-bottom: 8px;">Eat more of</div>
        <div style="font-size: 0.92rem; color: #15803D; line-height: 1.5;">
            {eat_msg}
        </div>
    </div>
    """
    render_clean_html(eat_more_html)

# Card 2: Go easy on (Rich shaded amber/peach tint)
with col_b2:
    if profile and "bmi" in profile:
        bmi_num = float(profile["bmi"])
        if bmi_num >= 23.0:
            easy_msg = "Samosa, pakora, jalebi, heavy butter gravies."
        elif bmi_num < 18.5:
            easy_msg = "Skipping meals, low-nutrient sugary junk foods."
        else:
            easy_msg = "Deep-fried snacks, excess refined sugar, sodas."
    else:
        easy_msg = "Save your profile on the left to see which rich foods to moderate."

    go_easy_html = f"""
    <div style="background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%); border: 1px solid #FED7AA; box-shadow: 0 4px 16px rgba(154, 52, 18, 0.08); border-radius: 18px; padding: 24px; min-height: 180px;">
        <div style="font-size: 1.12rem; font-weight: 750; color: #9A3412; margin-bottom: 8px;">Go easy on</div>
        <div style="font-size: 0.92rem; color: #C2410C; line-height: 1.5;">
            {easy_msg}
        </div>
    </div>
    """
    render_clean_html(go_easy_html)

# Card 3: Daily target
with col_b3:
    with st.container(border=True):
        if profile and "target_calories" in profile:
            target_str = f"{float(profile['target_calories']):,.0f} kcal"
            target_sub = "From your BMR and activity level."
        else:
            target_str = "— kcal"
            target_sub = "Enter your height & weight to calculate."

        daily_target_html = f"""
        <div style="min-height: 132px; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div class="nl-card-title" style="margin-bottom: 4px;">Daily target</div>
                <div style="font-size: 2.1rem; font-weight: 850; color: #1E1B4B; margin-top: 6px;">{target_str}</div>
            </div>
            <div style="font-size: 0.82rem; color: #64748B;">{target_sub}</div>
        </div>
        """
        render_clean_html(daily_target_html)
