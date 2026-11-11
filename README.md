# NutriLens — Indian Food Recognition & Nutrition Tracker

NutriLens is a deep learning web application that identifies Indian dishes from food photos, estimates calories and macronutrients, and tracks your daily nutrition against personalized health goals.

It combines a PyTorch computer vision classifier (**43 Indian food classes**), region-proposal multi-dish detection for thalis/plates, verified **IFCT 2017 (ICMR-NIN)** nutritional data stored in SQLite, and standard metabolic formulas (**BMI**, **Mifflin-St Jeor BMR**, and **TDEE**).

---

## How It Works

The app has a 6-page Streamlit interface:

1. **Home** (`frontend/app.py`) — Overview, daily calorie progress snapshot, and supported dish list.
2. **Dashboard** (`frontend/pages/1_Dashboard.py`) — Today's calorie target ring, macro breakdown (Protein, Carbs, Fat, Fibre), energy balance, and logged meals.
3. **Food Scanner** (`frontend/pages/2_Food_Scanner.py`) — Supports both **Single Meal** and **Multiple Meals** (plate / thali):
   - Upload a photo, take one with your camera, or try built-in sample dishes (`Samosa`, `Jalebi`), with an optional crop tool for focusing on a single bowl.
   - **Step 1 — Scan & Predict**: Enter portion quantity (single meal) or scan a multi-dish plate to detect dishes and display predicted labels right above your photo.
   - **Step 2 — Review, Edit & Report**: Correct any predicted dish, adjust quantities/units, or add/remove items on a multi-dish plate, then click **Report** to view the nutrition breakdown, BMI suitability advice, and log meals to your daily tracker.
4. **Health Profile** (`frontend/pages/3_Health_Profile.py`) — Calculates BMI (with Asian-Indian ICMR-NIN categories), BMR, TDEE, and daily calorie goals (Maintain, Lose Weight, or Gain Weight).
5. **Meal History** (`frontend/pages/4_Meal_History.py`) — Filterable date-range logs, 7-day calorie chart, daily averages, and meal deletion.
6. **Nutrition DB** (`frontend/pages/5_Nutrition_Database.py`) — Searchable database of 43 Indian dishes, serving unit weights (`piece`, `roti`, `bowl`, `plate`, `g`, etc.), and custom entry support.

---

## Quick Start (Run Locally)

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.13)
- Dependencies listed in `requirements.txt` (optional: `opencv-python` improves contour-based food region detection in Multiple Meals mode; otherwise the scanner falls back to structured grid crops).

### 2. Install Dependencies

Open PowerShell or Terminal in the project root folder:

```powershell
# Optional: create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\activate
```

Install PyTorch and app packages:
- **With NVIDIA GPU (CUDA 12.4):**
  ```powershell
  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
  pip install -r requirements.txt
  ```
- **CPU Only:**
  ```powershell
  pip install -r requirements.txt
  ```

### 3. Launch the App

```powershell
python -m streamlit run frontend/app.py
```

Then open `http://localhost:8501` in your browser.

---

## Project Structure

```text
DL_CAPSTONE/
├── .streamlit/
│   └── config.toml                        # Light indigo theme settings
├── backend/
│   ├── base_model.py                      # Abstract model interface & PredictionResult dataclass
│   ├── classifier.py                      # PyTorch food classifier (single, cropped & multi-region)
│   ├── database.py                        # SQLite schema & 43-dish IFCT 2017 seed data
│   ├── detector.py                        # Extensible detection adapter
│   ├── health_calculator.py               # BMI, Mifflin-St Jeor BMR, TDEE & target calories
│   ├── meal_service.py                    # Meal logging, daily totals, history & user profile CRUD
│   └── nutrition_engine.py                # Serving-unit scaling & macro totals calculation
├── data/
│   ├── nutrition.db                       # Local SQLite database (foods, units, profile, meal logs)
│   ├── dataset_exploration_summary.json   # Phase 1 dataset audit summary
│   └── evaluation_metrics.json            # Baseline MobileNetV2 test evaluation metrics
├── frontend/
│   ├── app.py                             # Home page
│   ├── utils.py                           # Shared theme CSS, navigation bar, BMI advice & caching
│   └── pages/
│       ├── 1_Dashboard.py
│       ├── 2_Food_Scanner.py
│       ├── 3_Health_Profile.py
│       ├── 4_Meal_History.py
│       └── 5_Nutrition_Database.py
├── models/
│   ├── best_model.pt                      # Trained PyTorch ResNet50 checkpoint (43 classes)
│   ├── class_names.json                   # 43 Indian food class names & index mapping
│   ├── model_config.json                  # Training specs, 224x224 input & ImageNet normalization
│   └── version.json                       # Model metadata manifest
├── notebooks/                             # Colab / Jupyter training & evaluation workflow
│   ├── 01_dataset_exploration.ipynb       # Dataset audit (SohlHealth/enhanced-indian-food-classification)
│   ├── 02_preprocessing.ipynb             # Stratified 70/15/15 split, class weights & augmentations
│   ├── 03_model_training.ipynb            # Transfer learning (MobileNetV2 & ResNet50) with AMP
│   └── 04_model_evaluation.ipynb          # Holdout evaluation, confusion matrix & artifact export
├── sample_images/                         # Built-in test photos (samosa.jpg, jalebi.jpg, R.jpg)
├── requirements.txt
└── README.md
```

---

## Model & Training Overview

- **Dataset:** `SohlHealth/enhanced-indian-food-classification` (15,404 images across **43 Indian food classes**, re-split 70% train / 15% validation / 15% test with inverse class weighting).
- **Production Weights (`models/best_model.pt`):** Fine-tuned **ResNet50** (90.32 MB) achieving **93.68% Top-1** and **99.05% Top-5** validation accuracy at checkpoint export (`224x224` RGB inputs).
- **Baseline Benchmark (`data/evaluation_metrics.json`):** Comparison **MobileNetV2** holdout test evaluation across 2,311 images achieved **81.45% Top-1**, **94.32% Top-5**, and **0.8092 macro-F1**.
- **Training Pipeline:** Self-contained notebooks in `notebooks/` cover exploration, stratified preprocessing, mixed-precision transfer learning, and evaluation.

---

## Nutritional Source & Disclaimer

Nutritional values per 100g and household serving weights are referenced from the **Indian Food Composition Tables (IFCT 2017)** by ICMR-NIN.

> **Disclaimer:** NutriLens provides calorie, nutrient, BMI, BMR, and TDEE estimates for informational and personal tracking use only. It is not medical or clinical dietary advice.
