"""
ML Engine
---------
Three independent models:

1. CustomerSegmentation — unsupervised RFM (Recency/Frequency/Monetary)
   clustering via KMeans, with clusters auto-labelled into human-readable
   business segments (Champions, Loyal, At Risk, Hibernating, New/Low-Value)
   based on their relative RFM scores.

2. ChurnPredictor — supervised RandomForestClassifier trained on
   behavioural + engagement features to predict churn probability per
   customer, with feature importances and standard evaluation metrics.

3. DecisionTreePredictor — supervised DecisionTreeClassifier trained on
   the same feature set as ChurnPredictor. Provides a fully inspectable
   single-tree model whose decision logic can be rendered visually, making
   it the interpretability complement to the Random Forest black box.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, confusion_matrix
)


class CustomerSegmentation:
    RFM_COLS = ["recency_days", "frequency", "monetary"]

    def __init__(self, n_clusters: int = 4, random_state: int = 42):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
        self.cluster_labels_: dict[int, str] = {}
        self.is_fitted = False

    def fit_predict(self, df: pd.DataFrame) -> pd.DataFrame:
        rfm = df[self.RFM_COLS].copy()
        # Recency: lower is better, so invert before scaling to keep "higher=better" direction consistent
        rfm_for_scaling = rfm.copy()
        rfm_for_scaling["recency_days"] = -rfm_for_scaling["recency_days"]

        X = self.scaler.fit_transform(rfm_for_scaling)
        clusters = self.model.fit_predict(X)
        self.is_fitted = True

        result = df.copy()
        result["cluster"] = clusters
        self._auto_label_clusters(result)
        result["segment"] = result["cluster"].map(self.cluster_labels_)
        return result

    def _auto_label_clusters(self, df: pd.DataFrame) -> None:
        """Rank clusters by a composite RFM score and assign business-friendly names."""
        summary = df.groupby("cluster")[self.RFM_COLS].mean()
        # Composite score: high frequency & monetary good, high recency bad
        r_rank = summary["recency_days"].rank(ascending=True)   # 1 = most recent = best
        f_rank = summary["frequency"].rank(ascending=False)      # 1 = most frequent = best
        m_rank = summary["monetary"].rank(ascending=False)       # 1 = highest spend = best
        composite = (r_rank + f_rank + m_rank).sort_values()

        ordered_clusters = composite.index.tolist()
        n = len(ordered_clusters)
        names = ["Champions", "Loyal Customers", "At Risk", "Hibernating", "New / Low-Value"]
        # Map best -> worst composite score onto the name list, extending gracefully if n_clusters differs
        labels = {}
        for i, cluster_id in enumerate(ordered_clusters):
            labels[cluster_id] = names[i] if i < len(names) else f"Segment {i+1}"
        self.cluster_labels_ = labels

    def segment_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.groupby("segment")
            .agg(
                customers=("customer_id", "count"),
                avg_recency=("recency_days", "mean"),
                avg_frequency=("frequency", "mean"),
                avg_monetary=("monetary", "mean"),
                churn_rate=("churned", "mean") if "churned" in df.columns else ("customer_id", "count"),
            )
            .round(2)
            .sort_values("avg_monetary", ascending=False)
        )


class ChurnPredictor:
    FEATURE_COLS = [
        "age", "tenure_days", "recency_days", "frequency", "monetary",
        "avg_order_value", "num_categories_purchased", "num_returns",
        "return_rate", "support_tickets", "avg_satisfaction_score",
        "email_open_rate", "discount_usage_rate", "loyalty_member",
    ]
    TARGET_COL = "churned"

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.model = RandomForestClassifier(
            n_estimators=300,
            max_depth=8,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1,
        )
        self.is_fitted = False
        self.metrics_: dict = {}
        self.feature_importances_: pd.Series | None = None

    def train(self, df: pd.DataFrame, test_size: float = 0.25) -> dict:
        X = df[self.FEATURE_COLS]
        y = df[self.TARGET_COL]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=self.random_state, stratify=y
        )

        self.model.fit(X_train, y_train)
        self.is_fitted = True

        y_pred = self.model.predict(X_test)
        y_proba = self.model.predict_proba(X_test)[:, 1]

        fpr, tpr, _ = roc_curve(y_test, y_proba)

        self.metrics_ = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred, zero_division=0),
            "recall": recall_score(y_test, y_pred, zero_division=0),
            "f1": f1_score(y_test, y_pred, zero_division=0),
            "roc_auc": roc_auc_score(y_test, y_proba),
            "confusion_matrix": confusion_matrix(y_test, y_pred),
            "roc_curve": (fpr, tpr),
            "n_train": len(X_train),
            "n_test": len(X_test),
            "test_churn_rate": float(y_test.mean()),
        }

        self.feature_importances_ = pd.Series(
            self.model.feature_importances_, index=self.FEATURE_COLS
        ).sort_values(ascending=False)

        return self.metrics_

    def predict_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """Score every customer in the full dataset with churn probability + risk tier."""
        if not self.is_fitted:
            raise RuntimeError("Model must be trained before calling predict_all().")

        X = df[self.FEATURE_COLS]
        proba = self.model.predict_proba(X)[:, 1]

        result = df.copy()
        result["churn_probability"] = np.round(proba, 4)
        result["risk_tier"] = pd.cut(
            result["churn_probability"],
            bins=[-0.01, 0.3, 0.6, 1.01],
            labels=["Low", "Medium", "High"],
        )
        return result


class DecisionTreePredictor:
    """Interpretable single Decision Tree classifier.

    Exposes the fitted sklearn model object directly so the UI layer can
    render the tree via sklearn.tree.plot_tree() without extra dependencies.
    """

    def __init__(self, max_depth: int = 4, random_state: int = 42):
        self.max_depth = max_depth
        self.random_state = random_state
        self.model = DecisionTreeClassifier(
            max_depth=max_depth,
            class_weight="balanced",
            random_state=random_state,
        )
        self.is_fitted = False
        self.metrics_: dict = {}
        self.feature_importances_: pd.Series | None = None
        self.target_col = None
        self.feature_cols = []

    def train(self, df: pd.DataFrame, target_col: str, feature_cols: list[str], test_size: float = 0.25) -> dict:
        self.target_col = target_col
        self.feature_cols = feature_cols

        X = df[feature_cols]
        y = df[target_col]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=self.random_state, stratify=y
        )

        self.model.fit(X_train, y_train)
        self.is_fitted = True

        y_pred = self.model.predict(X_test)

        try:
            y_proba = self.model.predict_proba(X_test)
            if y_proba.shape[1] == 2:
                proba_for_roc = y_proba[:, 1]
                roc_auc = roc_auc_score(y_test, proba_for_roc)
                fpr, tpr, _ = roc_curve(y_test, proba_for_roc)
                roc_curve_val = (fpr, tpr)
            else:
                proba_for_roc = y_proba
                roc_auc = roc_auc_score(y_test, proba_for_roc, multi_class="ovr")
                roc_curve_val = None
        except Exception:
            roc_auc = 0.0
            roc_curve_val = None

        self.metrics_ = {
            "accuracy":         accuracy_score(y_test, y_pred),
            "precision":        precision_score(y_test, y_pred, average="weighted", zero_division=0),
            "recall":           recall_score(y_test, y_pred, average="weighted", zero_division=0),
            "f1":               f1_score(y_test, y_pred, average="weighted", zero_division=0),
            "roc_auc":          roc_auc,
            "confusion_matrix": confusion_matrix(y_test, y_pred),
            "roc_curve":        roc_curve_val,
            "n_train":          len(X_train),
            "n_test":           len(X_test),
            "max_depth":        self.max_depth,
        }

        self.feature_importances_ = pd.Series(
            self.model.feature_importances_, index=feature_cols
        ).sort_values(ascending=False)

        return self.metrics_

    def predict_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """Score every customer with predictions and probability metrics."""
        if not self.is_fitted:
            raise RuntimeError("Model must be trained before calling predict_all().")

        X = df[self.feature_cols]
        preds = self.model.predict(X)

        result = df.copy()
        result["dt_prediction"] = preds

        try:
            proba = self.model.predict_proba(X)
            if proba.shape[1] == 2:
                result["dt_probability"] = np.round(proba[:, 1], 4)
                result["dt_risk_tier"] = pd.cut(
                    result["dt_probability"],
                    bins=[-0.01, 0.3, 0.6, 1.01],
                    labels=["Low", "Medium", "High"],
                )
            else:
                result["dt_probability"] = np.round(np.max(proba, axis=1), 4)
                result["dt_risk_tier"] = "N/A"
        except Exception:
            result["dt_probability"] = 0.5
            result["dt_risk_tier"] = "N/A"

        return result

