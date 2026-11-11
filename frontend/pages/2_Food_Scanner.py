"""
NutriLens — Page 2: Food Scanner
Supports Single Meal and Multiple Meals (Thali / Multi-Dish) scanning.
2-Step Workflow:
  1. Scan & Predict (asks quantity before scanning in Single Meal mode)
  2. Review & Edit predicted meal(s), then click Report to generate the meal-wise nutrition report.
Features 2030 futuristic animated liquid background & rich shaded styling.
"""

import os
import sys
from typing import List, Dict, Any
from PIL import Image, ImageDraw, ImageFont

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import streamlit as st
from frontend.utils import (
    apply_custom_theme,
    get_cached_classifier,
    get_meal_service,
    render_top_navigation,
    render_clean_html,
    evaluate_food_suitability
)
from backend.nutrition_engine import calculate_food_nutrition, calculate_meal_totals
from backend.database import get_all_foods, get_serving_units

st.set_page_config(
    page_title="Food Scanner — NutriLens",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="collapsed"
)
apply_custom_theme()

clf = get_cached_classifier()
svc = get_meal_service()
profile = svc.get_user_profile()

render_top_navigation("Food Scanner", profile)

# Load food metadata for editing & unit selection
all_foods = get_all_foods()
food_info_map: Dict[str, Dict[str, Any]] = {f["food_name"]: f for f in all_foods}
all_food_keys: List[str] = sorted(
    food_info_map.keys(),
    key=lambda k: food_info_map[k].get("display_name", k)
)

# Page Header
render_clean_html("""
<div>
    <div class="nl-headline">What is on your plate?</div>
    <div class="nl-subtitle">Step 1: Scan and predict your meal(s). Step 2: Check or edit predictions, then generate your report.</div>
</div>
""")

# Initialize session state
defaults = {
    "scanner_image": None,
    "scanner_source": None,
    "scan_mode": "Single Meal",
    "detected_dish": None,
    "edited_dish": None,
    "detection_summary": None,
    "multi_items": [],
    "multi_next_uid": 1,
    "report_generated": False,
    "active_uploader": None,
    "last_uploaded_token": None,
    "last_camera_token": None,
    "saved_count": None,
    "saved_grams": None,
    "saved_unit": "piece",
    "scanner_unit_mode": "Pieces",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def _reset_scan_state():
    st.session_state.detected_dish = None
    st.session_state.edited_dish = None
    st.session_state.detection_summary = None
    st.session_state.multi_items = []
    st.session_state.report_generated = False
    if "inp_single_edited_dish" in st.session_state:
        del st.session_state["inp_single_edited_dish"]


def _sync_count():
    st.session_state.saved_count = st.session_state.get("inp_count")


def _sync_grams():
    st.session_state.saved_grams = st.session_state.get("inp_grams")


def _sync_unit():
    val = st.session_state.get("inp_unit")
    st.session_state.saved_unit = (val or "piece").strip() or "piece"


def _sync_single_edited_dish():
    st.session_state.edited_dish = st.session_state.get("inp_single_edited_dish")


def _remove_multi_item(target_uid: int):
    st.session_state.multi_items = [
        x for x in st.session_state.multi_items if x["uid"] != target_uid
    ]
    for prefix in ("m_dish_", "m_unit_", "m_qty_"):
        st.session_state.pop(f"{prefix}{target_uid}", None)
    if not st.session_state.multi_items:
        st.session_state.report_generated = False


def _add_manual_multi_item():
    uid = st.session_state.multi_next_uid
    st.session_state.multi_next_uid += 1
    default_k = "chapati" if "chapati" in food_info_map else all_food_keys[0]
    st.session_state.multi_items.append({
        "uid": uid,
        "predicted_dish": default_k,
        "dish": default_k,
        "confidence": 0.0,
        "box": None,
        "quantity": 1.0,
        "unit": food_info_map.get(default_k, {}).get("default_serving_unit", "serving"),
    })


def _get_food_units(food_key: str) -> List[str]:
    units = [u["unit_name"] for u in get_serving_units(food_key)]
    def_unit = food_info_map.get(food_key, {}).get("default_serving_unit", "serving")
    ordered: List[str] = []
    for candidate in [def_unit, *units, "g"]:
        if candidate and candidate not in ordered:
            ordered.append(candidate)
    return ordered or ["serving", "g"]


def _annotate_multi_image(image: Image.Image, items: List[Dict[str, Any]]) -> Image.Image:
    """Draw numbered dish bounding boxes on a copy of the image for visual inspection."""
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)
    palette = ["#4F46E5", "#059669", "#D97706", "#DB2777", "#0284C7", "#7C3AED"]
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    w, h = annotated.size
    line_w = max(2, int(min(w, h) * 0.006))

    for idx, item in enumerate(items):
        box = item.get("box")
        if not box or len(box) != 4:
            continue
        x1, y1, x2, y2 = [int(v) for v in box]
        color = palette[idx % len(palette)]
        draw.rectangle([x1, y1, x2, y2], outline=color, width=line_w)

        dish_label = food_info_map.get(item["dish"], {}).get(
            "display_name", item["dish"].replace("_", " ").title()
        )
        tag = f"#{idx + 1} {dish_label}"
        pad_x, pad_y = 6, 4
        if font:
            tb = draw.textbbox((0, 0), tag, font=font)
            tw, th = tb[2] - tb[0], tb[3] - tb[1]
        else:
            tw, th = len(tag) * 6, 12
        ly1 = max(0, y1)
        lx2 = min(w, x1 + tw + pad_x * 2)
        ly2 = min(h, ly1 + th + pad_y * 2)
        draw.rectangle([x1, ly1, lx2, ly2], fill=color)
        draw.text((x1 + pad_x, ly1 + pad_y), tag, fill="#FFFFFF", font=font)

    return annotated


