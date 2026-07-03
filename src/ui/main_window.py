from PyQt6.QtWidgets import QMainWindow, QTabWidget, QStatusBar
from PyQt6.QtCore import Qt

from .data_tab import DataTab
from .crm_tab import CrmTab
from .dashboard_tab import DashboardTab
from .segmentation_tab import SegmentationTab
from .churn_tab import ChurnTab
from .decision_tree_tab import DecisionTreeTab
from .ai_insights_tab import AiInsightsTab
from .styles import APP_STYLESHEET
from ..database import Database


class AppState:
    """Shared, in-memory state passed between tabs (no global singletons)."""
    def __init__(self):
        self.raw_df = None
        self.segmented_df = None
        self.scored_df = None
        self.segmentation_engine = None
        self.churn_engine = None
        self.dt_engine = None
        self.dt_scored_df = None
        self.db = Database()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Customer Insight CMS — Segmentation & Churn Prediction")
        self.resize(1280, 820)
        self.setStyleSheet(APP_STYLESHEET)

        self.app_state = AppState()

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.data_tab = DataTab(self.app_state)
        self.crm_tab = CrmTab(self.app_state)
        self.dashboard_tab = DashboardTab(self.app_state)
        self.segmentation_tab = SegmentationTab(self.app_state)
        self.churn_tab = ChurnTab(self.app_state)
        self.dt_tab = DecisionTreeTab(self.app_state)
        self.ai_tab = AiInsightsTab(self.app_state)

        self.tabs.addTab(self.data_tab, "Data Explorer")
        self.tabs.addTab(self.crm_tab, "CRM Panel")
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.segmentation_tab, "Segmentation")
        self.tabs.addTab(self.churn_tab, "Churn Prediction")
        self.tabs.addTab(self.dt_tab, "Decision Tree")
        self.tabs.addTab(self.ai_tab, "AI Insights")

        # Sync tab data changes
        self.data_tab.data_loaded.connect(self.dashboard_tab.refresh)
        self.data_tab.data_loaded.connect(self.crm_tab.refresh)
        self.data_tab.data_loaded.connect(self.dt_tab.reset)
        self.data_tab.data_loaded.connect(
            lambda df: self.ai_tab.report_viewer.setHtml(self.ai_tab._get_initial_html())
        )
        
        self.crm_tab.data_changed.connect(self.dashboard_tab.refresh)
        self.crm_tab.data_changed.connect(self.data_tab.model.set_dataframe)
        self.crm_tab.data_changed.connect(
            lambda df: self.data_tab.status_label.setText(
                f"Syncing {len(df):,} rows from database updates."
            )
        )
        self.crm_tab.data_changed.connect(
            lambda df: self.ai_tab.report_viewer.setHtml(self.ai_tab._get_initial_html())
        )

        # Check if database has saved customers, and load them automatically on startup
        if self.app_state.db.table_exists("customers"):
            saved_df = self.app_state.db.load_customers("customers")
            if not saved_df.empty:
                self.app_state.raw_df = saved_df
                self.data_tab.model.set_dataframe(saved_df)
                self.data_tab.status_label.setText(
                    f"Loaded {len(saved_df):,} rows automatically from SQLite database."
                )
                self.dashboard_tab.refresh(saved_df)
                self.crm_tab.refresh()
                self.dt_tab.reset(saved_df)

        status = QStatusBar()
        status.showMessage("Ready. Start in Data Explorer to import or generate a dataset.")
        self.setStatusBar(status)

    def closeEvent(self, event):
        self.app_state.db.close()
        super().closeEvent(event)
