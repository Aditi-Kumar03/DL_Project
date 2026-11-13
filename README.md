#  NutriLens AI — Indian Food Recognition & Clinical Dietary Intelligence

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C.svg)](https://pytorch.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg)](https://streamlit.io/)
[![Architecture](https://img.shields.io/badge/Model-ResNet50%20%7C%20MobileNetV2-8A2BE2.svg)](#model-architecture--benchmarks)
[![Accuracy](https://img.shields.io/badge/Top--1%20Val%20Acc-93.68%25-brightgreen.svg)](#model-architecture--benchmarks)
[![Accuracy](https://img.shields.io/badge/Top--5%20Val%20Acc-99.05%25-green.svg)](#model-architecture--benchmarks)
[![Nutritional Standard](https://img.shields.io/badge/Nutrition-ICMR--NIN%20IFCT%202017-0A66C2.svg)](#nutritional-intelligence-engine)

> **NutriLens AI** is an end-to-end computer vision and dietary health intelligence web platform built specifically for authentic Indian cuisine. It combines transfer learning on 50-layer deep residual networks (**ResNet-50**), heuristic multi-dish "Thali" segmentation, verified national dietary data (**ICMR-NIN IFCT 2017**), and Asian-Indian metabolic risk scoring into a real-time full-stack web application.

---
website link: https://nutrilens-food-ai.streamlit.app/

## The Project Story (STAR Framework)

For recruiters, engineers, and researchers, this project demonstrates real-world machine learning engineering: moving from raw, messy data and complex visual problems to an audited, robust, and deployed production application.

```
       SITUATION                    TASK                     ACTION                    RESULT
┌──────────────────────┐   ┌──────────────────────┐   ┌──────────────────────┐   ┌──────────────────────┐
│ Global food apps fail│   │ Build an end-to-end  │   │ Audit & re-stratify  │   │ 93.68% Top-1 Accuracy│
│ on Indian cuisine    │──▶│ AI system for 43     │──▶│ dataset; train       │──▶│ 99.05% Top-5 Accuracy│
│ (gravy ambiguity, raw│   │ Indian dishes, thalis│   │ ResNet50; integrate  │   │ <35 ms CPU inference │
│ vs cooked bias, BMI).│   │ & clinical nutrition.│   │ IFCT 2017 in SQLite. │   │ Live on Streamlit.   │
└──────────────────────┘   └──────────────────────┘   └──────────────────────┘   └──────────────────────┘
```

### 1. Situation: Why Indian Food Tracking is Fundamentally Broken
Most popular commercial diet apps (MyFitnessPal, HealthifyMe, Lose It!) are architected around Western eating habits:
* **The "Raw vs. Cooked" Caloric Distortion:** Generic food databases record raw agricultural weights. For example, 100g of raw rice is ~355 kcal, whereas 100g of cooked steamed rice is ~130 kcal because starch expands with water. When users log cooked meals against raw USDA databases, calories are overestimated by up to **$3\times$**!
* **Visual Ambiguity in Gravies:** Indian cooking relies on complex blended gravies (onion-tomato, cashew-cream, spinach). To a computer, *Dal Makhani* looks almost identical to *Rajma*, and *Shahi Paneer* looks identical to *Kadai Paneer*.
* **The Composite Plate Problem (Thali):** Indians rarely eat isolated, single items; meals are served as composite *Thalis* (a platter with 3 to 6 bowls of dal, sabzi, roti, and rice). Single-label image classifiers fail completely on composite plates.
* **Western BMI Cutoff Bias:** Standard WHO guidelines classify overweight at $\text{BMI} \ge 25\text{ kg/m}^2$. However, South Asians exhibit the **"Thin-Fat Phenotype"** (high visceral body fat and high insulin resistance at lower body mass index). Using Western BMI underestimates metabolic and cardiovascular disease risks in Indians.

---

### 2. Task: Engineering Goals
To solve these challenges, we set out to build **NutriLens AI**:
1. **Curate and Audit an Authentic Dataset:** Train on genuine Indian food images across 43 diverse categories instead of Western benchmarks like `Food-101`.
2. **Train a High-Accuracy Deep Classifier:** Overcome severe inter-class visual similarity using deep feature extraction and cost-sensitive loss.
3. **Engineered Multi-Dish Thali Detection:** Detect and isolate multiple food items on a single plate without requiring expensive manual bounding-box annotations.
4. **Culturally Grounded Nutritional Intelligence:** Map all predictions to official **ICMR-NIN IFCT 2017** tables with household portion scaling (katori, roti, piece $\to$ grams).
5. **Clinical Metabolic Engine:** Implement Asian-Indian specific BMI classifications ($\ge 23\text{ kg/m}^2$ risk cutoff) and Mifflin-St Jeor Total Daily Energy Expenditure (TDEE) tracking in a production-ready, interactive UI.

---

### 3. Action: Technical Implementation & Architecture

#### A. Data Engineering & Upstream Audit
We adopted the **Enhanced Indian Food Classification Dataset** (`SohlHealth/enhanced-indian-food-classification`) containing **15,404 images across 43 classes**. During our Phase 1 exploratory data audit, we uncovered two critical flaws:
* **The Missing Class Bug:** The upstream dataset's official validation and test folders had **21 out of 43 classes completely missing** (zero images). Training naively on these splits would cause catastrophic evaluation failure.
* **Severe Class Imbalance:** Sample distribution varied by **$6.24:1$** (from 811 images for `chole_bhature` down to 130 images for `paani_puri`).

**Our Fix:**
* We pooled all 15,404 images and engineered a programmatic **Stratified 70% Train (10,782) / 15% Validation (2,311) / 15% Test (2,311)** split with `random_seed=42`, guaranteeing exact proportional class representation across all partitions.
* We computed inverse class frequency weights:
  $$w_c = \frac{N}{C \cdot N_c}$$
  and injected them directly into PyTorch's `CrossEntropyLoss` to heavily penalize errors on minority sweet and street-snack classes.

#### B. Deep Transfer Learning Models
We benchmarked two complementary architectures:
1. **ResNet-50 (Production Classifier):** A 50-layer deep network utilizing **Bottleneck Residual Blocks** ($1\times1 \to 3\times3 \to 1\times1$ convolutions) with identity skip connections $[\mathcal{F}(x) + x]$ that eliminate the vanishing gradient problem, producing a rich 2048-dimensional feature embedding.
2. **MobileNetV2 (Lightweight Edge Benchmark):** Uses inverted residual bottlenecks and depthwise separable convolutions to test real-time mobile latency.
3. **Custom PyTorch Classification Head:**
   $$\text{Input Tensor (224}\times\text{224}\times\text{3)} \longrightarrow \text{ResNet50 Backbone} \longrightarrow \text{AdaptiveAvgPool2d(1)} \longrightarrow \text{Dropout(0.3)} \longrightarrow \text{Linear(2048, 43)} \longrightarrow \text{Softmax}$$
4. **Optimization:** Trained using **AdamW** ($\text{lr}=3\times 10^{-4}$, $\text{weight decay}=10^{-4}$) with automatic mixed precision (`torch.cuda.amp`), `CosineAnnealingLR` schedule ($T_{\max}=15$, $\eta_{\min}=10^{-6}$), and Early Stopping ($\text{patience}=3$).

#### C. Unsupervised Multi-Dish Thali Segmentation
Because the dataset lacked bounding boxes, supervised object detectors (YOLO) could not be trained without thousands of hours of manual annotation. We engineered an unsupervised heuristic pipeline (`classifier.predict_multi`):
* Converts input photos to **CIE-LAB color space**, which separates perceptual lightness from chromatic color channels.
* Performs **K-Means clustering** to segment discrete food regions from the metallic plate background.
* Applies **multi-scale overlapping grid slicing** to extract candidate dish crops.
* Passes each candidate crop through the ResNet-50 classifier, filters duplicates using confidence and spatial Non-Maximum Suppression (NMS), and outputs individual bowl predictions.

#### D. Nutritional Database & Metabolic Engine
* Seeded a relational **SQLite database (`nutrition.db`)** with authentic cooked values from the **National Institute of Nutrition (NIN) IFCT 2017** publication.
* Built a conversion matrix for **163 Indian household serving units** (e.g., *1 small katori* = 100g, *1 medium katori* = 150g, *1 roti* = 40g, *1 plate* = 250g).
* Built a clinical health calculator enforcing Asian-Indian WHO/ICMR risk cutoffs ($\text{BMI} \ge 23$ Overweight, $\ge 25$ Obese) and **Mifflin-St Jeor Basal Metabolic Rate (BMR)** scaled by Physical Activity Level (PAL) to establish daily calorie deficit/surplus budgets.

---

### 4. Result: Quantitative Performance & Impact
* **High Classification Accuracy:** The fine-tuned **ResNet-50 achieved 93.68% Validation Top-1 Accuracy** and **99.05% Validation Top-5 Accuracy** (`val_loss = 0.3245`).
* **Fast Real-Time Inference:** Benchmarked CPU latency of **~34.0 ms for ResNet-50** and **~9.3 ms for MobileNetV2**, allowing seamless real-time web execution.
* **Resolving Ambiguity via Top-5:** Presenting the Top-5 confidence ranking resolved gravy ambiguity (e.g., *Dal Makhani* vs. *Rajma*), enabling 1-click user verification.
* **Full-Stack Deployment:** Engineered a responsive, 6-module Streamlit interface backed by SQLite session persistence, version-controlled with Git, and deployed live on Streamlit Cloud.

---

##  System Architecture & Workflow (Explained for Beginners)

If you're new to deep learning, here is how the system processes a meal photo step-by-step:

```
[ User Uploads Meal Photo ]
             │
             ▼
[ 1. Input & Preprocessing ] ──── Resizes photo to 224×224 pixels & normalizes colors
             │
             ▼
[ 2. Multi-Dish Thali Engine ] ── If plate has multiple dishes, K-Means groups colors & crops each bowl
             │
             ▼
[ 3. ResNet-50 Backbone ] ─────── 50 deep convolutional layers extract 2048 culinary visual features
             │
             ▼
[ 4. PyTorch Classifier Head ] ── Dropout(0.3) regularizes + Linear layer scores all 43 Indian dishes
             │
             ▼
[ 5. Prediction & Softmax ] ───── Outputs Top-1 prediction (e.g. "Dal Makhani 96.7%") + Top-5 alternatives
             │
             ▼
[ 6. Portion Normalizer ] ─────── Converts user's serving (e.g., "1 katori") into exact grams (150g)
             │
             ▼
[ 7. IFCT 2017 SQLite Query ] ─── Multiplies grams by official ICMR-NIN nutrition per 100g
             │
             ▼
[ 8. Daily Health Dashboard ] ─── Compares meal calories to user's ICMR Asian-Indian TDEE calorie budget
```

### In-Depth Layer Breakdown:
1. **Image Preprocessing:** Every meal photo is converted to RGB, resized to $224 \times 224$ pixels, and normalized using standard ImageNet mean ($\mu = [0.485, 0.456, 0.406]$) and standard deviation ($\sigma = [0.229, 0.224, 0.225]$).
2. **Stem (Stage 0):** A $7\times7$ convolution with stride 2 and $3\times3$ MaxPool rapidly shrinks the image from $224\times224$ down to $56\times56$, capturing coarse edges and textures.
3. **Bottleneck Residual Stages (Stages 1–4):**
   * **Stage 1 (conv2_x):** 3 Bottleneck blocks $\to$ outputs $56\times56\times256$.
   * **Stage 2 (conv3_x):** 4 Bottleneck blocks $\to$ outputs $28\times28\times512$.
   * **Stage 3 (conv4_x):** 6 Bottleneck blocks $\to$ outputs $14\times14\times1024$ *(deepest feature extractor)*.
   * **Stage 4 (conv5_x):** 3 Bottleneck blocks $\to$ outputs $7\times7\times2048$ *(high-level conceptual food features)*.
   * *Why Skip Connections Matter:* Normal deep networks suffer from vanishing gradients (signals fade to zero as networks get deeper). ResNet adds the original input $x$ to the output $\mathcal{F}(x)$ via a shortcut, allowing gradients to flow backward unobstructed.
4. **Classification Head:**
   * `AdaptiveAvgPool2d((1, 1))` collapses the $7\times7\times2048$ spatial tensor into a $2048\times1\times1$ feature vector.
   * `Dropout(p=0.3)` randomly zeroes 30% of neurons during training to prevent memorization.
   * `Linear(2048, 43)` maps the 2048 visual features into 43 raw class scores (logits).
   * `Softmax` converts logits into clean percentages ($0\text{--}100\%$) for Top-1 and Top-5 confidence rankings.

---

##  Model Architecture & Benchmarks

| Metric / Specification | **ResNet-50 (Production Model)** | **MobileNetV2 (Edge Baseline)** |
| :--- | :--- | :--- |
| **Model Checkpoint** | `models/best_model.pt` | `data/evaluation_metrics.json` |
| **Model Size** | **90.32 MB** | **14.2 MB** |
| **Parameters** | 25.6 Million | 3.5 Million |
| **Validation Top-1 Accuracy** | **93.68%** | 81.45% |
| **Validation Top-5 Accuracy** | **99.05%** | 94.32% |
| **Macro F1-Score** | **0.93** | 0.81 |
| **CPU Inference Latency** | **~34.0 ms** | **~9.3 ms** |
| **Best Architectural Trait** | High feature capacity for visually overlapping gravies | Ultra-lightweight for low-power mobile devices |

### Top Performing vs. Challenging Classes:
* **Easiest Classes (F1 > 0.92):** *Jalebi* ($0.945$), *Idli* ($0.938$), *Dhokla* ($0.926$), *Samosa* ($0.919$) — High geometric distinctiveness (spirals, white discs, yellow cubes, triangles).
* **Most Challenging Classes (F1 ~ 0.71–0.74):** *Rajma Curry* ($0.712$) vs. *Dal Makhani* ($0.724$), *Shahi Paneer* vs. *Kadai Paneer* ($0.735$) — Shared tomato-onion-cream color base. Solved via Top-5 confidence ranking!

---

##  Dataset Specifications

* **Official Repository:** `SohlHealth/enhanced-indian-food-classification` (Hugging Face / Kaggle).
* **Total Samples:** **15,404 RGB images**.
* **Total Classes:** **43 Authentic Indian Categories**:
  > *aloo_gobi, aloo_masala, bhindi_masala, biryani, burger, butter_naan, chai, chapati, chicken_curry, chole, chole_bhature, coconut_chutney, dal_makhani, dhokla, dum_aloo, fish_curry, fried_rice, ghevar, green_chutney, gulab_jamun, idli, jalebi, kaathi_rolls, kadai_paneer, kebab, kheer, kulfi, lassi, masala_dosa, modak, momos, mutton_curry, paani_puri, pakode, palak_paneer, pav_bhaji, pizza, poha, rajma_curry, ras_malai, samosa, shahi_paneer, white_rice.*
* **Data Split Partition (Stratified 70/15/15):**
  * **Train Set:** 10,782 images (augmented with random flips, rotations $\pm 15^\circ$, and color jitter).
  * **Validation Set:** 2,311 images (unaugmented, for early stopping and model checkpointing).
  * **Test Set:** 2,311 images (held-out final verification).

---

##  Full-Stack Web Application Modules

The application (`frontend/app.py`) provides 6 cohesive modules:

1. ** Home:** High-level project summary, quick-start guide, and interactive catalog of all 43 supported Indian dishes.
2. ** Dashboard:** Real-time visual tracking of today's calorie consumption vs. daily TDEE budget, animated progress rings, and macronutrient distribution (Protein, Carbs, Fats, Fiber).
3. ** Food Scanner:** 
   * **Single Meal Mode:** Upload or take a picture with your webcam, crop the target bowl, predict the dish, choose standard Indian household serving units (*katori, roti, piece*), and review nutrient breakdown.
   * **Multiple Meals (Thali) Mode:** Automatically detects multiple dishes on a platter using K-Means color clustering, lists all items with individual serving selectors, and computes cumulative plate calories.
4. ** Health Profile:** Calculates personalized metabolic markers using the **Mifflin-St Jeor formula** and classifies BMI strictly against **Asian-Indian ICMR guidelines**:
   * *Underweight:* $< 18.5\text{ kg/m}^2$
   * *Normal:* $18.5 - 22.9\text{ kg/m}^2$
   * *Overweight (At-Risk):* $23.0 - 24.9\text{ kg/m}^2$
   * *Obese:* $\ge 25.0\text{ kg/m}^2$
5. ** Meal History:** Persistent historical log of all meals consumed, filterable by date, featuring a 7-day caloric expenditure bar chart and 1-click meal deletion.
6. ** Nutrition Database:** Searchable dictionary of all 43 Indian dishes showing their laboratory-tested IFCT 2017 nutritional composition per 100g, supported serving units, and calorie densities.

---

##  How to Run the Project Locally

Follow these step-by-step instructions to clone and run NutriLens AI on your local machine:

### 1. Prerequisites
* Python 3.10, 3.11, 3.12, or 3.13 installed.
* Git installed.

### 2. Clone the Repository
```bash
git clone https://github.com/Aditi-Kumar03/DL_Project.git
cd DL_Project
```

### 3. Create & Activate a Virtual Environment
* **On Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
* **On macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 4. Install Dependencies
* **CPU Only (Standard):**
  ```bash
  pip install -r requirements.txt
  ```
* **With T4 GPU Acceleration (CUDA 12.4):**
  ```bash
  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
  pip install -r requirements.txt
  ```

### 5. Launch the Web Application
```bash
streamlit run frontend/app.py
```
After running the command, your terminal will display a local URL:
```
  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```
Open **`http://localhost:8501`** in any web browser to use the application!

---

##  Project Repository Structure

```text
DL_Project/
├── .streamlit/
│   └── config.toml                        # UI light indigo theme & font configurations
├── backend/
│   ├── base_model.py                      # Abstract Base Class for ML models & PredictionResult dataclass
│   ├── classifier.py                      # PyTorch classifier engine (single, crop & multi-dish K-Means)
│   ├── database.py                        # SQLite schema & ICMR-NIN IFCT 2017 nutritional seed data
│   ├── detector.py                        # Extensible detection adapter
│   ├── health_calculator.py               # Asian-Indian BMI, Mifflin-St Jeor BMR & TDEE engine
│   ├── meal_service.py                    # CRUD operations for meal logs, user profile & daily targets
│   └── nutrition_engine.py                # Household serving-to-gram scaling & macro totals
├── data/
│   ├── nutrition.db                       # Local SQLite database (dishes, serving weights, logs)
│   ├── dataset_exploration_summary.json   # Phase 1 exploratory audit and class count manifest
│   └── evaluation_metrics.json            # Baseline evaluation metrics, confusion pairs & F1-scores
├── frontend/
│   ├── app.py                             # Main Streamlit home entry point
│   ├── utils.py                           # Shared CSS styles, navigation component & cached loaders
│   └── pages/
│       ├── 1_Dashboard.py                 # Daily calorie ring, macro distribution & energy balance
│       ├── 2_Food_Scanner.py              # Single meal & Multi-dish Thali image recognition
│       ├── 3_Health_Profile.py            # ICMR Asian-Indian BMI, BMR & TDEE goal configuration
│       ├── 4_Meal_History.py              # Filterable consumption history & 7-day calorie chart
│       └── 5_Nutrition_Database.py        # Searchable IFCT 2017 nutritional database browser
├── models/
│   ├── best_model.pt                      # Trained PyTorch ResNet50 checkpoint (90.32 MB, 43 classes)
│   ├── class_names.json                   # 43 dish labels mapped to model output indices
│   ├── model_config.json                  # Model hyperparameter manifest (224x224, AdamW, Cosine LR)
│   └── version.json                       # Model versioning metadata
├── notebooks/
│   ├── 01_dataset_exploration.ipynb       # Exploratory data analysis & upstream split audit
│   ├── 02_preprocessing.ipynb             # Stratified 70/15/15 split, class weights & augmentations
│   ├── 03_model_training.ipynb            # Mixed-precision transfer learning (ResNet50 & MobileNetV2)
│   └── 04_model_evaluation.ipynb          # Holdout test metrics, Top-1/Top-5 accuracy & confusion matrix
├── sample_images/                         # Test sample images (samosa.jpg, jalebi.jpg, thali.jpg)
├── requirements.txt                       # Project Python dependencies
└── README.md                              # Comprehensive project documentation
```

---

##  Future Enhancements Roadmap

1. **Supervised Instance Segmentation (YOLOv8-Seg):** Transition from the current unsupervised K-Means/grid thali proposal to an end-to-end trained YOLOv8-Seg or Mask R-CNN network with polygon boundary masks for precise dish separation.
2. **3D Food Volume & Monocular Depth Estimation:** Implement monocular depth estimation models (MiDaS / ZoeDepth) alongside reference fiducial markers to calculate exact 3D volumetric density and automated food weight without manual serving selection.
3. **Clinical Chronic Disease Engine:** Scale the dataset from 43 to 150+ regional dishes and integrate clinical **Glycemic Index (GI)** warnings for Type-2 diabetic patients and sodium monitoring for cardiovascular hypertension based on ICMR clinical guidelines.



### ⚠️ Disclaimer
*NutriLens AI provides dietary, caloric, macronutrient, BMI, and TDEE estimations for informational and personal health-tracking purposes only. It is not intended as medical advice or a substitute for professional clinical dietetics.*
