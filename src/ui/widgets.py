"""Reusable widgets shared across tabs."""

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
import pandas as pd


class PandasTableModel(QAbstractTableModel):
    """Read-only Qt table model backed by a pandas DataFrame."""

    def __init__(self, df: pd.DataFrame = None):
        super().__init__()
        self._df = df if df is not None else pd.DataFrame()

    def set_dataframe(self, df: pd.DataFrame):
        self.beginResetModel()
        self._df = df
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._df)

    def columnCount(self, parent=QModelIndex()):
        return len(self._df.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            value = self._df.iat[index.row(), index.column()]
            if isinstance(value, float):
                return f"{value:,.2f}"
            return str(value)
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return str(self._df.columns[section])
        return str(section + 1)


class KpiCard(QFrame):
    def __init__(self, label: str, value: str, accent: str = "#3b82f6"):
        super().__init__()
        self.setObjectName("kpiCard")
        self.setMinimumHeight(90)
        self.setStyleSheet(f"QFrame#kpiCard {{ border-left: 4px solid {accent}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)

        self.value_label = QLabel(value)
        self.value_label.setObjectName("kpiValue")

        label_widget = QLabel(label.upper())
        label_widget.setObjectName("kpiLabel")

        layout.addWidget(self.value_label)
        layout.addWidget(label_widget)

    def set_value(self, value: str):
        self.value_label.setText(value)