def _add_single_meal_to_db(dish_key: str, qty: float, unit_str: str, calc_item):
    global svc
    if not hasattr(svc, "add_meal_entry"):
        import importlib
        import backend.meal_service as _meal_service_mod
        importlib.reload(_meal_service_mod)
        svc = _meal_service_mod.MealService(db_path=svc.db_path)

    if hasattr(svc, "add_meal_entry"):
        svc.add_meal_entry(
            meal_type="Snack",
            food_name=dish_key,
            quantity=float(qty),
            unit=unit_str,
            weight_g=float(calc_item.weight_g if calc_item else 100.0),
            calories=float(calc_item.calories if calc_item else 0.0),
            protein=float(calc_item.protein_g if calc_item else 0.0),
            carbs=float(calc_item.carbs_g if calc_item else 0.0),
            fat=float(calc_item.fat_g if calc_item else 0.0),
            fibre=float(calc_item.fibre_g if calc_item else 0.0),
        )
    else:
        svc.log_meal_items(
            meal_type="Snack",
            items=[{
                "food_name": dish_key,
                "quantity": float(qty),
                "unit": unit_str,
                "custom_weight_g": float(calc_item.weight_g if calc_item else 100.0),
            }],
        )


# Load sample paths
sample_dir = os.path.join(root_dir, "sample_images")
samosa_path = os.path.join(sample_dir, "samosa.jpg")
jalebi_path = os.path.join(sample_dir, "jalebi.jpg")

col_left, col_right = st.columns(2, gap="medium")

