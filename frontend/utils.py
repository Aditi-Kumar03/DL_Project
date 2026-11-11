"""
NutriLens — Frontend Utilities & Shared Helpers
Provides theme styling, animated liquid background, top bar navigation,
model caching, and health evaluations.
Matches the Indigo UI/UX Design Mockups with 2030 Futuristic Aesthetics.
"""

import os
import streamlit as st
import matplotlib.pyplot as plt
from typing import Optional, Dict, Any, List

from backend.classifier import FoodClassifier
from backend.database import DB_PATH, init_db
from backend.meal_service import MealService

# Paths
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
MODEL_PATH = os.path.join(MODELS_DIR, "best_model.pt")
CLASS_NAMES_PATH = os.path.join(MODELS_DIR, "class_names.json")


def render_clean_html(html_str: str, sidebar: bool = False):
    """
    Renders raw HTML safely without Markdown indentation bugs.
    Strips leading and trailing whitespace from every line so CommonMark
    never parses indented HTML as a code block (<pre><code>).
    """
    clean_lines = [line.strip() for line in html_str.strip().splitlines()]
    cleaned = "".join(clean_lines)

    if sidebar:
        st.sidebar.markdown(cleaned, unsafe_allow_html=True)
    else:
        st.markdown(cleaned, unsafe_allow_html=True)


