from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableView, QMessageBox, QSpinBox, QFormLayout
)
import pandas as pd

from ..ml_engine import CustomerSegmentation
from .widgets import PandasTableModel
from .mpl_canvas import MplCanvas
from .styles import NAVY

SEGMENT_COLORS = {
    "Champions": "#22c55e",
    "Loyal Customers": "#3b82f6",
    "At Risk": "#f59e0b",
    "Hibernating": "#ef4444",
    "New / Low-Value": "#9ca3af",
}


class SegmentationTab(QWidget):
    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Customer Segmentation")
        title.setObjectName("sectionTitle")
        subtitle = QLabel("K-Means clustering on Recency, Frequency, and Monetary value (RFM).")
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        controls = QHBoxLayout()
        form = QFormLayout()
        self.cluster_spin = QSpinBox()
        self.cluster_spin.setRange(2, 6)
        self.cluster_spin.setValue(4)
        form.addRow("Number of segments:", self.cluster_spin)
        controls.addLayout(form)

        self.run_btn = QPushButton("Run Segmentation")
        self.run_btn.clicked.connect(self.run_segmentation)
        controls.addWidget(self.run_btn)
        controls.addStretch()
        layout.addLayout(controls)

        chart_row = QHBoxLayout()
        self.scatter = MplCanvas(width=5, height=4)
        self.pie = MplCanvas(width=4, height=4)
        chart_row.addWidget(self.scatter, stretch=3)
        chart_row.addWidget(self.pie, stretch=2)
        layout.addLayout(chart_row, stretch=2)

        summary_label = QLabel("Segment Summary")
        summary_label.setObjectName("sectionTitle")
        layout.addWidget(summary_label)

        self.summary_table = QTableView()
        self.summary_table.setAlternatingRowColors(True)
        self.summary_model = PandasTableModel()
        self.summary_table.setModel(self.summary_model)
        self.summary_table.setMaximumHeight(160)
        layout.addWidget(self.summary_table)

    def run_segmentation(self):
        df = self.app_state.raw_df
        if df is None or df.empty:
            QMessageBox.warning(self, "No Data", "Load a dataset in the Data Explorer tab first.")
            return

        required = {"recency_days", "frequency", "monetary"}
        if not required.issubset(df.columns):
            QMessageBox.warning(self, "Missing Columns", f"Dataset needs columns: {', '.join(required)}")
            return

        n_clusters = self.cluster_spin.value()
        engine = CustomerSegmentation(n_clusters=n_clusters)
        segmented = engine.fit_predict(df)
        self.app_state.segmented_df = segmented
        self.app_state.segmentation_engine = engine

        self._draw_scatter(segmented)
        self._draw_pie(segmented)

        summary = engine.segment_summary(segmented).reset_index()
        self.summary_model.set_dataframe(summary)
        self.summary_table.resizeColumnsToContents()

        QMessageBox.information(self, "Done", f"Segmented {len(df):,} customers into {n_clusters} groups.")

    def _draw_scatter(self, df: pd.DataFrame):
        self.scatter.clear()
        for segment, color in SEGMENT_COLORS.items():
            subset = df[df["segment"] == segment]
            if subset.empty:
                continue
            self.scatter.axes.scatter(
                subset["recency_days"], subset["monetary"],
                s=18, alpha=0.6, label=segment, color=color
            )
        self.scatter.axes.set_xlabel("Recency (days since last purchase)", fontsize=9)
        self.scatter.axes.set_ylabel("Monetary (total spend)", fontsize=9)
        self.scatter.axes.set_title("Segments: Recency vs Spend", fontsize=11, color=NAVY, fontweight="bold")
        self.scatter.axes.legend(fontsize=7, loc="upper right", facecolor="#1e1e1e", edgecolor="#2c2c2c", labelcolor="#d4d4d8")
        self.scatter.axes.tick_params(labelsize=8)
        self.scatter.draw()

    def _draw_pie(self, df: pd.DataFrame):
        self.pie.clear()
        counts = df["segment"].value_counts()
        colors = [SEGMENT_COLORS.get(s, "#999999") for s in counts.index]
        self.pie.axes.pie(counts.values, labels=counts.index, autopct="%1.0f%%",
                           colors=colors, textprops={"fontsize": 7, "color": "#f1f5f9"})
        self.pie.axes.set_title("Segment Distribution", fontsize=11, color=NAVY, fontweight="bold")
        self.pie.draw()
