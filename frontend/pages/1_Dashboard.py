"""
NutriLens — Page 1: Dashboard
Matches PDF Mockup: Good morning! Here is your day so far
Calorie budget donut, nutrient bars, solid energy balance card, and today's meals list.
Features 2030 futuristic animated liquid background & rich shaded styling.
"""

import os
import sys
from datetime import date

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

st.set_page_config(
    page_title="Dashboard — NutriLens",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)
apply_custom_theme()

svc = get_meal_service()
profile = svc.get_user_profile()
summary = svc.get_daily_summary()

render_top_navigation("Dashboard", profile)

# Date & Greeting Headline
today_str = date.today().strftime("%A, %d %B")

target_cals = float(profile.get("target_calories") or 2000.0) if profile else 2000.0
consumed_cals = summary["total_calories"]
remaining_cals = max(0.0, target_cals - consumed_cals)
pct_target = min(100.0, (consumed_cals / target_cals) * 100.0) if target_cals > 0 else 0.0

prot_val = summary["total_protein"]
prot_target = 70.0
carbs_val = summary["total_carbs"]
carbs_target = 230.0
fat_val = summary["total_fat"]
fat_target = 55.0
fibre_val = summary["total_fibre"]
fibre_target = 30.0

if summary["total_items"] > 0:
    subtitle_text = f"You have eaten {consumed_cals:,.0f} kcal. {remaining_cals:,.0f} kcal of room is left for today."
else:
    subtitle_text = f"No meals logged yet today. You have your full {target_cals:,.0f} kcal budget available."

render_clean_html(f"""
<div>
    <div class="nl-date-header">{today_str}</div>
    <div class="nl-headline">Good morning! Here is your day so far</div>
    <div class="nl-subtitle">{subtitle_text}</div>
</div>
""")

# Row of 3 Cards
col1, col2, col3 = st.columns(3, gap="medium")

# Card 1: Calorie Budget Donut
with col1:
    with st.container(border=True):
        offset = max(0.0, 251.2 - (pct_target / 100.0 * 251.2))
        donut_html = f"""
        <div style="min-height: 280px; display: flex; flex-direction: column; justify-content: space-between; align-items: center; text-align: center;">
            <div class="nl-card-title" style="width: 100%; text-align: left;">Calorie budget</div>
            
            <div style="position: relative; width: 160px; height: 160px; margin: 8px auto;">
                <svg viewBox="0 0 100 100" style="transform: rotate(-90deg); width: 100%; height: 100%;">
                    <circle cx="50" cy="50" r="40" fill="transparent" stroke="#EDE9FE" stroke-width="12"></circle>
                    <circle cx="50" cy="50" r="40" fill="transparent" stroke="url(#donutGrad)" stroke-width="12"
                            stroke-dasharray="251.2" stroke-dashoffset="{offset:.1f}"
                            stroke-linecap="round"></circle>
                    <defs>
                        <linearGradient id="donutGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#818CF8" />
                            <stop offset="100%" stop-color="#4F46E5" />
                        </linearGradient>
                    </defs>
                </svg>
                <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                    <div style="font-size: 1.85rem; font-weight: 800; color: #1E1B4B; line-height: 1;">{consumed_cals:,.0f}</div>
                    <div style="font-size: 0.78rem; color: #64748B; margin-top: 3px;">of {target_cals:,.0f} kcal</div>
                </div>
            </div>

            <div style="font-size: 0.84rem; color: #4B5563; font-weight: 550; margin-top: 8px;">
                {remaining_cals:,.0f} kcal left · {pct_target:.0f}% of target
            </div>
        </div>
        """
        render_clean_html(donut_html)

