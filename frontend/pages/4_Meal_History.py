"""
NutriLens — Page 4: Meal History & Logs
Matches PDF Mockup: Your last few days
Daily average card, Date range selector, Under or over your target bar chart,
and Meals list with itemized dishes and Delete action.
Starts blank by default and displays actual user history.
Features 2030 futuristic animated liquid background & rich shaded styling.
"""

import os
import sys
from datetime import datetime, date, timedelta

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
    page_title="Meal History — NutriLens",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed"
)
apply_custom_theme()

svc = get_meal_service()
profile = svc.get_user_profile()

render_top_navigation("Meal History", profile)

# Page Header
render_clean_html("""
<div>
    <div class="nl-headline">Your last few days</div>
    <div class="nl-subtitle">Small habits add up. Here is how the week looked.</div>
</div>
""")

# Top Row: Daily average (Left) & Date range (Right)
col_avg, col_range = st.columns(2, gap="medium")

# Fetch recent entries
end_d = date.today()
start_d = end_d - timedelta(days=6)
entries = svc.get_meal_history(start_date=start_d.isoformat(), end_date=end_d.isoformat(), limit=100)

target_cal = float(profile.get("target_calories") or 2000.0) if profile else 2000.0

if entries:
    total_cals = sum(e["calories"] for e in entries)
    num_days = max(1, len(set(e["date"] for e in entries)))
    avg_cals = total_cals / num_days
    avg_sub = f"Calculated across {num_days} day(s)"
else:
    avg_cals = 0.0
    avg_sub = "No meals logged in this period"

with col_avg:
    with st.container(border=True):
        avg_html = f"""
        <div style="min-height: 110px; display: flex; flex-direction: column; justify-content: space-between;">
            <div class="nl-card-title" style="margin-bottom: 2px;">Daily average</div>
            <div style="font-size: 2.1rem; font-weight: 850; color: #1E1B4B;">{avg_cals:,.0f} kcal</div>
            <div style="font-size: 0.82rem; color: #64748B;">{avg_sub}</div>
        </div>
        """
        render_clean_html(avg_html)

with col_range:
    with st.container(border=True):
        render_clean_html('<div class="nl-card-title" style="margin-bottom: 4px;">Date range</div>')
        date_options = [
            f"{start_d.strftime('%d %b')} to {end_d.strftime('%d %b')}",
            "Last 14 days",
            "Last 30 days"
        ]
        st.selectbox("Showing", date_options, label_visibility="visible")


# Middle Card: Under or over your target
with st.container(border=True):
    render_clean_html('<div class="nl-card-title" style="margin-bottom: 24px;">Under or over your target</div>')

    if entries:
        # Group by date for real data
        day_totals = {}
        for i in range(7):
            d_str = (start_d + timedelta(days=i)).isoformat()
            day_totals[d_str] = 0.0
        for e in entries:
            d = e.get("date")
            if d in day_totals:
                day_totals[d] += e.get("calories", 0.0)

        bars_html = '<div style="display: flex; align-items: flex-end; justify-content: space-between; height: 160px; padding: 0 16px 12px 16px; border-bottom: 1px solid #E2E8F0; gap: 14px;">'
        for d_str, cals in day_totals.items():
            dt = datetime.strptime(d_str, "%Y-%m-%d")
            day_label = dt.strftime("%a")
            is_over = cals > target_cal
            bar_color = "linear-gradient(180deg, #FB7185 0%, #E11D48 100%)" if is_over else "linear-gradient(180deg, #6366F1 0%, #4F46E5 100%)"
            height_pct = min(100.0, max(12.0, (cals / target_cal) * 80.0)) if cals > 0 else 4.0
            
            bars_html += f"""
            <div style="flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%; justify-content: flex-end;">
                <div style="font-size: 0.72rem; font-weight: 650; color: #64748B; margin-bottom: 4px;">{cals:.0f}</div>
                <div style="width: 100%; max-width: 80px; height: {height_pct}%; background: {bar_color}; border-radius: 8px 8px 0 0; box-shadow: 0 2px 6px rgba(79, 70, 229, 0.25);"></div>
                <div style="font-size: 0.75rem; color: #64748B; margin-top: 6px;">{day_label}</div>
            </div>
            """
        bars_html += '</div>'
        bars_html += '<div style="font-size: 0.82rem; color: #64748B; margin-top: 14px;">Indigo means under target, pink means over target.</div>'
        render_clean_html(bars_html)
    else:
        empty_chart = """
        <div style="text-align: center; padding: 36px 14px; color: #64748B; font-size: 0.90rem;">
            No meal history recorded for this period yet. Once you scan and add dishes in the <strong>Food Scanner</strong>, your daily target progress will be charted here.
        </div>
        """
        render_clean_html(empty_chart)


# Bottom Card: Meals List
with st.container(border=True):
    render_clean_html('<div class="nl-card-title" style="margin-bottom: 12px;">Meals</div>')

    if entries:
        for idx, e in enumerate(entries):
            m_date = datetime.strptime(e["date"], "%Y-%m-%d").strftime("%d %b") if "date" in e else "Today"
            qty_str = f"{float(e.get('quantity', 1)):.1f}".rstrip("0").rstrip(".")
            m_dish = f"{e.get('food_name', '').replace('_', ' ').title()} · {qty_str} {e.get('unit', 'piece')}"
            m_cal = f"{e.get('calories', 0):.0f} kcal"
            
            c_row1, c_row2, c_row3, c_del = st.columns([1.5, 4.5, 1.5, 1])
            with c_row1:
                st.write(f"**{m_date}**")
            with c_row2:
                st.write(m_dish)
            with c_row3:
                st.write(f"**{m_cal}**")
            with c_del:
                if st.button("Delete", key=f"del_meal_{e['id']}", type="secondary"):
                    svc.delete_meal_entry(e["id"])
                    st.rerun()
    else:
        empty_meals = """
        <div style="text-align: center; padding: 24px 14px; color: #64748B; font-size: 0.90rem;">
            No meal entries logged yet. Go to <strong>Food Scanner</strong> to log your first meal!
        </div>
        """
        render_clean_html(empty_meals)
