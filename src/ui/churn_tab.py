from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableView, QMessageBox, QComboBox, QFormLayout
)
from PyQt6.QtCore import Qt
import pandas as pd

from ..ml_engine import ChurnPredictor
from .widgets import PandasTableModel, KpiCard
from .mpl_canvas import MplCanvas
from .styles import NAVY, BLUE_ACCENT, RED, AMBER, GREEN


class ChurnTab(QWidget):
    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self.scored_df = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Churn Prediction")
        title.setObjectName("sectionTitle")
        subtitle = QLabel("Random Forest classifier trained on behavioural and engagement signals.")
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        controls = QHBoxLayout()
        self.train_btn = QPushButton("Train Churn Model")
        self.train_btn.clicked.connect(self.train_model)
        controls.addWidget(self.train_btn)
        controls.addStretch()
        layout.addLayout(controls)

        kpi_row = QHBoxLayout()
        self.kpi_auc = KpiCard("ROC-AUC", "—", BLUE_ACCENT)
        self.kpi_acc = KpiCard("Accuracy", "—", GREEN)
        self.kpi_recall = KpiCard("Recall (catch rate)", "—", AMBER)
        self.kpi_high_risk = KpiCard("High-Risk Customers", "—", RED)
        for card in (self.kpi_auc, self.kpi_acc, self.kpi_recall, self.kpi_high_risk):
            kpi_row.addWidget(card)
        layout.addLayout(kpi_row)

        chart_row = QHBoxLayout()
        self.importance_chart = MplCanvas(width=5, height=3.4)
        self.roc_chart = MplCanvas(width=4, height=3.4)
        chart_row.addWidget(self.importance_chart, stretch=3)
        chart_row.addWidget(self.roc_chart, stretch=2)
        layout.addLayout(chart_row)

        table_header = QHBoxLayout()
        table_label = QLabel("At-Risk Customers")
        table_label.setObjectName("sectionTitle")
        table_header.addWidget(table_label)
        table_header.addStretch()

        self.risk_filter = QComboBox()
        self.risk_filter.addItems(["All", "High", "Medium", "Low"])
        self.risk_filter.currentTextChanged.connect(self._apply_filter)
        table_header.addWidget(QLabel("Filter by risk:"))
        table_header.addWidget(self.risk_filter)
        layout.addLayout(table_header)

        self.risk_table = QTableView()
        self.risk_table.setAlternatingRowColors(True)
        self.risk_model = PandasTableModel()
        self.risk_table.setModel(self.risk_model)
        layout.addWidget(self.risk_table, stretch=1)

    def train_model(self):
        df = self.app_state.raw_df
        if df is None or df.empty:
            QMessageBox.warning(self, "No Data", "Load a dataset in the Data Explorer tab first.")
            return
        if "churned" not in df.columns:
            QMessageBox.warning(self, "Missing Target", "Dataset needs a 'churned' column (0/1) to train on.")
            return

        predictor = ChurnPredictor()
        try:
            metrics = predictor.train(df)
        except Exception as e:
            QMessageBox.critical(self, "Training Failed", str(e))
            return

        self.app_state.churn_engine = predictor
        scored = predictor.predict_all(df)
        self.scored_df = scored
        self.app_state.scored_df = scored

        self.kpi_auc.set_value(f"{metrics['roc_auc']:.3f}")
        self.kpi_acc.set_value(f"{metrics['accuracy']:.1%}")
        self.kpi_recall.set_value(f"{metrics['recall']:.1%}")
        high_risk_count = (scored["risk_tier"] == "High").sum()
        self.kpi_high_risk.set_value(f"{high_risk_count:,}")

        self._draw_importance(predictor.feature_importances_)
        self._draw_roc(metrics["roc_curve"], metrics["roc_auc"])
        self._apply_filter(self.risk_filter.currentText())

        QMessageBox.information(
            self, "Training Complete",
            f"Trained on {metrics['n_train']:,} customers, tested on {metrics['n_test']:,}.\n"
            f"ROC-AUC: {metrics['roc_auc']:.3f}  |  Recall: {metrics['recall']:.1%}"
        )

    def _draw_importance(self, importances: pd.Series):
        self.importance_chart.clear()
        top = importances.head(8).sort_values()
        self.importance_chart.axes.barh(top.index, top.values, color=BLUE_ACCENT)
        self.importance_chart.axes.set_title("Top Churn Drivers", fontsize=11, color=NAVY, fontweight="bold")
        self.importance_chart.axes.tick_params(labelsize=7)
        self.importance_chart.draw()

    def _draw_roc(self, roc_curve_data, auc):
        fpr, tpr = roc_curve_data
        self.roc_chart.clear()
        self.roc_chart.axes.plot(fpr, tpr, color=BLUE_ACCENT, linewidth=2, label=f"AUC = {auc:.3f}")
        self.roc_chart.axes.plot([0, 1], [0, 1], color="#9ca3af", linestyle="--", linewidth=1)
        self.roc_chart.axes.set_xlabel("False Positive Rate", fontsize=8)
        self.roc_chart.axes.set_ylabel("True Positive Rate", fontsize=8)
        self.roc_chart.axes.set_title("ROC Curve", fontsize=11, color=NAVY, fontweight="bold")
        self.roc_chart.axes.legend(fontsize=8, loc="lower right", facecolor="#1e1e1e", edgecolor="#2c2c2c", labelcolor="#d4d4d8")
        self.roc_chart.axes.tick_params(labelsize=7)
        self.roc_chart.draw()

    def _apply_filter(self, tier: str):
        if self.scored_df is None:
            return
        cols = ["customer_id", "recency_days", "frequency", "monetary",
                "avg_satisfaction_score", "support_tickets", "churn_probability", "risk_tier"]
        cols = [c for c in cols if c in self.scored_df.columns]
        df = self.scored_df[cols].sort_values("churn_probability", ascending=False)
        if tier != "All":
            df = df[df["risk_tier"] == tier]
        self.risk_model.set_dataframe(df.reset_index(drop=True))
        self.risk_table.resizeColumnsToContents()