def apply_custom_theme():
    """
    Apply futuristic 2030 animated liquid water & shaded indigo theme for NutriLens.
    Features:
      - Complete removal of Streamlit default Deploy button & top header chrome
      - Fluid moving water-floating background animation with shifting dark/light orbs
      - Crisp architectural grid paper overlay
      - Playfair Display serif headlines (#1E1B4B)
      - Rich multi-stop gradient shaded buttons with glowing depth
      - Pure white frosted cards with purple underglow
    """
    css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;0,800;1,600&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

        /* ====================================================================
           1. HIDE ALL STREAMLIT DEFAULT HEADER & DEPLOY CHROME
           ==================================================================== */
        header[data-testid="stHeader"],
        [data-testid="stHeader"],
        .stDeployButton,
        [data-testid="stDeployButton"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        #MainMenu,
        footer {
            display: none !important;
            visibility: hidden !important;
            height: 0px !important;
            max-height: 0px !important;
            min-height: 0px !important;
            padding: 0 !important;
            margin: 0 !important;
            opacity: 0 !important;
            pointer-events: none !important;
            overflow: hidden !important;
        }

        /* Hide default Streamlit sidebar nav so users navigate primarily via TOP BAR */
        [data-testid="stSidebarNav"] {
            display: none !important;
        }

        /* ====================================================================
           2. 2030 FUTURISTIC ANIMATED WATER/LIQUID BACKGROUND & GRID CANVAS
           ==================================================================== */
        html, body {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            color: #1E1B4B !important;
            background-color: #FAF9FE !important;
        }

        /* Fluid animated liquid water gradient mesh + architectural grid directly on background */
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            color: #1E1B4B !important;
            background-color: #FAF9FE !important;
            background-image: 
                radial-gradient(circle at 18% 22%, rgba(99, 102, 241, 0.16) 0%, rgba(129, 140, 248, 0.05) 30%, transparent 60%),
                radial-gradient(circle at 82% 18%, rgba(168, 85, 247, 0.15) 0%, rgba(216, 180, 254, 0.05) 30%, transparent 60%),
                radial-gradient(circle at 50% 80%, rgba(56, 189, 248, 0.12) 0%, rgba(99, 102, 241, 0.04) 30%, transparent 60%),
                radial-gradient(circle at 75% 65%, rgba(139, 92, 246, 0.14) 0%, transparent 50%),
                radial-gradient(circle at 25% 70%, rgba(192, 132, 252, 0.10) 0%, transparent 50%),
                linear-gradient(to right, rgba(99, 102, 241, 0.055) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(99, 102, 241, 0.055) 1px, transparent 1px) !important;
            background-size: 150% 150%, 150% 150%, 150% 150%, 140% 140%, 140% 140%, 32px 32px, 32px 32px !important;
            background-attachment: fixed !important;
            animation: floatingWaterMesh 18s ease-in-out infinite alternate !important;
        }

        @keyframes floatingWaterMesh {
            0% {
                background-position: 0% 0%, 100% 0%, 50% 100%, 80% 80%, 20% 70%, 0 0, 0 0;
            }
            33% {
                background-position: 25% 15%, 75% 20%, 35% 85%, 65% 65%, 35% 80%, 0 0, 0 0;
            }
            66% {
                background-position: 10% 30%, 90% 10%, 65% 75%, 85% 60%, 15% 60%, 0 0, 0 0;
            }
            100% {
                background-position: 20% 5%, 80% 25%, 45% 90%, 70% 75%, 30% 65%, 0 0, 0 0;
            }
        }

        /* Streamlit Main Container Spacing — Prominently starts right at the top */
        .block-container {
            position: relative !important;
            z-index: 10 !important;
            padding-top: 1.2rem !important;
            padding-bottom: 3.5rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 1120px !important;
            margin: 0 auto !important;
        }

        /* ====================================================================
           3. TOP NAVIGATION BAR & BRAND LOGO
           ==================================================================== */
        .brand-logo-text {
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            font-size: 1.52rem !important;
            font-weight: 850 !important;
            color: #1E1B4B !important;
            letter-spacing: -0.035em !important;
            line-height: 1 !important;
            display: flex !important;
            align-items: center !important;
            white-space: nowrap !important;
        }
        .brand-logo-text a {
            color: #1E1B4B !important;
            text-decoration: none !important;
        }

        /* Active Selected Tab Pill: Guaranteed vibrant shaded purple with highlight */
        .active-nav-pill {
            background: linear-gradient(135deg, #6366F1 0%, #4F46E5 55%, #3730A3 100%) !important;
            color: #FFFFFF !important;
            font-weight: 650 !important;
            font-size: 0.88rem !important;
            border-radius: 9999px !important;
            padding: 7px 18px !important;
            text-align: center !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-shadow: 
                inset 0 1px 1px rgba(255, 255, 255, 0.4),
                0 4px 16px rgba(79, 70, 229, 0.45) !important;
            white-space: nowrap !important;
            letter-spacing: 0.01em !important;
            min-height: 36px !important;
            cursor: default !important;
        }

        /* Inactive Top Nav Link */
        [data-testid="stPageLink-NavLink"] {
            background: transparent !important;
            border: none !important;
            border-radius: 9999px !important;
            padding: 6px 12px !important;
            box-shadow: none !important;
            transition: all 0.16s ease !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
            min-height: 36px !important;
        }
        [data-testid="stPageLink-NavLink"] a {
            color: #4B5563 !important;
            font-size: 0.88rem !important;
            font-weight: 500 !important;
            text-decoration: none !important;
            white-space: nowrap !important;
        }
        [data-testid="stPageLink-NavLink"]:hover {
            background: rgba(79, 70, 229, 0.09) !important;
        }
        [data-testid="stPageLink-NavLink"]:hover a {
            color: #1E1B4B !important;
        }

        /* Top BMI Pill Badge */
        .top-bmi-wrapper {
            display: flex !important;
            justify-content: flex-end !important;
            align-items: center !important;
            width: 100% !important;
        }
        .top-bmi-pill {
            font-size: 0.82rem !important;
            font-weight: 650 !important;
            padding: 6px 16px !important;
            border-radius: 9999px !important;
            display: inline-block !important;
            white-space: nowrap !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
        }
        .top-bmi-pill-active {
            background: linear-gradient(135deg, #EDE9FE 0%, #DDD6FE 100%) !important;
            color: #4338CA !important;
            border: 1px solid #C4B5FD !important;
            box-shadow: 0 2px 8px rgba(99, 102, 241, 0.18) !important;
        }
        .top-bmi-pill-empty {
            background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%) !important;
            color: #64748B !important;
            border: 1px solid #E2E8F0 !important;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04) !important;
        }

        /* ====================================================================
           4. HEADLINES, SUBTITLES & CARDS
           ==================================================================== */
        .nl-headline {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 2.35rem;
            font-weight: 700;
            color: #1E1B4B;
            margin-top: 0.2rem;
            margin-bottom: 0.4rem;
            line-height: 1.2;
            letter-spacing: -0.015em;
        }
        .nl-subtitle {
            font-size: 1rem;
            color: #64748B;
            font-weight: 400;
            margin-bottom: 1.8rem;
            line-height: 1.5;
        }
        .nl-date-header {
            font-size: 0.88rem;
            color: #64748B;
            font-weight: 500;
            margin-bottom: 0.2rem;
        }

        /* Card Containers with Frosted Glass Edge & Purple Ambient Underglow */
        .nl-card,
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255, 255, 255, 0.96) !important;
            backdrop-filter: blur(12px) !important;
            border-radius: 18px !important;
            border: 1px solid rgba(224, 231, 255, 0.75) !important;
            box-shadow: 
                0 10px 30px -4px rgba(79, 70, 229, 0.07),
                0 4px 12px -2px rgba(99, 102, 241, 0.04),
                inset 0 1px 0 rgba(255, 255, 255, 0.9) !important;
            padding: 24px !important;
            margin-bottom: 18px !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"] > div {
            border: none !important;
            padding: 0 !important;
        }

        .nl-card-title {
            font-size: 1.12rem;
            font-weight: 700;
            color: #1E1B4B;
            margin-bottom: 0.75rem;
        }
        .nl-card-desc {
            font-size: 0.88rem;
            color: #64748B;
            line-height: 1.5;
            margin-bottom: 1.2rem;
        }

        /* Shaded Pill Tags */
        .nl-pill {
            display: inline-block;
            border-radius: 9999px;
            padding: 4px 12px;
            font-size: 0.78rem;
            font-weight: 650;
            margin-bottom: 8px;
        }
        .nl-pill-step1 {
            background: linear-gradient(135deg, #EDE9FE 0%, #DDD6FE 100%) !important;
            color: #4338CA !important;
            border: 1px solid #C4B5FD !important;
            box-shadow: 0 2px 6px rgba(99, 102, 241, 0.12) !important;
        }
        .nl-pill-step2 {
            background: linear-gradient(135deg, #E0F2FE 0%, #BAE6FD 100%) !important;
            color: #0369A1 !important;
            border: 1px solid #7DD3FC !important;
            box-shadow: 0 2px 6px rgba(2, 132, 199, 0.12) !important;
        }

        /* ====================================================================
           5. SHADED GRADIENT BUTTONS (2030 FUTURISTIC DEPTH)
           ==================================================================== */
        .stButton>button {
            border-radius: 9999px !important;
            font-weight: 650 !important;
            font-size: 0.92rem !important;
            transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1) !important;
            padding: 0.55rem 1.6rem !important;
            letter-spacing: 0.015em !important;
            border: none !important;
        }

        /* Primary Button: Multi-stop rich shaded royal purple gradient */
        .stButton>button[kind="primary"] {
            background: linear-gradient(135deg, #6366F1 0%, #4F46E5 50%, #3730A3 100%) !important;
            color: #FFFFFF !important;
            box-shadow: 
                inset 0 1px 1px rgba(255, 255, 255, 0.35),
                0 6px 20px -2px rgba(79, 70, 229, 0.45),
                0 2px 6px rgba(0, 0, 0, 0.06) !important;
        }
        .stButton>button[kind="primary"]:hover {
            background: linear-gradient(135deg, #4F46E5 0%, #4338CA 55%, #312E81 100%) !important;
            box-shadow: 
                inset 0 1px 1px rgba(255, 255, 255, 0.45),
                0 8px 25px -2px rgba(79, 70, 229, 0.58),
                0 3px 8px rgba(0, 0, 0, 0.1) !important;
            transform: translateY(-2px) scale(1.01) !important;
        }
        .stButton>button[kind="primary"]:active {
            transform: translateY(0px) scale(0.98) !important;
        }

        /* Secondary Button: Soft shaded lilac gradient */
        .stButton>button[kind="secondary"] {
            background: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 60%, #DDD6FE 100%) !important;
            border: 1px solid #C4B5FD !important;
            color: #4338CA !important;
            box-shadow: 
                inset 0 1px 1px rgba(255, 255, 255, 0.6),
                0 3px 10px rgba(99, 102, 241, 0.12) !important;
        }
        .stButton>button[kind="secondary"]:hover {
            background: linear-gradient(135deg, #EDE9FE 0%, #DDD6FE 100%) !important;
            border-color: #A5B4FC !important;
            color: #3730A3 !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.2) !important;
        }

        /* ====================================================================
           6. FORM FIELDS, UPLOADER, EXPANDERS & DROPDOWNS (THEME MATCH)
           ==================================================================== */
        :root, .stApp {
            color-scheme: light !important;
        }

        /* Widget labels & captions */
        [data-testid="stWidgetLabel"],
        [data-testid="stWidgetLabel"] label,
        [data-testid="stWidgetLabel"] p,
        [data-testid="stWidgetLabel"] span {
            color: #334155 !important;
            font-weight: 600 !important;
        }
        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] * {
            color: #64748B !important;
        }

        /* Text, Number, TextArea & Date input boxes (single unified outer border) */
        [data-testid="stNumberInputContainer"],
        [data-testid="stTextInputRootElement"],
        [data-testid="stTextAreaRootElement"],
        [data-testid="stDateInput"] > div > div,
        [data-testid="stTimeInput"] > div > div {
            background: linear-gradient(135deg, #FFFFFF 0%, #F5F3FF 100%) !important;
            background-color: #F8F7FF !important;
            border: 1.5px solid #C7D2FE !important;
            border-radius: 12px !important;
            color: #1E1B4B !important;
            box-shadow: inset 0 1px 2px rgba(79, 70, 229, 0.05) !important;
        }
        [data-testid="stNumberInputContainer"] div[data-baseweb="input"],
        [data-testid="stNumberInputContainer"] div[data-baseweb="base-input"],
        [data-testid="stTextInputRootElement"] div[data-baseweb="input"],
        [data-testid="stTextInputRootElement"] div[data-baseweb="base-input"],
        [data-testid="stTextAreaRootElement"] div[data-baseweb="base-input"],
        [data-testid="stTextAreaRootElement"] div[data-baseweb="textarea"] {
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        [data-testid="stNumberInputContainer"]:focus-within,
        [data-testid="stTextInputRootElement"]:focus-within,
        [data-testid="stTextAreaRootElement"]:focus-within,
        [data-testid="stDateInput"] > div > div:focus-within {
            border-color: #6366F1 !important;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.16) !important;
        }
        div[data-baseweb="input"] input,
        div[data-baseweb="base-input"] input,
        div[data-baseweb="textarea"] textarea,
        [data-testid="stNumberInputField"] {
            background-color: transparent !important;
            color: #1E1B4B !important;
            -webkit-text-fill-color: #1E1B4B !important;
            caret-color: #4F46E5 !important;
            border-radius: 10px !important;
        }
        div[data-baseweb="input"] input::placeholder,
        div[data-baseweb="textarea"] textarea::placeholder {
            color: #94A3B8 !important;
            -webkit-text-fill-color: #94A3B8 !important;
        }
        [data-testid="stTextInputRootElement"]:has(input:disabled),
        [data-testid="stNumberInputContainer"]:has(input:disabled) {
            background: #F1F5F9 !important;
            background-color: #F1F5F9 !important;
            border-color: #CBD5E1 !important;
            opacity: 1 !important;
        }
        div[data-baseweb="input"] input:disabled,
        div[data-baseweb="base-input"] input:disabled {
            color: #475569 !important;
            -webkit-text-fill-color: #475569 !important;
            opacity: 1 !important;
        }

        /* Number input +/- stepper buttons */
        [data-testid="stNumberInputStepDown"],
        [data-testid="stNumberInputStepUp"] {
            background-color: transparent !important;
            color: #4F46E5 !important;
            border-color: #E0E7FF !important;
        }
        [data-testid="stNumberInputStepDown"]:hover,
        [data-testid="stNumberInputStepUp"]:hover {
            background-color: #EDE9FE !important;
            color: #312E81 !important;
        }
        [data-testid="stNumberInputIcon"],
        [data-testid="stNumberInputIcon"] svg {
            color: #4F46E5 !important;
        }

        /* Selectbox & MultiSelect boxes + dropdown popup menu */
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stMultiSelect"] div[data-baseweb="select"] > div {
            background: linear-gradient(135deg, #FFFFFF 0%, #F5F3FF 100%) !important;
            background-color: #F8F7FF !important;
            border: 1.5px solid #C7D2FE !important;
            border-radius: 12px !important;
            color: #1E1B4B !important;
            box-shadow: inset 0 1px 2px rgba(79, 70, 229, 0.05) !important;
        }
        [data-testid="stSelectbox"] div[data-baseweb="select"] span,
        [data-testid="stSelectbox"] div[data-baseweb="select"] div,
        [data-testid="stSelectbox"] div[data-baseweb="select"] input,
        [data-testid="stMultiSelect"] div[data-baseweb="select"] input {
            color: #1E1B4B !important;
            background-color: transparent !important;
        }
        [data-testid="stSelectbox"] svg,
        [data-testid="stMultiSelect"] svg {
            color: #4F46E5 !important;
        }
        div[data-baseweb="popover"],
        div[data-baseweb="popover"] > div,
        div[data-baseweb="menu"],
        [data-testid="stSelectboxVirtualDropdown"],
        ul[role="listbox"] {
            background-color: #FFFFFF !important;
            color: #1E1B4B !important;
            border: 1px solid #C7D2FE !important;
            border-radius: 12px !important;
            box-shadow: 0 10px 28px rgba(79, 70, 229, 0.14) !important;
        }
        ul[role="listbox"] li,
        [role="option"],
        div[data-baseweb="menu"] li {
            background-color: #FFFFFF !important;
            color: #1E1B4B !important;
        }
        [role="option"]:hover,
        [role="option"][aria-selected="true"],
        div[data-baseweb="menu"] li:hover {
            background-color: #EDE9FE !important;
            color: #3730A3 !important;
        }

        /* File Uploader dropzone, uploaded file chips & Camera input */
        [data-testid="stFileUploader"],
        [data-testid="stFileUploader"] > div {
            color: #1E1B4B !important;
        }
        [data-testid="stFileUploaderDropzone"] {
            background: linear-gradient(135deg, #FFFFFF 0%, #F5F3FF 100%) !important;
            background-color: #F8F7FF !important;
            border: 1.5px dashed #A5B4FC !important;
            border-radius: 14px !important;
            color: #1E1B4B !important;
        }
        [data-testid="stFileUploaderDropzone"]:hover {
            background: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%) !important;
            border-color: #6366F1 !important;
        }
        [data-testid="stFileUploaderDropzoneInstructions"],
        [data-testid="stFileUploaderDropzoneInstructions"] span,
        [data-testid="stFileUploaderDropzone"] span,
        [data-testid="stFileUploaderDropzone"] small {
            color: #475569 !important;
        }
        [data-testid="stFileUploaderDropzone"] svg {
            color: #6366F1 !important;
        }
        [data-testid="stFileUploaderDropzone"] button,
        [data-testid="stCameraInputButton"],
        [data-testid="stCameraInputSwitchButton"] {
            background: linear-gradient(135deg, #EDE9FE 0%, #DDD6FE 100%) !important;
            border: 1px solid #C4B5FD !important;
            color: #3730A3 !important;
            border-radius: 9999px !important;
            font-weight: 650 !important;
        }
        [data-testid="stFileUploaderDropzone"] button:hover,
        [data-testid="stCameraInputButton"]:hover {
            background: linear-gradient(135deg, #DDD6FE 0%, #C4B5FD 100%) !important;
            color: #1E1B4B !important;
        }
        [data-testid="stFileChip"],
        [data-testid="stFile"] {
            background: #EDE9FE !important;
            background-color: #EDE9FE !important;
            border: 1px solid #C4B5FD !important;
            border-radius: 10px !important;
            color: #1E1B4B !important;
        }
        [data-testid="stFileChip"] span,
        [data-testid="stFileChip"] small,
        [data-testid="stFileChipName"],
        [data-testid="stFileName"],
        [data-testid="stFile"] span,
        [data-testid="stFile"] small {
            color: #1E1B4B !important;
        }
        [data-testid="stFileUploaderDropzone"] [data-testid="stFileChipDeleteBtn"] button,
        [data-testid="stFileChipDeleteBtn"] button {
            background: transparent !important;
            border: none !important;
            color: #4338CA !important;
        }
        [data-testid="stFileUploaderDropzone"] [data-testid="stFileChipDeleteBtn"] button:hover,
        [data-testid="stFileChipDeleteBtn"] button:hover {
            background: rgba(99, 102, 241, 0.14) !important;
            color: #1E1B4B !important;
        }
        [data-testid="stFileChipDeleteBtn"] svg {
            color: #4338CA !important;
        }
        [data-testid="stCameraInputWebcamStyledBox"] {
            background-color: #F5F3FF !important;
            border: 1.5px solid #C7D2FE !important;
            border-radius: 14px !important;
            color: #1E1B4B !important;
        }

        /* Expander header & body (Thali crop box) */
        [data-testid="stExpander"] details {
            background: rgba(255, 255, 255, 0.94) !important;
            border: 1px solid #C7D2FE !important;
            border-radius: 14px !important;
            overflow: hidden !important;
        }
        [data-testid="stExpander"] summary {
            background: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%) !important;
            color: #1E1B4B !important;
            font-weight: 600 !important;
        }
        [data-testid="stExpander"] summary:hover {
            background: linear-gradient(135deg, #EDE9FE 0%, #E0E7FF 100%) !important;
            color: #3730A3 !important;
        }
        [data-testid="stExpander"] summary p,
        [data-testid="stExpander"] summary span {
            color: #1E1B4B !important;
        }
        [data-testid="stExpander"] summary svg,
        [data-testid="stExpanderIcon"] {
            color: #4F46E5 !important;
        }
        [data-testid="stExpanderDetails"] {
            background-color: #FFFFFF !important;
            color: #1E1B4B !important;
        }
    </style>
    """
    render_clean_html(css)


def render_top_navigation(current_page: str, user_profile: Optional[Dict[str, Any]] = None):
    """
    Renders top navigation header matching PDF mockups across all 6 pages:
    NutriLens (Left) | Home · Dashboard · Food Scanner · Health Profile · Meal History · Nutrition DB (Center) | BMI Pill (Right)
    Dynamically renders active pill with guaranteed shaded purple gradient, while inactive links are clickable.
    """
    tabs_data = [
        ("Home", "app.py"),
        ("Dashboard", "pages/1_Dashboard.py"),
        ("Food Scanner", "pages/2_Food_Scanner.py"),
        ("Health Profile", "pages/3_Health_Profile.py"),
        ("Meal History", "pages/4_Meal_History.py"),
        ("Nutrition DB", "pages/5_Nutrition_Database.py"),
    ]

    if user_profile and user_profile.get("bmi") is not None:
        bmi_val = float(user_profile.get("bmi", 22.0))
        bmi_cat = (user_profile.get("bmi_category") or "Healthy").split("(")[0].strip()
        pill_html = f'<span class="top-bmi-pill top-bmi-pill-active">BMI {bmi_val:.1f} · {bmi_cat}</span>'
    else:
        pill_html = '<span class="top-bmi-pill top-bmi-pill-empty">No Profile Yet</span>'

    c_logo, c_nav1, c_nav2, c_nav3, c_nav4, c_nav5, c_nav6, c_status = st.columns(
        [1.8, 0.95, 1.15, 1.4, 1.4, 1.3, 1.3, 2.5],
        gap="small",
        vertical_alignment="center"
    )

    with c_logo:
        logo_html = '<div class="brand-logo-text"><a href="/" target="_self">NutriLens</a></div>'
        render_clean_html(logo_html)

    nav_cols = [c_nav1, c_nav2, c_nav3, c_nav4, c_nav5, c_nav6]
    for col, (label, path) in zip(nav_cols, tabs_data):
        with col:
            if current_page.lower() == label.lower():
                # Active tab: guaranteed vibrant shaded purple pill!
                render_clean_html(f'<div class="active-nav-pill">{label}</div>')
            else:
                st.page_link(path, label=label, use_container_width=True)

    with c_status:
        status_html = f'<div class="top-bmi-wrapper">{pill_html}</div>'
        render_clean_html(status_html)

    render_clean_html('<div style="margin-bottom: 22px;"></div>')


def evaluate_food_suitability(
    food_name: str,
    calories: float,
    fat_g: float,
    protein_g: float,
    carbs_g: float,
    profile: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """
    Evaluates food suitability with supportive, human advice.
    Matches PDF tone: 'Your BMI is 26.2. This samosa is high in fat, so a half portion with a fresh cucumber salad would suit your goal better.'
    """
    display_title = food_name.replace("_", " ").title()

    if not profile or profile.get("bmi") is None:
        return {
            "status": "info",
            "title": "Set up your Health Profile",
            "message": f"This portion of {display_title.lower()} provides {calories:.0f} kcal and {fat_g:.1f}g fat. Set up your Health Profile to get advice tailored to your personal BMI and calorie goal.",
            "recommendation": "Go to Health Profile to enter your height & weight."
        }

    bmi = float(profile.get("bmi", 22.0))
    bmi_cat = (profile.get("bmi_category") or "Healthy").split("(")[0].strip()

    is_high_fat = fat_g >= 12.0
    is_high_cal = calories >= 320.0

    if bmi >= 23.0:
        if is_high_fat or is_high_cal:
            issue = "high in fat" if is_high_fat else "higher in calories"
            return {
                "status": "caution",
                "title": "Be a little mindful",
                "message": f"Your BMI is {bmi:.1f}. This {display_title.lower()} is {issue}, so a half portion with a fresh cucumber salad would suit your goal better.",
                "recommendation": "Consider pairing with fresh salad or curd to balance satiety."
            }
        else:
            return {
                "status": "good",
                "title": "Great choice!",
                "message": f"Your BMI is {bmi:.1f}. This {display_title.lower()} is moderate in calories and controlled in fat, fitting well into your daily goal.",
                "recommendation": "Great balanced choice for your plate today."
            }
    elif bmi < 18.5:
        return {
            "status": "nourish",
            "title": "Nourishing choice",
            "message": f"Your BMI is {bmi:.1f}. This provides good sustained energy ({calories:.0f} kcal) and nourishment to build healthy weight.",
            "recommendation": "Add a cup of curd or handful of nuts for healthy protein."
        }
    else:
        return {
            "status": "good",
            "title": "Well balanced",
            "message": f"Your BMI is {bmi:.1f}. This meal fits comfortably into your daily energy targets.",
            "recommendation": "Enjoy your food mindfully!"
        }


@st.cache_resource(show_spinner="Loading NutriLens deep learning model...")
def _load_classifier_cached() -> Optional[FoodClassifier]:
    """
    Cached model loader. Loads weights from models/best_model.pt
    """
    try:
        init_db()
        if os.path.exists(MODEL_PATH) and os.path.exists(CLASS_NAMES_PATH):
            clf = FoodClassifier(
                model_path=MODEL_PATH,
                class_names_path=CLASS_NAMES_PATH,
                architecture="mobilenet_v2"
            )
            return clf
        else:
            return None
    except Exception as e:
        st.error(f"Error loading classification model: {e}")
        return None


def get_cached_classifier() -> Optional[FoodClassifier]:
    """Return cached classifier, reloading backend module if stale in Streamlit."""
    clf = _load_classifier_cached()
    if clf is not None and not hasattr(clf, "predict_multi"):
        import importlib
        import backend.classifier as _clf_mod
        importlib.reload(_clf_mod)
        globals()["FoodClassifier"] = _clf_mod.FoodClassifier
        _load_classifier_cached.clear()
        clf = _load_classifier_cached()
    return clf


def get_meal_service() -> MealService:
    """Helper to obtain MealService instance (reloading backend module if stale in Streamlit)."""
    if not hasattr(MealService, "add_meal_entry"):
        import importlib
        import backend.meal_service as _meal_service_mod
        importlib.reload(_meal_service_mod)
        globals()["MealService"] = _meal_service_mod.MealService
    return MealService(db_path=DB_PATH)
