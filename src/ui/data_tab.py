from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableView, QFileDialog, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
import pandas as pd

from .widgets import PandasTableModel
from ..data_generator import generate_customers


class DataTab(QWidget):
    data_loaded = pyqtSignal(pd.DataFrame)

    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Data Explorer")
        title.setObjectName("sectionTitle")
        subtitle = QLabel("Import a customer CSV or generate a sample e-commerce dataset to explore below.")
        subtitle.setObjectName("pageSubtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        btn_row = QHBoxLayout()
        self.load_btn = QPushButton("Import CSV…")
        self.load_btn.clicked.connect(self.import_csv)

        self.generate_btn = QPushButton("Generate Sample Dataset (2000 customers)")
        self.generate_btn.setObjectName("secondary")
        self.generate_btn.clicked.connect(self.generate_sample)

        self.status_label = QLabel("No data loaded.")
        self.status_label.setObjectName("pageSubtitle")

        btn_row.addWidget(self.load_btn)
        btn_row.addWidget(self.generate_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        layout.addWidget(self.status_label)

        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.model = PandasTableModel()
        self.table.setModel(self.model)
        layout.addWidget(self.table, stretch=1)

    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Customer CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            df = pd.read_csv(path)
            self._apply_dataset(df, source=path)
        except Exception as e:
            QMessageBox.critical(self, "Import Failed", f"Could not read CSV:\n{e}")

    def generate_sample(self):
        df = generate_customers(2000)
        self._apply_dataset(df, source="Generated sample dataset")

    def _apply_dataset(self, df: pd.DataFrame, source: str):
        required = {"customer_id", "recency_days", "frequency", "monetary"}
        missing = required - set(df.columns)
        if missing:
            QMessageBox.warning(
                self, "Missing Columns",
                f"Dataset is missing required columns for ML features: {', '.join(missing)}\n"
                "The table will still display, but segmentation/churn tabs may fail."
            )
        self.model.set_dataframe(df)
        self.status_label.setText(f"Loaded {len(df):,} rows from: {source}")
        self.app_state.raw_df = df
        
        # Save to SQLite database
        try:
            self.app_state.db.save_customers(df, "customers")
        except Exception as e:
            QMessageBox.warning(self, "Database Save Error", f"Could not save data to database:\n{str(e)}")
            
        self.data_loaded.emit(df)
