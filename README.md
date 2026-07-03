# Daluvuyo Magagane: Customer Insight CMS & Machine Learning Analytics Suite

A professional desktop application developed using **PyQt6** and **Scikit-Learn**. This platform transitions organizations from static spreadsheet data processing to an interactive, real-time customer data explorer, Customer Relationship Manager (CRM), and advanced machine learning predictive analytics suite.

---

## Project Overview

Modern businesses require immediate, data-driven intelligence to maximize customer lifetime value (LTV) and preempt customer attrition. This "Smart" Customer Insight CMS provides a centralized desktop environment that enables marketing departments and business analysts to load customer records, update profiles, cluster cohorts via unsupervised learning, train predictive churn classifiers, and extract automated AI tactical action playbooks.

---

## Key Objectives

1. **Integrated CRM Sync**: Active SQLite database synchronization ensures user profile edits immediately update across raw data tables and downstream ML models.
2. **Data-Driven Cohort Clustering**: Automated RFM (Recency, Frequency, Monetary) scaling and K-Means clustering partitions the customer base into distinct, actionable business segments.
3. **Predictive Attrition Classification**: High-accuracy RandomForest modeling exposes exactly which behavioral metrics (support tickets, satisfaction, recency) drive customer attrition.
4. **Adaptive Explainability**: A fully interactive Decision Tree module allows dynamically choosing the prediction target and visual depth to decode model rules visually.
5. **AI Tactical Action Interpretation**: Translates complex feature importances and cluster metrics into structured, color-coded executive prioritization guides.

---

## Developer Accountability

As the **sole developer** of this project, **Daluvuyo Magagane** executed all stages of the product lifecycle:

| Role / Domain | Key Responsibilities |
|---|---|
| **Product & System Architect** | System design, cross-tab reactive data synchronization pipelines, and app state design. |
| **Backend & Database Engineer** | SQLite schema engineering, SQL statement management, and connection handling in `src/database.py`. |
| **ML & Data Engineer** | Preprocessing scaling pipelines, unsupervised KMeans RFM segmentation, supervised Random Forest, and adaptive Decision Tree classifiers in `src/ml_engine.py`. |
| **Frontend / UI Designer** | Modern, premium charcoal-grey Dark Theme layout design, tab architecture, and custom widget styling in `src/ui/`. |
| **AI Interpreter Architect** | Automated HTML report compilation and metric translation rules in `src/ui/ai_insights_tab.py`. |

---

## Technical Architecture

The platform follows an **in-memory MVC (Model-View-Controller) / AppState architecture** designed for high responsiveness:

```
cms_ml/
├── main.py                     # App bootstrap and initialization entry point
├── src/
│   ├── database.py             # SQLite layer managing CRM database state
│   ├── data_generator.py       # High-fidelity synthetic client data engine
│   ├── ml_engine.py            # ML models (KMeans, RandomForest, DecisionTree)
│   └── ui/
│       ├── main_window.py      # App Controller holding AppState and tab layout
│       ├── styles.py           # Premium dark theme stylesheets (Charcoal/Blue)
│       ├── widgets.py          # Shared pandas model layouts & KPI cards
│       ├── data_tab.py         # CSV importing and table views
│       ├── crm_tab.py          # Customer profile CRM editor with CRUD sync
│       ├── dashboard_tab.py    # Executive metrics charts & graphs
│       ├── segmentation_tab.py # K-Means cluster visualizer and table summaries
│       ├── churn_tab.py        # Random Forest training panel and ROC curve plots
│       ├── decision_tree_tab.py# Dynamic tree zoom canvas and target selectors
│       └── ai_insights_tab.py  # Structured AI tactical priority generator
```

*   **Models**: Managed by `src/ml_engine.py` (scikit-learn classifiers/clustering models) and `src/database.py` (SQLite persistence schema).
*   **Views**: Rich PyQt6 widgets styled via QSS in `src/ui/styles.py`, interactive Matplotlib charts (`src/ui/mpl_canvas.py`), scrollable zoom canvases, and embedded web views for rendered HTML.
*   **Controllers**: Coordinated by the `MainWindow` class in `src/ui/main_window.py`. A centralized, shared `AppState` instance propagates data modifications across tabs reactively via Qt Signals.

---

## Key Features

### 1. Data Explorer & Generator
*   **Arbitrary CSV Importer**: Load customer datasets directly into Pandas tables.
*   **Synthetic Customer Generator**: Instantly generate 2,000 synthetic customer records with realistic, causally-linked behaviors (e.g., support ticket counts and low CSAT scores causally driving churn) to provide high-quality signal for the ML models to learn.

### 2. Live Database CRM
*   **SQLite-Backed Customer Registry**: Complete CRUD interface to search, add, edit, and delete customer database profiles.
*   **Active Sync**: Updates in the CRM automatically rewrite to SQLite and feed directly back to the raw DataFrame.

### 3. Unsupervised K-Means Segmentation
*   **RFM Scaling**: Automates Min-Max scaling on Recency, Frequency, and Monetary parameters.
*   **Auto-Labelling**: Maps cluster indices onto business-friendly cohorts: *Champions*, *Loyal Customers*, *At Risk*, *Hibernating*, and *New / Low-Value*.

### 4. Random Forest Churn Predictor
*   **Supervised Attrition Modeling**: Trains a Random Forest Classifier on 14 behavioral/engagement columns.
*   **Model Assessment**: Displays evaluation KPIs: Accuracy, Precision, Recall, and F1-Score alongside an ROC Curve.
*   **Feature Importances**: Renders a ranked bar graph showing what drives customer churn.

### 5. Adaptive Decision Tree Explainability
*   **Target Selector**: Dynamically select *any* column in the dataset as the target class variable (e.g., Churn, Loyalty Member).
*   **Auto-Feature Extraction**: Discovers and extracts all other numeric columns to use as features.
*   **Zoom Controls**: Sharp, non-blurry SVG/DPI zoom (30% to 400%) with custom scroll bars to navigate deep tree splits comfortably.

### 6. AI Insights Engine
*   **Automated Executive Report**: Translates model outputs into structured, executive-friendly cards.
*   **Tactical Priority List**: Lists actionable customer retention playbooks, ranked by urgency.

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone <repository-url>
cd cms_ml
```

### 2. Initialize Virtual Environment & Dependencies
```bash
# Create environment
python -m venv .venv

# Activate environment (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate environment (macOS / Linux)
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. (Optional) Run Synthetic Data Generator Separately
To generate a local CSV without booting the GUI:
```bash
python -m src.data_generator
```

### 4. Launch Application
```bash
python main.py
```

---

## Standalone Executable Packaging
You can pack the application into a single executable using PyInstaller:
```bash
pip install pyinstaller
pyinstaller --name "CustomerInsightCMS" --windowed --onefile --collect-all matplotlib --collect-all PyQt6 main.py
```
The packaged binary will be located in the `dist/` directory.