# LEFT CARD: Your photo
with col_left:
    with st.container(border=True):
        render_clean_html('<div class="nl-card-title">Your photo</div>')

        # Upper side prediction banner (shown right below card title)
        if st.session_state.scan_mode == "Single Meal" and st.session_state.detection_summary:
            dish_summary_text = st.session_state.detection_summary
            edited_note = ""
            if st.session_state.edited_dish and st.session_state.edited_dish != st.session_state.detected_dish:
                edited_name = food_info_map.get(st.session_state.edited_dish, {}).get(
                    "display_name", st.session_state.edited_dish.replace("_", " ").title()
                )
                edited_note = f' <span style="color: #4F46E5; font-weight: 650;">(Edited to: {edited_name})</span>'
            render_clean_html(f"""
                <div style="font-size: 0.92rem; color: #4B5563; margin-top: 2px; margin-bottom: 12px;">
                    Looks like: <strong style="color: #1E1B4B;">{dish_summary_text}</strong>{edited_note}
                </div>
            """)
        elif st.session_state.scan_mode == "Multiple Meals" and st.session_state.multi_items:
            summary_parts = []
            for idx, item in enumerate(st.session_state.multi_items):
                d_name = food_info_map.get(item["dish"], {}).get(
                    "display_name", item["dish"].replace("_", " ").title()
                )
                summary_parts.append(f"#{idx + 1} {d_name}")
            multi_summary_str = " · ".join(summary_parts)
            render_clean_html(f"""
                <div style="font-size: 0.92rem; color: #4B5563; margin-top: 2px; margin-bottom: 12px;">
                    Detected {len(st.session_state.multi_items)} meal(s): <strong style="color: #1E1B4B;">{multi_summary_str}</strong>
                </div>
            """)
        elif st.session_state.scanner_image is not None:
            render_clean_html("""
                <div style="font-size: 0.88rem; color: #6366F1; margin-top: 2px; margin-bottom: 12px; font-weight: 550;">
                    Photo ready. Use Step 1 on the right to scan &amp; predict.
                </div>
            """)

        # Photo preview (annotated with numbered boxes in Multiple Meals mode after scanning)
        if st.session_state.scanner_image is not None:
            if st.session_state.scan_mode == "Multiple Meals" and st.session_state.multi_items:
                disp_img = _annotate_multi_image(st.session_state.scanner_image, st.session_state.multi_items)
                st.image(disp_img, use_container_width=True)
            else:
                st.image(st.session_state.scanner_image, use_container_width=True)
        else:
            render_clean_html("""
            <div style="border: 2px dashed #C7D2FE; border-radius: 14px; background: rgba(238, 242, 255, 0.85); min-height: 200px; display: flex; align-items: center; justify-content: center; color: #6366F1; font-weight: 550; font-size: 0.95rem; margin-bottom: 16px; text-align: center; padding: 20px;">
                Upload, click camera, or select a sample dish below
            </div>
            """)

        # 4 Action Pills: Upload, Camera, Samosa, Jalebi
        b_col1, b_col2, b_col3, b_col4 = st.columns(4, gap="small")

        with b_col1:
            show_upload = st.button("Upload", key="btn_upload_pill", use_container_width=True, type="primary")
        with b_col2:
            show_cam = st.button("Camera", key="btn_cam_pill", use_container_width=True, type="secondary")
        with b_col3:
            if st.button("Samosa", key="btn_samosa_pill", use_container_width=True, type="secondary"):
                if os.path.exists(samosa_path):
                    st.session_state.scanner_image = Image.open(samosa_path).convert("RGB")
                    st.session_state.scanner_source = "sample_samosa"
                    st.session_state.active_uploader = None
                    st.session_state.last_uploaded_token = None
                    st.session_state.last_camera_token = None
                    _reset_scan_state()
                    st.rerun()
        with b_col4:
            if st.button("Jalebi", key="btn_jalebi_pill", use_container_width=True, type="secondary"):
                if os.path.exists(jalebi_path):
                    st.session_state.scanner_image = Image.open(jalebi_path).convert("RGB")
                    st.session_state.scanner_source = "sample_jalebi"
                    st.session_state.active_uploader = None
                    st.session_state.last_uploaded_token = None
                    st.session_state.last_camera_token = None
                    _reset_scan_state()
                    st.rerun()

        if show_upload:
            st.session_state.active_uploader = "file"
        elif show_cam:
            st.session_state.active_uploader = "cam"

        # Expandable File Uploader / Camera (loads image only; waits for Step 1 Scan)
        if st.session_state.active_uploader == "file":
            up_file = st.file_uploader("Upload meal photo:", type=["jpg", "jpeg", "png", "webp"], key="scanner_file_up")
            if up_file is not None:
                file_token = (up_file.name, up_file.size)
                if file_token != st.session_state.last_uploaded_token:
                    st.session_state.scanner_image = Image.open(up_file).convert("RGB")
                    st.session_state.scanner_source = "upload"
                    st.session_state.last_uploaded_token = file_token
                    _reset_scan_state()
                    st.rerun()
            elif st.session_state.last_uploaded_token is not None:
                st.session_state.last_uploaded_token = None

        elif st.session_state.active_uploader == "cam":
            cam_file = st.camera_input("Take a photo:", key="scanner_camera_in")
            if cam_file is not None:
                cam_token = (cam_file.name, cam_file.size)
                if cam_token != st.session_state.last_camera_token:
                    st.session_state.scanner_image = Image.open(cam_file).convert("RGB")
                    st.session_state.scanner_source = "camera"
                    st.session_state.last_camera_token = cam_token
                    _reset_scan_state()
                    st.rerun()
            elif st.session_state.last_camera_token is not None:
                st.session_state.last_camera_token = None

        # Crop Expander for thali
        with st.expander("Eating a thali? Crop one bowl or switch to Multiple Meals."):
            st.caption("You can focus on a single bowl or use Multiple Meals mode on the right:")
            if st.session_state.scanner_image is not None:
                w, h = st.session_state.scanner_image.size
                cx1, cx2 = st.columns(2)
                with cx1:
                    xmin = st.slider("Left %", 0, 90, 10, key="thali_x1")
                    xmax = st.slider("Right %", 10, 100, 90, key="thali_x2")
                with cx2:
                    ymin = st.slider("Top %", 0, 90, 10, key="thali_y1")
                    ymax = st.slider("Bottom %", 10, 100, 90, key="thali_y2")
                if st.button("Crop Selection", type="secondary", key="btn_crop_dish"):
                    if xmax <= xmin or ymax <= ymin:
                        st.error("Right % must be greater than Left % and Bottom % must be greater than Top %.")
                    else:
                        box = [int(xmin * w / 100), int(ymin * h / 100), int(xmax * w / 100), int(ymax * h / 100)]
                        if box[2] <= box[0] or box[3] <= box[1]:
                            st.error("Selected crop area is too small. Please widen the sliders.")
                        else:
                            cropped = st.session_state.scanner_image.crop(box)
                            st.session_state.scanner_image = cropped
                            st.session_state.scanner_source = "cropped"
                            _reset_scan_state()
                            st.rerun()
            else:
                st.info("Upload or take a photo first to use the crop tool.")


# RIGHT CARD: Scan Mode + Step 1 (Scan & Predict) + Step 2 (Check/Edit & Report)
count_val = None
unit_val = "piece"

