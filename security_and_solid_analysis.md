# SOLID Principles & Security Analysis Report

This document evaluates the codebase of the **Customer Insight CMS** application against the **SOLID design principles** and **security best practices**. It outlines findings and provides a prioritized task sheet to guide refactoring and mitigation efforts.

---

## 1. SOLID Principles Analysis

### 🔴 Single Responsibility Principle (SRP)
* **Finding**: The UI tab classes (e.g., `DataTab`, `CrmTab`, `ChurnTab`, `SegmentationTab`) have too many responsibilities. They handle visual layout rendering, parse user inputs, coordinate SQLite database transactions, execute training logic, and compute evaluation metrics.
* **Impact**: Changes to data loading formatting, model options, or database engines force modifications to UI visual presentation classes.
* **Recommendation**: Separate UI controls from business logic by introducing a controller layer or database/ML services.

### 🟡 Open/Closed Principle (OCP)
* **Finding**: The ML training classes `ChurnPredictor` and `CustomerSegmentation` are tightly coupled to specific scikit-learn models (`RandomForestClassifier` and `KMeans`). Swapping in a different algorithm (e.g. XGBoost, GradientBoosting, DBScan) requires modifying the implementation code of these engines directly.
* **Impact**: Adding new features, columns, or models requires modifying core files instead of extending them.
* **Recommendation**: Introduce abstract base interfaces (e.g., `BaseClassifier` or `BaseClusterer`) and inject model instances.

### 🟢 Liskov Substitution Principle (LSP)
* **Finding**: No violations. The custom widgets and classes correctly subclass PyQt classes (like `QWidget` and `QAbstractTableModel`) and adhere to their signature interfaces.

### 🟡 Interface Segregation Principle (ISP)
* **Finding**: The global `AppState` object is shared across all tabs. A tab like `DashboardTab` receives the entire state (including ML classifiers, database references, and clustering engines) when it only requires access to the raw dataframes.
* **Impact**: Tight coupling makes debugging state updates difficult.
* **Recommendation**: Segregate the state into smaller, logical contexts, or pass only required subsets to tabs.

### 🔴 Dependency Inversion Principle (DIP)
* **Finding**: High-level modules directly depend on low-level concrete modules. `MainWindow` instantiates concrete `Database` and tabs, and tabs directly instantiate concrete model engines.
* **Impact**: Hard to mock models/database connections for unit tests.
* **Recommendation**: Use dependency injection to pass service references (e.g., Database wrapper, ML models) into the constructor of tabs and windows.

---

## 2. Security Analysis

### 🔴 SQL Injection Vulnerability (High Risk)
* **Location**: `src/database.py` — `load_customers`
* **Vulnerable Code**: 
  ```python
  def load_customers(self, table: str = "customers") -> pd.DataFrame:
      try:
          return pd.read_sql(f"SELECT * FROM {table}", self.conn)
      except Exception:
          return pd.DataFrame()
  ```
* **Threat**: Using string formatting (`f"SELECT * FROM {table}"`) permits SQL injection if the table parameter ever gets populated from user inputs or untrusted files.
* **Mitigation**: Parameterize table queries or strictly sanitize/whitelist permitted table names before execution.

### 🟡 Safe Model Deserialization / Pickle Risks (Medium Risk)
* **Context**: The project README suggests saving models via `joblib.dump` / `pickle`. 
* **Threat**: Deserializing model binaries (`joblib.load` / `pickle.load`) from untrusted user directories can trigger arbitrary remote code execution (RCE).
* **Mitigation**: Warn users or require cryptographic signatures/verifications when loading external model files, or save model parameters in structured formats like JSON/ONNX instead.

### 🟡 Malicious CSV Payloads / Formula Injection (Medium Risk)
* **Context**: `data_tab.py` uses `pd.read_csv` to load user-supplied spreadsheets.
* **Threat**: If files containing Excel formulas (starting with `=`, `+`, `-`, `@`) are imported and later exported, it can result in formula injection, launching command-line processes in the user's spreadsheet software.
* **Mitigation**: Sanitize CSV cells containing active formula characters during import/export.

### 🟢 Missing Input Sanitation & Data Validation (Low Risk)
* **Location**: `src/ui/crm_tab.py` and `src/ui/data_tab.py`
* **Finding**: Inputs are parsed as numbers without bounds checking (e.g., checking if spend is negative, satisfaction scores range from 1 to 5, or return rates fall between 0 and 1).
* **Impact**: Malformed data rows can corrupt ML model predictions or crash training routines due to division-by-zero or out-of-bounds metrics.
* **Mitigation**: Validate numerical ranges and enforce signup date syntax (`YYYY-MM-DD`).

---

## 3. Prioritized Task Sheet

Here is the task sheet grouped from **most crucial** to **least crucial**:

| Priority | Category | Task | Target File(s) | Description |
| :--- | :--- | :--- | :--- | :--- |
| **1. Crucial** | Security | Parameterize or Validate Table Queries | `src/database.py` | Eliminate dynamic string interpolation in `load_customers` SQL query. |
| **2. Crucial** | Security | Enforce Numeric Input Validation in CRM | `src/ui/crm_tab.py` | Add validation bounds for metrics (e.g., satisfaction: 1–5, email/return rate: 0–1, non-negative monetary spend). |
| **3. High** | SOLID (SRP) | Refactor Business Workflows from Tabs | `src/ui/*_tab.py` | Relocate classifier training and cluster fitting away from UI event handlers to specialized controllers. |
| **4. Medium** | SOLID (OCP) | Define ML Model Base Interfaces | `src/ml_engine.py` | Abstract `ChurnPredictor` and `CustomerSegmentation` to support swapping ML classifiers/clusterers. |
| **5. Medium** | Security | Sanitize CSV Formula Characters | `src/ui/data_tab.py` | Sanitize cells starting with formula tokens (`=`, `+`, `-`, `@`) during loading. |
| **6. Low** | SOLID (ISP) | Segregate Shared State Context | `src/ui/main_window.py` | Restructure state sharing so tabs only receive the dependencies they actually consume. |
