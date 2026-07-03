from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout
import pandas as pd

from .widgets import KpiCard
from .mpl_canvas import MplCanvas
from .styles import BLUE_ACCENT, GREEN, AMBER, RED, NAVY


class DashboardTab(QWidget):
    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Dashboard")
        title.setObjectName("sectionTitle")
        subtitle = QLabel("Overview of the currently loaded customer base.")
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        kpi_row = QHBoxLayout()
        self.kpi_total = KpiCard("Total Customers", "—", BLUE_ACCENT)
        self.kpi_churn = KpiCard("Churn Rate", "—", RED)
        self.kpi_revenue = KpiCard("Avg. Customer Value", "—", GREEN)
        self.kpi_loyalty = KpiCard("Loyalty Members", "—", AMBER)
        for card in (self.kpi_total, self.kpi_churn, self.kpi_revenue, self.kpi_loyalty):
            kpi_row.addWidget(card)
        layout.addLayout(kpi_row)

        chart_row = QHBoxLayout()
        self.churn_pie = MplCanvas(width=4, height=3.2)
        self.monetary_hist = MplCanvas(width=4, height=3.2)
        self.channel_bar = MplCanvas(width=4, height=3.2)
        chart_row.addWidget(self.churn_pie)
        chart_row.addWidget(self.monetary_hist)
        chart_row.addWidget(self.channel_bar)
        layout.addLayout(chart_row, stretch=1)

        self.empty_label = QLabel("Load data in the Data Explorer tab to populate the dashboard.")
        self.empty_label.setObjectName("pageSubtitle")
        layout.addWidget(self.empty_label)

    def refresh(self, df: pd.DataFrame):
        if df is None or df.empty:
            return
        self.empty_label.setText("")

        self.kpi_total.set_value(f"{len(df):,}")

        if "churned" in df.columns:
            churn_rate = df["churned"].mean()
            self.kpi_churn.set_value(f"{churn_rate:.1%}")
        else:
            self.kpi_churn.set_value("N/A")

        if "monetary" in df.columns:
            self.kpi_revenue.set_value(f"R {df['monetary'].mean():,.0f}")
        else:
            self.kpi_revenue.set_value("N/A")

        if "loyalty_member" in df.columns:
            self.kpi_loyalty.set_value(f"{df['loyalty_member'].mean():.1%}")
        else:
            self.kpi_loyalty.set_value("N/A")

        # Churn pie
        self.churn_pie.clear()
        if "churned" in df.columns:
            counts = df["churned"].value_counts().sort_index()
            labels = ["Active", "Churned"]
            colors = [GREEN, RED]
            self.churn_pie.axes.pie(
                counts.values, labels=labels, autopct="%1.1f%%",
                colors=colors, textprops={"fontsize": 8, "color": "#f1f5f9"}
            )
        self.churn_pie.axes.set_title("Churn Split", fontsize=10, color=NAVY, fontweight="bold")
        self.churn_pie.draw()

        # Monetary distribution
        self.monetary_hist.clear()
        if "monetary" in df.columns:
            self.monetary_hist.axes.hist(df["monetary"], bins=25, color=BLUE_ACCENT, edgecolor="white")
        self.monetary_hist.axes.set_title("Customer Spend Distribution", fontsize=10, color=NAVY, fontweight="bold")
        self.monetary_hist.axes.set_xlabel("Total Spend (12mo)", fontsize=8)
        self.monetary_hist.axes.set_ylabel("Customers", fontsize=8)
        self.monetary_hist.axes.tick_params(labelsize=7)
        self.monetary_hist.draw()

        # Channel breakdown
        self.channel_bar.clear()
        if "preferred_channel" in df.columns:
            counts = df["preferred_channel"].value_counts()
            self.channel_bar.axes.bar(counts.index, counts.values, color=[BLUE_ACCENT, AMBER, GREEN])
        self.channel_bar.axes.set_title("Preferred Channel", fontsize=10, color=NAVY, fontweight="bold")
        self.channel_bar.axes.tick_params(labelsize=7)
        self.channel_bar.draw()