# Card 2: Your Nutrients
with col2:
    with st.container(border=True):
        def make_progress(pct: float, grad: str) -> str:
            w = min(100.0, max(0.0, pct))
            return (
                f'<div style="background: #EEF2F6; border-radius: 9999px; height: 9px; width: 100%; overflow: hidden; margin-top: 6px; margin-bottom: 12px; box-shadow: inset 0 1px 2px rgba(0,0,0,0.06);">'
                f'<div style="background: {grad}; width: {w}%; height: 100%; border-radius: 9999px;"></div>'
                f'</div>'
            )

        prot_pct = (prot_val / prot_target) * 100.0 if prot_val > 0 else 0.0
        carbs_pct = (carbs_val / carbs_target) * 100.0 if carbs_val > 0 else 0.0
        fat_pct = (fat_val / fat_target) * 100.0 if fat_val > 0 else 0.0
        fibre_pct = (fibre_val / fibre_target) * 100.0 if fibre_val > 0 else 0.0

        nutrients_html = f"""
        <div style="min-height: 280px; display: flex; flex-direction: column; justify-content: space-between;">
            <div class="nl-card-title">Your nutrients</div>
            
            <div>
                <div style="display: flex; justify-content: space-between; font-size: 0.86rem; font-weight: 550; color: #374151;">
                    <span>Protein</span>
                    <span style="font-weight: 750; color: #1E1B4B;">{prot_val:.0f} / {prot_target:.0f} g</span>
                </div>
                {make_progress(prot_pct, "linear-gradient(90deg, #6366F1 0%, #4F46E5 100%)")}

                <div style="display: flex; justify-content: space-between; font-size: 0.86rem; font-weight: 550; color: #374151;">
                    <span>Carbohydrates</span>
                    <span style="font-weight: 750; color: #1E1B4B;">{carbs_val:.0f} / {carbs_target:.0f} g</span>
                </div>
                {make_progress(carbs_pct, "linear-gradient(90deg, #A5B4FC 0%, #818CF8 100%)")}

                <div style="display: flex; justify-content: space-between; font-size: 0.86rem; font-weight: 550; color: #374151;">
                    <span>Fats</span>
                    <span style="font-weight: 750; color: #1E1B4B;">{fat_val:.0f} / {fat_target:.0f} g</span>
                </div>
                {make_progress(fat_pct, "linear-gradient(90deg, #F472B6 0%, #EC4899 100%)")}

                <div style="display: flex; justify-content: space-between; font-size: 0.86rem; font-weight: 550; color: #374151;">
                    <span>Fibre</span>
                    <span style="font-weight: 750; color: #1E1B4B;">{fibre_val:.0f} / {fibre_target:.0f} g</span>
                </div>
                {make_progress(fibre_pct, "linear-gradient(90deg, #38BDF8 0%, #06B6D4 100%)")}
            </div>
        </div>
        """
        render_clean_html(nutrients_html)

# Card 3: Energy Balance Solid Shaded Gradient Card
with col3:
    if summary["total_items"] > 0:
        balance_sub = "under your daily limit. You are on track for your weight goal."
        if fibre_val < 15:
            tip_msg = "Fibre is a bit low. A cucumber salad with dinner will keep you full longer."
        else:
            tip_msg = "Great balanced nutrient intake today! Drink plenty of water."
    else:
        balance_sub = "available today. You haven't logged any meals yet."
        tip_msg = "Start your day by scanning breakfast or your first dish with the Food Scanner!"

    energy_html = f"""
    <div style="background: linear-gradient(135deg, #6366F1 0%, #4F46E5 50%, #3730A3 100%); border-radius: 18px; padding: 24px; color: #FFFFFF; min-height: 328px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: inset 0 1px 1px rgba(255,255,255,0.35), 0 8px 28px -4px rgba(79, 70, 229, 0.45);">
        <div>
            <div style="font-size: 0.88rem; font-weight: 600; color: rgba(255, 255, 255, 0.88); margin-bottom: 6px;">Energy balance</div>
            <div style="font-size: 2.3rem; font-weight: 850; line-height: 1.1; margin-bottom: 6px;">{remaining_cals:,.0f} kcal</div>
            <div style="font-size: 0.86rem; color: rgba(255, 255, 255, 0.95); line-height: 1.4;">
                {balance_sub}
            </div>
        </div>

        <div style="background: rgba(255, 255, 255, 0.18); backdrop-filter: blur(8px); border-radius: 12px; padding: 12px 14px; font-size: 0.83rem; line-height: 1.45; color: #FFFFFF; border: 1px solid rgba(255, 255, 255, 0.25);">
            {tip_msg}
        </div>
    </div>
    """
    render_clean_html(energy_html)

# Today's Meals Section
meals_entries = summary.get("entries", [])

with st.container(border=True):
    render_clean_html('<div class="nl-card-title" style="margin-bottom: 6px;">Today’s meals</div>')
    
    if meals_entries:
        rows_html = ""
        for entry in meals_entries:
            meal_name = entry.get("meal_type", "Meal").title()
            qty_str = f"{float(entry.get('quantity', 1)):.1f}".rstrip("0").rstrip(".")
            dish_desc = f"{entry.get('food_name', '').replace('_', ' ').title()} · {qty_str} {entry.get('unit', 'serving')}"
            kcal_str = f"{entry.get('calories', 0):.0f} kcal"
            rows_html += f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #F1F5F9;">
                <div style="width: 120px; font-weight: 600; color: #64748B; font-size: 0.88rem;">{meal_name}</div>
                <div style="flex: 1; font-weight: 600; color: #1E1B4B; font-size: 0.92rem;">{dish_desc}</div>
                <div style="font-weight: 750; color: #4F46E5; font-size: 0.92rem;">{kcal_str}</div>
            </div>
            """
        render_clean_html(rows_html)
    else:
        empty_html = """
        <div style="text-align: center; padding: 26px 14px; color: #64748B; font-size: 0.90rem;">
            No meals logged for today yet. Scan or add your first meal in <strong>Food Scanner</strong> to see it here!
        </div>
        """
        render_clean_html(empty_html)
