"""
NutriLens — Home Page (Page 1)
Matches Mockup: Hello! What did you eat today?
Two easy steps: know your body, then scan your plate. No spreadsheets, no jargon.
Features 2030 futuristic animated liquid background & rich shaded styling.
"""

import os
import sys

# Ensure root directory is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import streamlit as st
from frontend.utils import (
    apply_custom_theme,
    get_meal_service,
    render_top_navigation,
    render_clean_html
)
from backend.database import init_db

# Page Configuration with collapsed sidebar
st.set_page_config(
    page_title="NutriLens — Indian Food & Nutrition Tracker",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize database and apply theme
init_db()
apply_custom_theme()

svc = get_meal_service()
profile = svc.get_user_profile()
summary = svc.get_daily_summary()

# Render Top Bar matching PDF: NutriLens (Left) | Tabs (Center with guaranteed active pill) | BMI Pill (Right)
render_top_navigation("Home", profile)

# Page Headline & Subtitle
render_clean_html("""
<div>
    <div class="nl-headline">Hello! What did you eat today?</div>
    <div class="nl-subtitle">Two easy steps: know your body, then scan your plate. No spreadsheets, no jargon.</div>
</div>
""")

# Two Steps Row
col1, col2 = st.columns(2, gap="medium")

with col1:
    with st.container(border=True):
        render_clean_html("""
        <div>
            <div class="nl-pill nl-pill-step1">Step 1</div>
            <div class="nl-card-title">Understand your body</div>
            <div class="nl-card-desc">
                Tell us your height and weight. We read your BMI using Indian 
                (ICMR-NIN) cutoffs, which suit our bodies better.
            </div>
        </div>
        """)
        if st.button("Set up my profile", key="btn_setup_profile", type="primary"):
            st.switch_page("pages/3_Health_Profile.py")

with col2:
    with st.container(border=True):
        render_clean_html("""
        <div>
            <div class="nl-pill nl-pill-step2">Step 2</div>
            <div class="nl-card-title">Scan your food</div>
            <div class="nl-card-desc">
                Click a photo of your samosa, thali or dal. Say it in pieces or 
                grams, whichever you know.
            </div>
        </div>
        """)
        if st.button("Scan a meal", key="btn_scan_meal", type="primary"):
            st.switch_page("pages/2_Food_Scanner.py")

# Today so far Card — Dynamically populated from actual logs with rich shaded pills
target_val = float(profile.get("target_calories") or 2000.0) if profile else 2000.0
eaten_val = summary["total_calories"]
left_val = max(0, int(target_val - eaten_val))
meals_logged = summary["total_items"]

with st.container(border=True):
    if meals_logged > 0:
        badge_sub = ""
    else:
        badge_sub = '<div style="font-size: 0.82rem; color: #64748B; margin-top: 10px;">No meals logged yet today. Click "Scan a meal" above to log your first dish!</div>'

    today_html = f"""
    <div>
        <div class="nl-card-title" style="margin-bottom: 14px;">Today so far</div>
        <div style="display: flex; gap: 12px; flex-wrap: wrap; align-items: center;">
            <span style="background: linear-gradient(135deg, #EDE9FE 0%, #DDD6FE 100%); color: #4338CA; border: 1px solid #C4B5FD; box-shadow: 0 2px 8px rgba(99, 102, 241, 0.14); font-size: 0.88rem; font-weight: 650; padding: 6px 18px; border-radius: 9999px;">
                {eaten_val:,.0f} kcal eaten
            </span>
            <span style="background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%); color: #047857; border: 1px solid #6EE7B7; box-shadow: 0 2px 8px rgba(13, 148, 136, 0.14); font-size: 0.88rem; font-weight: 650; padding: 6px 18px; border-radius: 9999px;">
                {left_val:,.0f} kcal left
            </span>
            <span style="background: linear-gradient(135deg, #F3E8FF 0%, #E9D5FF 100%); color: #6B21A8; border: 1px solid #D8B4FE; box-shadow: 0 2px 8px rgba(107, 33, 168, 0.14); font-size: 0.88rem; font-weight: 650; padding: 6px 18px; border-radius: 9999px;">
                {meals_logged} meals logged
            </span>
        </div>
        {badge_sub}
    </div>
    """
    render_clean_html(today_html)

# 43 Indian dishes we understand Card — with shaded pill tags
with st.container(border=True):
    dishes_html = """
    <div>
        <div class="nl-card-title" style="margin-bottom: 14px;">43 Indian dishes we understand</div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
            <span style="background: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%); color: #4338CA; border: 1px solid #DDD6FE; box-shadow: 0 2px 5px rgba(99, 102, 241, 0.08); font-size: 0.84rem; font-weight: 550; padding: 6px 15px; border-radius: 9999px;">Idli</span>
            <span style="background: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%); color: #4338CA; border: 1px solid #DDD6FE; box-shadow: 0 2px 5px rgba(99, 102, 241, 0.08); font-size: 0.84rem; font-weight: 550; padding: 6px 15px; border-radius: 9999px;">Dal tadka</span>
            <span style="background: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%); color: #4338CA; border: 1px solid #DDD6FE; box-shadow: 0 2px 5px rgba(99, 102, 241, 0.08); font-size: 0.84rem; font-weight: 550; padding: 6px 15px; border-radius: 9999px;">Roti</span>
            <span style="background: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%); color: #4338CA; border: 1px solid #DDD6FE; box-shadow: 0 2px 5px rgba(99, 102, 241, 0.08); font-size: 0.84rem; font-weight: 550; padding: 6px 15px; border-radius: 9999px;">Bhindi</span>
            <span style="background: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%); color: #4338CA; border: 1px solid #DDD6FE; box-shadow: 0 2px 5px rgba(99, 102, 241, 0.08); font-size: 0.84rem; font-weight: 550; padding: 6px 15px; border-radius: 9999px;">Samosa</span>
            <span style="background: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%); color: #4338CA; border: 1px solid #DDD6FE; box-shadow: 0 2px 5px rgba(99, 102, 241, 0.08); font-size: 0.84rem; font-weight: 550; padding: 6px 15px; border-radius: 9999px;">Jalebi</span>
            <span style="background: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%); color: #4338CA; border: 1px solid #DDD6FE; box-shadow: 0 2px 5px rgba(99, 102, 241, 0.08); font-size: 0.84rem; font-weight: 550; padding: 6px 15px; border-radius: 9999px;">Poha</span>
            <span style="background: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%); color: #4338CA; border: 1px solid #DDD6FE; box-shadow: 0 2px 5px rgba(99, 102, 241, 0.08); font-size: 0.84rem; font-weight: 550; padding: 6px 15px; border-radius: 9999px;">Rajma</span>
            <span style="color: #64748B; font-size: 0.84rem; font-weight: 500; padding: 6px 10px;">and 35 more</span>
        </div>
    </div>
    """
    render_clean_html(dishes_html)
