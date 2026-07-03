"""
Decision Tree Tab
-----------------
Trains a single interpretable DecisionTreeClassifier and presents:

  Panel A  —  Controls (depth slider, target column selector) and KPI cards.
  Panel B  —  Zoomable, scrollable Matplotlib tree visualization.
  Panel C  —  Filterable customer list showing model predictions.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableView, QMessageBox, QSlider, QScrollArea, QFrame,
    QFileDialog, QHeaderView, QSizePolicy, QSplitter, QComboBox,
)
from PyQt6.QtCore import Qt

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from sklearn import tree as sk_tree
import pandas as pd
import numpy as np

from ..ml_engine import DecisionTreePredictor
from .widgets import PandasTableModel, KpiCard
from .styles import BLUE_ACCENT, GREEN, AMBER, RED, BORDER_COLOR, TEXT_DARK, TEXT_MUTED

# DPI used for figure rendering size calculations
_DPI = 100


# ─── canvas ───────────────────────────────────────────────────────────────────

class _TreeCanvas(FigureCanvasQTAgg):
    """Zoomable Matplotlib canvas for a decision tree (no True/False labels overlay)."""

    BG        = "#12122a"
    BASE_DPI  = 90
    ZOOM_STEP = 0.20
    MIN_ZOOM  = 0.30
    MAX_ZOOM  = 4.00

    def __init__(self):
        self._fig = Figure(dpi=self.BASE_DPI, facecolor=self.BG)
        self._ax  = self._fig.add_subplot(111)
        super().__init__(self._fig)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Persisted across zoom re-renders
        self._model        = None
        self._feature_names: list = []
        self._max_depth: int      = 4
        self._zoom: float         = 1.0
        self._base_w_in: float    = 14.0
        self._base_h_in: float    = 8.0

        self._init_axes()

    def _init_axes(self):
        self._ax.set_facecolor(self.BG)
        self._ax.set_axis_off()
        for sp in self._ax.spines.values():
            sp.set_visible(False)

    def _compute_base_size(self):
        n_leaves = self._model.get_n_leaves()
        self._base_w_in = max(14.0, n_leaves * 1.8)
        self._base_h_in = max(7.0,  self._max_depth * 1.8)

    def _apply_canvas_size(self):
        dpi  = self.BASE_DPI * self._zoom
        w_px = int(self._base_w_in * dpi)
        h_px = int(self._base_h_in * dpi)
        self._fig.set_dpi(dpi)
        self._fig.set_size_inches(self._base_w_in, self._base_h_in)
        self.resize(w_px, h_px)
        self.setMinimumSize(w_px, h_px)

    def _do_render(self):
        """Full render cycle (used by both initial render and zoom)."""
        self._apply_canvas_size()
        self._ax.clear()
        self._init_axes()

        class_names = [str(c) for c in self._model.classes_] if hasattr(self._model, "classes_") else None

        sk_tree.plot_tree(
            self._model,
            feature_names=self._feature_names,
            class_names=class_names,
            filled=True,
            rounded=True,
            fontsize=max(7, 11 - self._max_depth),
            ax=self._ax,
            impurity=True,
            precision=3,
        )

        self._fig.tight_layout(pad=1.2)
        super().draw()

    # ── public API ────────────────────────────────────────────────────────────

    def render_tree(self, model, feature_names: list, max_depth: int):
        self._model         = model
        self._feature_names = feature_names
        self._max_depth     = max_depth
        self._zoom          = 1.0
        self._compute_base_size()
        self._do_render()

    def zoom_in(self) -> float:
        if self._model is None:
            return self._zoom
        self._zoom = min(round(self._zoom + self.ZOOM_STEP, 2), self.MAX_ZOOM)
        self._do_render()
        return self._zoom

    def zoom_out(self) -> float:
        if self._model is None:
            return self._zoom
        self._zoom = max(round(self._zoom - self.ZOOM_STEP, 2), self.MIN_ZOOM)
        self._do_render()
        return self._zoom

    def reset_zoom(self) -> float:
        if self._model is None:
            return self._zoom
        self._zoom = 1.0
        self._do_render()
        return self._zoom

    @property
    def zoom_pct(self) -> int:
        return int(round(self._zoom * 100))


# ─── tab ──────────────────────────────────────────────────────────────────────

class DecisionTreeTab(QWidget):

    def __init__(self, app_state):
        super().__init__()
        self.app_state    = app_state
        self.dt_scored_df = None
        self._build_ui()

    # ── construction ──────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # Header
        title = QLabel("Decision Tree Classifier")
        title.setObjectName("sectionTitle")
        subtitle = QLabel(
            "An interpretable decision tree classifier. Select any target column in your dataset "
            "to assess. The model automatically trains on all other relevant numeric features, "
            "revealing the exact splitting logic."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(subtitle)

        # ── Controls bar ──────────────────────────────────────────────────────
        ctrl_frame = QFrame()
        ctrl_frame.setObjectName("kpiCard")
        ctrl = QHBoxLayout(ctrl_frame)
        ctrl.setContentsMargins(16, 12, 16, 12)
        ctrl.setSpacing(20)

        # Depth Slider
        lbl = QLabel("Tree Depth:")
        lbl.setStyleSheet(f"color: {TEXT_DARK}; font-weight: 600;")
        self.depth_value_label = QLabel("4")
        self.depth_value_label.setStyleSheet(
            f"color: {BLUE_ACCENT}; font-size: 16px; font-weight: 700; min-width: 22px;"
        )
        self.depth_slider = QSlider(Qt.Orientation.Horizontal)
        self.depth_slider.setRange(2, 8)
        self.depth_slider.setValue(4)
        self.depth_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.depth_slider.setTickInterval(1)
        self.depth_slider.setFixedWidth(160)
        self.depth_slider.valueChanged.connect(
            lambda v: self.depth_value_label.setText(str(v))
        )
        self.depth_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {BORDER_COLOR}; height: 4px; border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {BLUE_ACCENT}; width: 14px; height: 14px;
                margin: -5px 0; border-radius: 7px;
            }}
            QSlider::sub-page:horizontal {{
                background: {BLUE_ACCENT}; border-radius: 2px;
            }}
        """)

        # Target Column Selector
        target_lbl = QLabel("Target Column:")
        target_lbl.setStyleSheet(f"color: {TEXT_DARK}; font-weight: 600;")
        self.target_combo = QComboBox()
        self.target_combo.setMinimumWidth(150)

        ctrl.addWidget(lbl)
        ctrl.addWidget(self.depth_slider)
        ctrl.addWidget(self.depth_value_label)
        ctrl.addWidget(target_lbl)
        ctrl.addWidget(self.target_combo)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color: {BORDER_COLOR};")
        ctrl.addWidget(sep)

        self.train_btn = QPushButton("Train Decision Tree")
        self.train_btn.clicked.connect(self._train)
        ctrl.addWidget(self.train_btn)

        self.export_btn = QPushButton("Save as PNG")
        self.export_btn.setObjectName("secondary")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export_png)
        ctrl.addWidget(self.export_btn)

        ctrl.addStretch()
        root.addWidget(ctrl_frame)

        # ── KPI cards ─────────────────────────────────────────────────────────
        kpi_row = QHBoxLayout()
        self.kpi_acc    = KpiCard("Accuracy",             "—", BLUE_ACCENT)
        self.kpi_prec   = KpiCard("Precision (Weighted)", "—", GREEN)
        self.kpi_recall = KpiCard("Recall (Weighted)",    "—", AMBER)
        self.kpi_f1     = KpiCard("F1 Score (Weighted)",  "—", RED)
        for card in (self.kpi_acc, self.kpi_prec, self.kpi_recall, self.kpi_f1):
            kpi_row.addWidget(card)
        root.addLayout(kpi_row)

        # ── Splitter ──────────────────────────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)

        # Tree panel
        tree_outer = QWidget()
        tv = QVBoxLayout(tree_outer)
        tv.setContentsMargins(0, 0, 0, 0)
        tv.setSpacing(6)

        # Toolbar with title and zoom controls
        toolbar = QHBoxLayout()
        tree_lbl = QLabel("Tree Visualisation")
        tree_lbl.setObjectName("sectionTitle")
        toolbar.addWidget(tree_lbl)
        toolbar.addStretch()

        zlbl = QLabel("Zoom:")
        zlbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        toolbar.addWidget(zlbl)

        self.zoom_out_btn = QPushButton("−")
        self.zoom_out_btn.setObjectName("secondary")
        self.zoom_out_btn.setFixedSize(32, 32)
        self.zoom_out_btn.setEnabled(False)
        self.zoom_out_btn.clicked.connect(self._zoom_out)
        toolbar.addWidget(self.zoom_out_btn)

        self.zoom_pct_label = QLabel("100%")
        self.zoom_pct_label.setStyleSheet(
            f"color: {TEXT_DARK}; font-weight: 700; font-size: 13px; min-width: 46px;"
        )
        self.zoom_pct_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toolbar.addWidget(self.zoom_pct_label)

        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setObjectName("secondary")
        self.zoom_in_btn.setFixedSize(32, 32)
        self.zoom_in_btn.setEnabled(False)
        self.zoom_in_btn.clicked.connect(self._zoom_in)
        toolbar.addWidget(self.zoom_in_btn)

        self.zoom_reset_btn = QPushButton("Reset")
        self.zoom_reset_btn.setObjectName("secondary")
        self.zoom_reset_btn.setEnabled(False)
        self.zoom_reset_btn.clicked.connect(self._zoom_reset)
        toolbar.addWidget(self.zoom_reset_btn)

        tv.addLayout(toolbar)

        self.tree_placeholder = QLabel(
            "Train the model using the controls above to render the decision tree diagram."
        )
        self.tree_placeholder.setObjectName("pageSubtitle")
        self.tree_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tree_placeholder.setMinimumHeight(120)
        tv.addWidget(self.tree_placeholder)

        self.tree_canvas = _TreeCanvas()
        self.tree_canvas.setVisible(False)

        self.tree_scroll = QScrollArea()
        self.tree_scroll.setWidgetResizable(False)
        self.tree_scroll.setWidget(self.tree_canvas)
        self.tree_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.tree_scroll.setStyleSheet("background-color: #12122a;")
        self.tree_scroll.setVisible(False)
        tv.addWidget(self.tree_scroll, stretch=1)

        splitter.addWidget(tree_outer)

        # Table panel
        tbl_outer = QWidget()
        tbv = QVBoxLayout(tbl_outer)
        tbv.setContentsMargins(0, 0, 0, 0)
        tbv.setSpacing(6)

        thdr = QHBoxLayout()
        tbl_title = QLabel("Model Predictions Table")
        tbl_title.setObjectName("sectionTitle")
        thdr.addWidget(tbl_title)
        thdr.addStretch()
        
        self.filter_lbl = QLabel("Filter by risk tier:")
        self.filter_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        thdr.addWidget(self.filter_lbl)
        
        self.risk_filter = QComboBox()
        self.risk_filter.addItems(["All", "High", "Medium", "Low"])
        self.risk_filter.currentTextChanged.connect(self._apply_filter)
        thdr.addWidget(self.risk_filter)
        tbv.addLayout(thdr)

        self.risk_table = QTableView()
        self.risk_table.setAlternatingRowColors(True)
        self.risk_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )
        self.risk_model = PandasTableModel()
        self.risk_table.setModel(self.risk_model)
        tbv.addWidget(self.risk_table)

        splitter.addWidget(tbl_outer)
        splitter.setSizes([460, 240])
        root.addWidget(splitter, stretch=1)

    # ── training ──────────────────────────────────────────────────────────────

    def _train(self):
        df = self.app_state.raw_df
        if df is None or df.empty:
            QMessageBox.warning(self, "No Data",
                                "Load a dataset in the Data Explorer tab first.")
            return

        target_col = self.target_combo.currentText()
        if not target_col:
            QMessageBox.warning(self, "No Target Column",
                                "Please select a target column to train the model.")
            return

        # Dynamically discover numeric columns to use as features (excluding target, ids, and dates)
        feature_cols = [
            col for col in df.columns
            if pd.api.types.is_numeric_dtype(df[col])
            and col != target_col
            and col.lower() not in ["customer_id", "id", "signup_date"]
            and not col.lower().endswith("_id")
            and not col.lower().endswith("_date")
        ]

        if not feature_cols:
            QMessageBox.warning(self, "No Feature Columns",
                                "Could not find any numeric feature columns to use for training.")
            return

        depth = self.depth_slider.value()
        predictor = DecisionTreePredictor(max_depth=depth)
        try:
            metrics = predictor.train(df, target_col=target_col, feature_cols=feature_cols)
        except Exception as exc:
            QMessageBox.critical(self, "Training Failed", str(exc))
            return

        self.app_state.dt_engine = predictor
        scored = predictor.predict_all(df)
        self.dt_scored_df = scored
        self.app_state.dt_scored_df = scored

        self.kpi_acc.set_value(f"{metrics['accuracy']:.1%}")
        self.kpi_prec.set_value(f"{metrics['precision']:.1%}")
        self.kpi_recall.set_value(f"{metrics['recall']:.1%}")
        self.kpi_f1.set_value(f"{metrics['f1']:.3f}")

        self.tree_placeholder.setVisible(False)
        self.tree_canvas.setVisible(True)
        self.tree_scroll.setVisible(True)
        self.tree_canvas.render_tree(
            predictor.model,
            feature_names=feature_cols,
            max_depth=depth,
        )
        self._update_zoom_label()
        self._set_zoom_enabled(True)
        self.export_btn.setEnabled(True)
        self._apply_filter(self.risk_filter.currentText())

        # Update table risk controls visibility based on binary target
        is_binary_target = ("dt_risk_tier" in scored.columns and "N/A" not in scored["dt_risk_tier"].values)
        self.filter_lbl.setVisible(is_binary_target)
        self.risk_filter.setVisible(is_binary_target)

        QMessageBox.information(
            self, "Training Complete",
            f"Decision Tree trained on target '{target_col}' (depth {depth}).\n\n"
            f"Training records : {metrics['n_train']:,}\n"
            f"Test records     : {metrics['n_test']:,}\n\n"
            f"Accuracy  : {metrics['accuracy']:.1%}\n"
            f"Precision : {metrics['precision']:.1%}\n"
            f"Recall    : {metrics['recall']:.1%}\n"
            f"F1 Score  : {metrics['f1']:.3f}"
        )

    # ── zoom ──────────────────────────────────────────────────────────────────

    def _zoom_in(self):
        self.tree_canvas.zoom_in()
        self._update_zoom_label()

    def _zoom_out(self):
        self.tree_canvas.zoom_out()
        self._update_zoom_label()

    def _zoom_reset(self):
        self.tree_canvas.reset_zoom()
        self._update_zoom_label()

    def _update_zoom_label(self):
        self.zoom_pct_label.setText(f"{self.tree_canvas.zoom_pct}%")

    def _set_zoom_enabled(self, state: bool):
        for btn in (self.zoom_in_btn, self.zoom_out_btn, self.zoom_reset_btn):
            btn.setEnabled(state)

    # ── table filter ──────────────────────────────────────────────────────────

    def _apply_filter(self, tier: str):
        if self.dt_scored_df is None:
            return
        
        target_col = self.target_combo.currentText()
        wanted = [
            "customer_id", target_col, "dt_prediction", "dt_probability", "dt_risk_tier"
        ]
        
        # Pull key behavioral features as context if they exist
        context_cols = ["recency_days", "frequency", "monetary", "avg_satisfaction_score", "support_tickets"]
        for c in context_cols:
            if c in self.dt_scored_df.columns and c != target_col:
                wanted.append(c)

        cols = [c for c in wanted if c in self.dt_scored_df.columns]
        
        sort_col = "dt_probability" if "dt_probability" in self.dt_scored_df.columns else "dt_prediction"
        df = self.dt_scored_df[cols].sort_values(sort_col, ascending=False)
        
        if tier != "All" and "dt_risk_tier" in df.columns:
            df = df[df["dt_risk_tier"] == tier]
            
        self.risk_model.set_dataframe(df.reset_index(drop=True))
        self.risk_table.resizeColumnsToContents()

    # ── PNG export ────────────────────────────────────────────────────────────

    def _export_png(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Tree Diagram", "decision_tree.png", "PNG Image (*.png)"
        )
        if not path:
            return
        try:
            self.tree_canvas._fig.savefig(
                path, dpi=150, bbox_inches="tight",
                facecolor=self.tree_canvas.BG,
            )
            QMessageBox.information(self, "Exported", f"Tree diagram saved:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", str(exc))

    # ── reset on new data ─────────────────────────────────────────────────────

    def reset(self, df=None):
        self.dt_scored_df = None
        self.app_state.dt_engine = None
        self.app_state.dt_scored_df = None

        for card in (self.kpi_acc, self.kpi_prec, self.kpi_recall, self.kpi_f1):
            card.set_value("—")

        self.tree_canvas.setVisible(False)
        self.tree_scroll.setVisible(False)
        self.tree_placeholder.setVisible(True)
        self.export_btn.setEnabled(False)
        self._set_zoom_enabled(False)
        self.zoom_pct_label.setText("100%")

        # Populate target columns dropdown
        self.target_combo.blockSignals(True)
        self.target_combo.clear()
        
        if df is not None and not df.empty:
            candidates = []
            for col in df.columns:
                col_lower = col.lower()
                # Skip obvious ID, date, or primary timestamp columns
                if col_lower in ["customer_id", "id", "signup_date"] or col_lower.endswith("_id") or col_lower.endswith("_date"):
                    continue
                candidates.append(col)
            
            self.target_combo.addItems(candidates)
            if "churned" in df.columns:
                self.target_combo.setCurrentText("churned")
            elif candidates:
                self.target_combo.setCurrentIndex(0)
                
        self.target_combo.blockSignals(False)

        self.risk_model.set_dataframe(pd.DataFrame())