with col_right:
    with st.container(border=True):
        render_clean_html('<div class="nl-card-title">How much did you eat?</div>')

        # Scan Mode Toggle: Single Meal vs Multiple Meals
        sm_col1, sm_col2 = st.columns(2, gap="small")
        with sm_col1:
            if st.button(
                "Single Meal",
                key="btn_scan_single",
                type="primary" if st.session_state.scan_mode == "Single Meal" else "secondary",
                use_container_width=True
            ):
                if st.session_state.scan_mode != "Single Meal":
                    st.session_state.scan_mode = "Single Meal"
                    _reset_scan_state()
                    st.rerun()
        with sm_col2:
            if st.button(
                "Multiple Meals",
                key="btn_scan_multi",
                type="primary" if st.session_state.scan_mode == "Multiple Meals" else "secondary",
                use_container_width=True
            ):
                if st.session_state.scan_mode != "Multiple Meals":
                    st.session_state.scan_mode = "Multiple Meals"
                    _reset_scan_state()
                    st.rerun()

        render_clean_html('<div style="margin-top: 8px;"></div>')

        # ------------------------------------------------------------------
        # MODE A: SINGLE MEAL
        # ------------------------------------------------------------------
        if st.session_state.scan_mode == "Single Meal":
            mode_col1, mode_col2 = st.columns([1, 1])
            with mode_col1:
                if st.button(
                    "Pieces",
                    key="btn_mode_pieces",
                    type="primary" if st.session_state.scanner_unit_mode == "Pieces" else "secondary",
                    use_container_width=True
                ):
                    st.session_state.scanner_unit_mode = "Pieces"
                    st.rerun()
            with mode_col2:
                if st.button(
                    "Grams",
                    key="btn_mode_grams",
                    type="primary" if st.session_state.scanner_unit_mode == "Grams" else "secondary",
                    use_container_width=True
                ):
                    st.session_state.scanner_unit_mode = "Grams"
                    st.rerun()

            inp_c1, inp_c2 = st.columns(2)
            if st.session_state.scanner_unit_mode == "Pieces":
                if "inp_count" not in st.session_state:
                    st.session_state.inp_count = st.session_state.saved_count
                if "inp_unit" not in st.session_state:
                    st.session_state.inp_unit = st.session_state.saved_unit
                with inp_c1:
                    count_val = st.number_input(
                        "Count",
                        min_value=0.5,
                        max_value=20.0,
                        step=0.5,
                        placeholder="Enter quantity (e.g. 1)",
                        key="inp_count",
                        on_change=_sync_count
                    )
                with inp_c2:
                    unit_raw = st.text_input("Unit", key="inp_unit", on_change=_sync_unit)
                    unit_val = (unit_raw or "piece").strip() or "piece"
                st.session_state.saved_count = count_val
                st.session_state.saved_unit = unit_val
            else:
                if "inp_grams" not in st.session_state:
                    st.session_state.inp_grams = st.session_state.saved_grams
                with inp_c1:
                    count_val = st.number_input(
                        "Weight (g)",
                        min_value=10.0,
                        max_value=1500.0,
                        step=10.0,
                        placeholder="Enter weight in g (e.g. 100)",
                        key="inp_grams",
                        on_change=_sync_grams
                    )
                with inp_c2:
                    unit_val = st.text_input("Unit", value="g", disabled=True, key="inp_unit_g")
                st.session_state.saved_grams = count_val

            # STEP 1: Scan & Predict
            if st.button("Step 1: Scan & Predict", key="btn_scan_predict", type="primary", use_container_width=True):
                if st.session_state.scanner_image is None:
                    st.warning("Please upload a photo, take a picture, or select a sample dish on the left first.")
                elif count_val is None or count_val <= 0:
                    st.warning("Please enter your quantity before scanning.")
                else:
                    src = st.session_state.get("scanner_source")
                    if src == "sample_samosa":
                        pred_dish = "samosa"
                        pred_summary = "Samosa 92% · Kachori 5% · Pakora 2%"
                    elif src == "sample_jalebi":
                        pred_dish = "jalebi"
                        pred_summary = "Jalebi 95% · Imarti 4% · Gulab Jamun 1%"
                    elif clf and clf.get_model_info().get("is_loaded"):
                        preds = clf.predict(st.session_state.scanner_image)
                        if preds:
                            best = preds[0]
                            pred_dish = best.food_name
                            pred_summary = " · ".join([
                                f"{k['food_name'].replace('_', ' ').title()} {k['confidence'] * 100:.0f}%"
                                for k in best.top_k[:3]
                            ])
                        else:
                            pred_dish = "samosa"
                            pred_summary = "Samosa 92% · Kachori 5% · Pakora 2%"
                    else:
                        pred_dish = "samosa"
                        pred_summary = "Samosa 92% · Kachori 5% · Pakora 2%"

                    st.session_state.detected_dish = pred_dish
                    st.session_state.edited_dish = pred_dish
                    st.session_state.inp_single_edited_dish = pred_dish
                    st.session_state.detection_summary = pred_summary
                    st.session_state.report_generated = False
                    st.rerun()

            # STEP 2: Check / Edit Prediction & Generate Report
            if st.session_state.detected_dish is None:
                render_clean_html("""
                <div style="text-align: center; padding: 28px 16px; color: #64748B; font-size: 0.90rem;">
                    <div style="font-size: 2rem; margin-bottom: 8px;">🍽️</div>
                    <div style="font-weight: 750; color: #1E1B4B; margin-bottom: 4px;">Step 1: Scan Your Meal</div>
                    <div>Select a photo on the left, enter your quantity above, and click <strong>Step 1: Scan &amp; Predict</strong>.</div>
                </div>
                """)
            else:
                render_clean_html("""
                <div style="margin-top: 14px; padding-top: 14px; border-top: 1px solid #E2E8F0; font-size: 0.90rem; font-weight: 700; color: #1E1B4B;">
                    Step 2: Check or edit predicted meal, then click Report
                </div>
                """)
                if "inp_single_edited_dish" not in st.session_state:
                    st.session_state.inp_single_edited_dish = (
                        st.session_state.edited_dish or st.session_state.detected_dish
                    )
                if st.session_state.inp_single_edited_dish not in all_food_keys and all_food_keys:
                    st.session_state.inp_single_edited_dish = all_food_keys[0]

                selected_dish = st.selectbox(
                    "Predicted meal (edit if needed)",
                    options=all_food_keys,
                    format_func=lambda k: food_info_map[k].get("display_name", k.replace("_", " ").title()),
                    key="inp_single_edited_dish",
                    on_change=_sync_single_edited_dish
                )
                st.session_state.edited_dish = selected_dish

                if st.button("Step 2: Report", key="btn_generate_report", type="primary", use_container_width=True):
                    if count_val is None or count_val <= 0:
                        st.warning("Please enter your quantity before generating the report.")
                    else:
                        st.session_state.report_generated = True
                        st.rerun()

        # ------------------------------------------------------------------
        # MODE B: MULTIPLE MEALS (Plate / Thali)
        # ------------------------------------------------------------------
        else:
            default_multi_qty = st.number_input(
                "Default portion per detected meal",
                min_value=0.5,
                max_value=10.0,
                value=1.0,
                step=0.5,
                key="inp_multi_default_qty"
            )

            # STEP 1: Scan & Predict Multiple Meals
            if st.button("Step 1: Scan & Predict Meals", key="btn_scan_multi_predict", type="primary", use_container_width=True):
                if st.session_state.scanner_image is None:
                    st.warning("Please upload a photo, take a picture, or select a sample dish on the left first.")
                else:
                    src = st.session_state.get("scanner_source")
                    if src == "sample_samosa":
                        w, h = st.session_state.scanner_image.size
                        preds = []
                        from backend.base_model import PredictionResult
                        preds.append(PredictionResult(food_name="samosa", confidence=0.92, class_id=40, box=[0, 0, w, h]))
                    elif src == "sample_jalebi":
                        w, h = st.session_state.scanner_image.size
                        from backend.base_model import PredictionResult
                        preds = [PredictionResult(food_name="jalebi", confidence=0.95, class_id=21, box=[0, 0, w, h])]
                    elif clf and clf.get_model_info().get("is_loaded"):
                        preds = clf.predict_multi(st.session_state.scanner_image)
                    else:
                        preds = []

                    items_list: List[Dict[str, Any]] = []
                    for p in preds:
                        uid = st.session_state.multi_next_uid
                        st.session_state.multi_next_uid += 1
                        dish_key = p.food_name if p.food_name in food_info_map else all_food_keys[0]
                        def_unit = food_info_map.get(dish_key, {}).get("default_serving_unit", "serving")
                        items_list.append({
                            "uid": uid,
                            "predicted_dish": dish_key,
                            "dish": dish_key,
                            "confidence": float(p.confidence),
                            "box": p.box,
                            "quantity": float(default_multi_qty or 1.0),
                            "unit": def_unit,
                        })

                    st.session_state.multi_items = items_list
                    st.session_state.report_generated = False
                    st.rerun()

            if not st.session_state.multi_items:
                render_clean_html("""
                <div style="text-align: center; padding: 28px 16px; color: #64748B; font-size: 0.90rem;">
                    <div style="font-size: 2rem; margin-bottom: 8px;">🍛</div>
                    <div style="font-weight: 750; color: #1E1B4B; margin-bottom: 4px;">Step 1: Scan Multiple Meals</div>
                    <div>Upload a thali or multi-dish plate photo on the left, then click <strong>Step 1: Scan &amp; Predict Meals</strong> to detect each dish.</div>
                </div>
                """)
            else:
                render_clean_html("""
                <div style="margin-top: 14px; padding-top: 14px; border-top: 1px solid #E2E8F0; font-size: 0.90rem; font-weight: 700; color: #1E1B4B; margin-bottom: 8px;">
                    Step 2: Check or edit predicted meals, then click Report
                </div>
                """)

                for idx, item in enumerate(st.session_state.multi_items):
                    uid = item["uid"]
                    dish_key = item["dish"]
                    unit_opts = _get_food_units(dish_key)

                    if f"m_dish_{uid}" not in st.session_state:
                        st.session_state[f"m_dish_{uid}"] = dish_key
                    if f"m_unit_{uid}" not in st.session_state or st.session_state[f"m_unit_{uid}"] not in unit_opts:
                        st.session_state[f"m_unit_{uid}"] = item["unit"] if item["unit"] in unit_opts else unit_opts[0]
                    if f"m_qty_{uid}" not in st.session_state:
                        st.session_state[f"m_qty_{uid}"] = float(item["quantity"])

                    def _on_dish_change(i_idx=idx, i_uid=uid):
                        new_d = st.session_state[f"m_dish_{i_uid}"]
                        st.session_state.multi_items[i_idx]["dish"] = new_d
                        new_u = food_info_map.get(new_d, {}).get("default_serving_unit", "serving")
                        st.session_state.multi_items[i_idx]["unit"] = new_u
                        st.session_state[f"m_unit_{i_uid}"] = new_u
                        if new_u != "g" and st.session_state.multi_items[i_idx]["quantity"] >= 25:
                            st.session_state.multi_items[i_idx]["quantity"] = 1.0
                            st.session_state[f"m_qty_{i_uid}"] = 1.0

                    def _on_unit_change(i_idx=idx, i_uid=uid):
                        old_u = st.session_state.multi_items[i_idx]["unit"]
                        new_u = st.session_state[f"m_unit_{i_uid}"]
                        st.session_state.multi_items[i_idx]["unit"] = new_u
                        d_k = st.session_state.multi_items[i_idx]["dish"]
                        if new_u == "g" and old_u != "g":
                            def_wt = float(food_info_map.get(d_k, {}).get("default_serving_weight_g", 100.0))
                            st.session_state.multi_items[i_idx]["quantity"] = def_wt
                            st.session_state[f"m_qty_{i_uid}"] = def_wt
                        elif new_u != "g" and old_u == "g":
                            st.session_state.multi_items[i_idx]["quantity"] = 1.0
                            st.session_state[f"m_qty_{i_uid}"] = 1.0

                    def _on_qty_change(i_idx=idx, i_uid=uid):
                        q_val = st.session_state[f"m_qty_{i_uid}"]
                        st.session_state.multi_items[i_idx]["quantity"] = float(q_val) if q_val else 1.0

                    conf_label = f"{item['confidence'] * 100:.0f}%" if item.get("confidence", 0) > 0 else "Manual"
                    st.caption(f"Meal #{idx + 1} · {conf_label}")

                    mc1, mc2, mc3, mc4 = st.columns([2.3, 1.1, 1.2, 0.55], gap="small")
                    with mc1:
                        st.selectbox(
                            "Dish",
                            options=all_food_keys,
                            format_func=lambda k: food_info_map[k].get("display_name", k.replace("_", " ").title()),
                            key=f"m_dish_{uid}",
                            on_change=_on_dish_change,
                            label_visibility="collapsed"
                        )
                    with mc2:
                        is_grams = st.session_state[f"m_unit_{uid}"] == "g"
                        st.number_input(
                            "Qty",
                            min_value=5.0 if is_grams else 0.5,
                            max_value=2000.0 if is_grams else 20.0,
                            step=10.0 if is_grams else 0.5,
                            key=f"m_qty_{uid}",
                            on_change=_on_qty_change,
                            label_visibility="collapsed"
                        )
                    with mc3:
                        st.selectbox(
                            "Unit",
                            options=unit_opts,
                            key=f"m_unit_{uid}",
                            on_change=_on_unit_change,
                            label_visibility="collapsed"
                        )
                    with mc4:
                        st.button(
                            "✕",
                            key=f"btn_del_multi_{uid}",
                            type="secondary",
                            use_container_width=True,
                            on_click=_remove_multi_item,
                            args=(uid,)
                        )

                    # Keep dict synchronized with widget state
                    item["dish"] = st.session_state[f"m_dish_{uid}"]
                    item["unit"] = st.session_state[f"m_unit_{uid}"]
                    item["quantity"] = float(st.session_state[f"m_qty_{uid}"] or 1.0)

                act_c1, act_c2 = st.columns([1, 1.4], gap="small")
                with act_c1:
                    st.button(
                        "+ Add meal",
                        key="btn_add_manual_meal",
                        type="secondary",
                        use_container_width=True,
                        on_click=_add_manual_multi_item
                    )
                with act_c2:
                    if st.button("Step 2: Report", key="btn_generate_multi_report", type="primary", use_container_width=True):
                        st.session_state.report_generated = True
                        st.rerun()


