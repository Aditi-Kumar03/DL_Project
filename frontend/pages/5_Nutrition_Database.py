"""
NutriLens — Page 5: Nutrition Database Explorer
Matches PDF Mockup: Indian food, explained
43 dishes with values from the IFCT 2017 tables, per 100 g.
Search input, category filter pills, clean data table, and 'Add my own recipe' button.
Features 2030 futuristic animated liquid background & rich shaded styling.
"""

import os
import sys

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import streamlit as st
import pandas as pd
from frontend.utils import (
    apply_custom_theme,
    get_meal_service,
    render_top_navigation,
    render_clean_html
)
from backend.database import get_all_foods, update_or_add_food

st.set_page_config(
    page_title="Nutrition Database — NutriLens",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="collapsed"
)
apply_custom_theme()

svc = get_meal_service()
profile = svc.get_user_profile()

render_top_navigation("Nutrition DB", profile)

# Page Header
render_clean_html("""
<div>
    <div class="nl-headline">Indian food, explained</div>
    <div class="nl-subtitle">43 dishes with values from the IFCT 2017 tables, per 100 g.</div>
</div>
""")

foods = get_all_foods()

# Main Card Container
with st.container(border=True):
    # Search Input
    search_term = st.text_input("Search a dish", placeholder="Try dal, paneer or poha", label_visibility="visible")

    # Category Filter Pills
    pill_categories = ["All", "Breakfast", "Dal and curries", "Snacks", "Sweets"]

    if "selected_db_cat" not in st.session_state:
        st.session_state.selected_db_cat = "All"

    p_cols = st.columns(len(pill_categories), gap="small")
    for col, cat_name in zip(p_cols, pill_categories):
        with col:
            is_sel = (st.session_state.selected_db_cat == cat_name)
            if st.button(
                cat_name,
                key=f"cat_pill_{cat_name}",
                type="primary" if is_sel else "secondary",
                use_container_width=True
            ):
                st.session_state.selected_db_cat = cat_name
                st.rerun()

    # Filter food records
    filtered = []
    for f in foods:
        f_cat = f.get("category", "").lower()
        f_name = f.get("food_name", "").lower()
        d_name = f.get("display_name", "").lower()

        # Search filter
        if search_term.strip():
            q = search_term.strip().lower()
            if q not in f_name and q not in d_name:
                continue

        # Category filter
        sel = st.session_state.selected_db_cat
        if sel == "All":
            filtered.append(f)
        elif sel == "Breakfast":
            if "breakfast" in f_cat or any(k in f_name for k in ["idli", "dosa", "poha", "upma", "puri", "paratha"]):
                filtered.append(f)
        elif sel == "Dal and curries":
            if "curry" in f_cat or "dal" in f_cat or any(k in f_name for k in ["dal", "chole", "rajma", "paneer", "aloo_gobi", "chicken"]):
                filtered.append(f)
        elif sel == "Snacks":
            if "snack" in f_cat or "chaat" in f_cat or "fast food" in f_cat or "bread" in f_cat:
                filtered.append(f)
        elif sel == "Sweets":
            if "sweet" in f_cat or "dessert" in f_cat or "beverage" in f_cat:
                filtered.append(f)

    # Build Clean Data Table Rows matching PDF Mockup
    table_rows = ""
    for f in filtered:
        dish = f.get("display_name", f.get("food_name", "").replace("_", " ").title())
        cal = f"{f.get('calories_per_100g', 0):.0f}"
        fat = f"{f.get('fat_per_100g', 0):.1f} g"
        carbs = f"{f.get('carbs_per_100g', 0):.1f} g"
        prot = f"{f.get('protein_per_100g', 0):.1f} g"
        fibr = f"{f.get('fibre_per_100g', 0):.1f} g"
        serving = f"1 {f.get('default_serving_unit', 'serving')}"

        table_rows += f"""
        <tr style="border-bottom: 1px solid #F1F5F9; color: #1E1B4B;">
            <td style="padding: 13px 14px; font-weight: 650;">{dish}</td>
            <td style="padding: 13px 14px;">{cal}</td>
            <td style="padding: 13px 14px;">{fat}</td>
            <td style="padding: 13px 14px;">{carbs}</td>
            <td style="padding: 13px 14px;">{prot}</td>
            <td style="padding: 13px 14px;">{fibr}</td>
            <td style="padding: 13px 14px; color: #64748B;">{serving}</td>
        </tr>
        """

    if not filtered:
        table_rows = """
        <tr>
            <td colspan="7" style="padding: 24px; text-align: center; color: #64748B;">
                No Indian dishes found matching your search.
            </td>
        </tr>
        """

    table_html = f"""
    <div style="margin-top: 18px; overflow-x: auto;">
        <table style="width: 100%; border-collapse: collapse; font-size: 0.90rem; text-align: left;">
            <thead>
                <tr style="border-bottom: 1.5px solid #E2E8F0; color: #1E1B4B; font-weight: 700;">
                    <th style="padding: 10px 14px;">Dish</th>
                    <th style="padding: 10px 14px;">kcal</th>
                    <th style="padding: 10px 14px;">Fat</th>
                    <th style="padding: 10px 14px;">Carbs</th>
                    <th style="padding: 10px 14px;">Protein</th>
                    <th style="padding: 10px 14px;">Fibre</th>
                    <th style="padding: 10px 14px;">1 serving</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </div>
    """
    render_clean_html(table_html)

    # Add my own recipe button
    st.write("")
    show_add_recipe = st.button("Add my own recipe", key="btn_add_recipe", type="primary")

    if show_add_recipe or ("show_recipe_form" in st.session_state and st.session_state.show_recipe_form):
        st.session_state.show_recipe_form = True
        with st.expander("Add Custom Recipe to Database", expanded=True):
            with st.form("custom_recipe_form"):
                c_rf1, c_rf2 = st.columns(2)
                with c_rf1:
                    r_id = st.text_input("Dish Identifier (e.g. palak_paneer)", placeholder="lowercase_with_underscores")
                    r_name = st.text_input("Dish Name", placeholder="e.g. Palak Paneer")
                    r_cat = st.selectbox("Category", ["Curry / Sabji", "Breakfast / Snacks", "Breads", "Sweets / Desserts", "Other"])
                with c_rf2:
                    r_cal = st.number_input("Calories per 100g", min_value=0.0, max_value=900.0, value=140.0, step=5.0)
                    r_prot = st.number_input("Protein per 100g (g)", min_value=0.0, max_value=80.0, value=6.0, step=0.5)
                    r_fat = st.number_input("Fat per 100g (g)", min_value=0.0, max_value=80.0, value=7.0, step=0.5)
                    r_carbs = st.number_input("Carbs per 100g (g)", min_value=0.0, max_value=80.0, value=12.0, step=0.5)
                    r_fibre = st.number_input("Fibre per 100g (g)", min_value=0.0, max_value=40.0, value=2.5, step=0.5)
                
                r_unit = st.selectbox("1 Serving Unit", ["bowl", "piece", "plate", "roti", "cup"])
                r_submit = st.form_submit_button("Save Recipe", type="primary")

                if r_submit:
                    if not r_id or not r_name:
                        st.error("Dish identifier and name are required.")
                    else:
                        update_or_add_food({
                            "food_name": r_id.strip().lower().replace(" ", "_"),
                            "display_name": r_name.strip(),
                            "calories_per_100g": float(r_cal),
                            "protein_per_100g": float(r_prot),
                            "carbs_per_100g": float(r_carbs),
                            "fat_per_100g": float(r_fat),
                            "fibre_per_100g": float(r_fibre),
                            "category": r_cat,
                            "preparation_state": "cooked",
                            "default_serving_unit": r_unit,
                            "default_serving_weight_g": 120.0,
                            "source": "User Recipe"
                        })
                        st.session_state.show_recipe_form = False
                        st.success(f"Saved {r_name} to database!")
                        st.rerun()