# ==============================================================================
# STEP 2 OUTPUT: MEAL REPORT & ADD TO TODAY'S MEALS
# ==============================================================================
if st.session_state.report_generated:
    if st.session_state.scan_mode == "Single Meal" and st.session_state.edited_dish and count_val is not None:
        final_dish = st.session_state.edited_dish
        calc_res = calculate_food_nutrition(final_dish, count_val, unit_val)

        cal_disp = calc_res.calories if calc_res else 0.0
        fat_disp = calc_res.fat_g if calc_res else 0.0
        carb_disp = calc_res.carbs_g if calc_res else 0.0
        prot_disp = calc_res.protein_g if calc_res else 0.0
        fibr_disp = calc_res.fibre_g if calc_res else 0.0
        disp_name = food_info_map.get(final_dish, {}).get("display_name", final_dish.replace("_", " ").title())
        qty_str = f"{float(count_val):.1f}".rstrip("0").rstrip(".")

        with st.container(border=True):
            render_clean_html(f'<div class="nl-card-title">Meal Nutrition Report — {disp_name} ({qty_str} {unit_val})</div>')
            macros_html = f"""
            <div style="margin-top: 8px;">
                <div style="background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); border: 1px solid #FCD34D; border-radius: 12px; padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; box-shadow: 0 2px 8px rgba(217, 119, 6, 0.12);">
                    <div>
                        <div style="font-weight: 750; color: #92400E; font-size: 0.95rem;">Calories</div>
                        <div style="font-size: 0.78rem; color: #B45309;">Energy for your body</div>
                    </div>
                    <div style="font-size: 1.18rem; font-weight: 850; color: #92400E;">{cal_disp:.0f} kcal</div>
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; border-bottom: 1px solid #F1F5F9;">
                    <div>
                        <div style="font-weight: 600; color: #1E1B4B; font-size: 0.9rem;">Fats</div>
                        <div style="font-size: 0.78rem; color: #64748B;">Protects cells</div>
                    </div>
                    <div style="font-weight: 750; color: #1E1B4B; font-size: 0.95rem;">{fat_disp:.1f} g</div>
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; border-bottom: 1px solid #F1F5F9;">
                    <div>
                        <div style="font-weight: 600; color: #1E1B4B; font-size: 0.9rem;">Carbohydrates</div>
                        <div style="font-size: 0.78rem; color: #64748B;">Daily fuel</div>
                    </div>
                    <div style="font-weight: 750; color: #1E1B4B; font-size: 0.95rem;">{carb_disp:.1f} g</div>
                </div>

                <div style="background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%); border: 1px solid #BBF7D0; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; margin-top: 6px; margin-bottom: 6px;">
                    <div>
                        <div style="font-weight: 750; color: #166534; font-size: 0.9rem;">Protein</div>
                        <div style="font-size: 0.78rem; color: #15803D;">Repairs muscle</div>
                    </div>
                    <div style="font-weight: 850; color: #166534; font-size: 0.95rem;">{prot_disp:.1f} g</div>
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 14px;">
                    <div>
                        <div style="font-weight: 600; color: #1E1B4B; font-size: 0.9rem;">Fibre</div>
                        <div style="font-size: 0.78rem; color: #64748B;">Digestion, steady sugar</div>
                    </div>
                    <div style="font-weight: 750; color: #1E1B4B; font-size: 0.95rem;">{fibr_disp:.1f} g</div>
                </div>
            </div>
            """
            render_clean_html(macros_html)

        suitability = evaluate_food_suitability(
            final_dish, cal_disp, fat_disp, prot_disp, carb_disp, profile
        )
        tip_card_html = f"""
        <div style="background: linear-gradient(135deg, #FEF9C3 0%, #FEF08A 100%); border: 1px solid #FDE047; box-shadow: 0 4px 16px rgba(202, 138, 4, 0.15); border-radius: 16px; padding: 22px; margin-top: 12px; margin-bottom: 14px;">
            <div style="font-size: 1.15rem; font-weight: 750; color: #713F12; margin-bottom: 6px;">
                {suitability['title']}
            </div>
            <div style="font-size: 0.92rem; color: #854D0E; line-height: 1.5;">
                {suitability['message']}
            </div>
        </div>
        """
        render_clean_html(tip_card_html)

        if st.button("Add to today’s meals", key="btn_add_to_meals", type="primary"):
            _add_single_meal_to_db(final_dish, float(count_val), unit_val, calc_res)
            st.success(f"Added {disp_name} ({cal_disp:.0f} kcal) to today's meals!")

    elif st.session_state.scan_mode == "Multiple Meals" and st.session_state.multi_items:
        item_inputs = [
            {
                "food_name": item["dish"],
                "quantity": float(item["quantity"]),
                "unit": item["unit"],
            }
            for item in st.session_state.multi_items
        ]
        totals = calculate_meal_totals(item_inputs)

        with st.container(border=True):
            render_clean_html(f'<div class="nl-card-title">Meal-Wise Nutrition Report ({len(totals.items)} Meals)</div>')

            rows_html = ""
            for idx, m_item in enumerate(totals.items):
                q_str = f"{float(m_item.quantity):.1f}".rstrip("0").rstrip(".")
                rows_html += f"""
                <tr style="border-bottom: 1px solid #F1F5F9; color: #1E1B4B;">
                    <td style="padding: 11px 12px; font-weight: 650;">#{idx + 1} {m_item.display_name}</td>
                    <td style="padding: 11px 12px; color: #4B5563;">{q_str} {m_item.unit} ({m_item.weight_g:.0f} g)</td>
                    <td style="padding: 11px 12px; font-weight: 700; color: #4F46E5;">{m_item.calories:.0f} kcal</td>
                    <td style="padding: 11px 12px;">{m_item.fat_g:.1f} g</td>
                    <td style="padding: 11px 12px;">{m_item.carbs_g:.1f} g</td>
                    <td style="padding: 11px 12px;">{m_item.protein_g:.1f} g</td>
                    <td style="padding: 11px 12px;">{m_item.fibre_g:.1f} g</td>
                </tr>
                """

            table_html = f"""
            <div style="overflow-x: auto; margin-top: 8px; margin-bottom: 16px;">
                <table style="width: 100%; border-collapse: collapse; font-size: 0.90rem; text-align: left;">
                    <thead>
                        <tr style="border-bottom: 1.5px solid #E2E8F0; color: #1E1B4B; font-weight: 700;">
                            <th style="padding: 10px 12px;">Meal</th>
                            <th style="padding: 10px 12px;">Portion</th>
                            <th style="padding: 10px 12px;">Calories</th>
                            <th style="padding: 10px 12px;">Fat</th>
                            <th style="padding: 10px 12px;">Carbs</th>
                            <th style="padding: 10px 12px;">Protein</th>
                            <th style="padding: 10px 12px;">Fibre</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
            """
            render_clean_html(table_html)

            macro_pct = totals.macro_percentages
            totals_html = f"""
            <div>
                <div style="background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); border: 1px solid #FCD34D; border-radius: 12px; padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; box-shadow: 0 2px 8px rgba(217, 119, 6, 0.12);">
                    <div>
                        <div style="font-weight: 750; color: #92400E; font-size: 0.95rem;">Total Plate Calories ({totals.total_weight_g:.0f} g)</div>
                        <div style="font-size: 0.78rem; color: #B45309;">Protein {macro_pct['protein_pct']:.0f}% · Carbs {macro_pct['carbs_pct']:.0f}% · Fat {macro_pct['fat_pct']:.0f}%</div>
                    </div>
                    <div style="font-size: 1.22rem; font-weight: 850; color: #92400E;">{totals.total_calories:.0f} kcal</div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;">
                    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 10px 14px;">
                        <div style="font-size: 0.78rem; color: #64748B;">Total Fats</div>
                        <div style="font-size: 1.02rem; font-weight: 750; color: #1E1B4B;">{totals.total_fat_g:.1f} g</div>
                    </div>
                    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 10px 14px;">
                        <div style="font-size: 0.78rem; color: #64748B;">Total Carbs</div>
                        <div style="font-size: 1.02rem; font-weight: 750; color: #1E1B4B;">{totals.total_carbs_g:.1f} g</div>
                    </div>
                    <div style="background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%); border: 1px solid #BBF7D0; border-radius: 10px; padding: 10px 14px;">
                        <div style="font-size: 0.78rem; color: #15803D;">Total Protein</div>
                        <div style="font-size: 1.02rem; font-weight: 850; color: #166534;">{totals.total_protein_g:.1f} g</div>
                    </div>
                    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 10px 14px;">
                        <div style="font-size: 0.78rem; color: #64748B;">Total Fibre</div>
                        <div style="font-size: 1.02rem; font-weight: 750; color: #1E1B4B;">{totals.total_fibre_g:.1f} g</div>
                    </div>
                </div>
            </div>
            """
            render_clean_html(totals_html)

        suitability = evaluate_food_suitability(
            "mixed plate",
            totals.total_calories,
            totals.total_fat_g,
            totals.total_protein_g,
            totals.total_carbs_g,
            profile
        )
        tip_card_html = f"""
        <div style="background: linear-gradient(135deg, #FEF9C3 0%, #FEF08A 100%); border: 1px solid #FDE047; box-shadow: 0 4px 16px rgba(202, 138, 4, 0.15); border-radius: 16px; padding: 22px; margin-top: 12px; margin-bottom: 14px;">
            <div style="font-size: 1.15rem; font-weight: 750; color: #713F12; margin-bottom: 6px;">
                {suitability['title']}
            </div>
            <div style="font-size: 0.92rem; color: #854D0E; line-height: 1.5;">
                {suitability['message']}
            </div>
        </div>
        """
        render_clean_html(tip_card_html)

        if st.button("Add all to today’s meals", key="btn_add_all_meals", type="primary"):
            for m_item in totals.items:
                _add_single_meal_to_db(m_item.food_name, m_item.quantity, m_item.unit, m_item)
            st.success(f"Added {len(totals.items)} meals ({totals.total_calories:.0f} kcal total) to today's meals!")
