from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableView, QMessageBox, QLineEdit, QComboBox, QSpinBox,
    QGridLayout, QFrame, QHeaderView, QScrollArea, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
import pandas as pd
from datetime import datetime

from .widgets import PandasTableModel
from .styles import RED, GREEN, BLUE_ACCENT, BORDER_COLOR


class CrmTab(QWidget):
    data_changed = pyqtSignal(pd.DataFrame)

    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self.filtered_df = pd.DataFrame()
        self.selected_customer_id = None
        self._build_ui()

    def _build_ui(self):
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Left Column: List and Search
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        title = QLabel("CRM Customer Directory")
        title.setObjectName("sectionTitle")
        subtitle = QLabel("Search, view, and manage customer records.")
        subtitle.setObjectName("pageSubtitle")
        left_layout.addWidget(title)
        left_layout.addWidget(subtitle)

        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by Customer ID...")
        self.search_box.textChanged.connect(self.search_changed)
        left_layout.addWidget(self.search_box)

        # Customer List Table
        self.list_table = QTableView()
        self.list_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.list_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_table.setAlternatingRowColors(True)
        self.list_model = PandasTableModel()
        self.list_table.setModel(self.list_model)
        self.list_table.clicked.connect(self.customer_selected)
        left_layout.addWidget(self.list_table, stretch=1)

        main_layout.addWidget(left_widget, stretch=3)

        # Right Column: Editor Form
        right_widget = QFrame()
        right_widget.setObjectName("kpiCard")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(12)

        form_title = QLabel("Customer Editor")
        form_title.setObjectName("sectionTitle")
        right_layout.addWidget(form_title)

        # Scrollable form area for the fields
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")

        form_container = QWidget()
        form_container.setStyleSheet("background-color: transparent;")
        grid = QGridLayout(form_container)
        grid.setSpacing(10)

        # Set up fields
        self.inputs = {}
        
        # Grid positions
        # Row 0: Basic
        grid.addWidget(QLabel("Customer ID:"), 0, 0)
        self.inputs["customer_id"] = QLineEdit()
        grid.addWidget(self.inputs["customer_id"], 0, 1)

        grid.addWidget(QLabel("Age:"), 0, 2)
        self.inputs["age"] = QSpinBox()
        self.inputs["age"].setRange(1, 120)
        self.inputs["age"].setValue(30)
        grid.addWidget(self.inputs["age"], 0, 3)

        # Row 1: Demographics
        grid.addWidget(QLabel("Gender:"), 1, 0)
        self.inputs["gender"] = QComboBox()
        self.inputs["gender"].addItems(["Male", "Female", "Other"])
        grid.addWidget(self.inputs["gender"], 1, 1)

        grid.addWidget(QLabel("Signup Date (YYYY-MM-DD):"), 1, 2)
        self.inputs["signup_date"] = QLineEdit()
        self.inputs["signup_date"].setText(datetime.now().strftime("%Y-%m-%d"))
        grid.addWidget(self.inputs["signup_date"], 1, 3)

        # Row 2: Account stats
        grid.addWidget(QLabel("Tenure (days):"), 2, 0)
        self.inputs["tenure_days"] = QSpinBox()
        self.inputs["tenure_days"].setRange(0, 10000)
        self.inputs["tenure_days"].setValue(100)
        grid.addWidget(self.inputs["tenure_days"], 2, 1)

        grid.addWidget(QLabel("Preferred Channel:"), 2, 2)
        self.inputs["preferred_channel"] = QComboBox()
        self.inputs["preferred_channel"].addItems(["Mobile App", "Website", "In-Store"])
        grid.addWidget(self.inputs["preferred_channel"], 2, 3)

        # Row 3: Transaction values (RFM)
        grid.addWidget(QLabel("Recency (days):"), 3, 0)
        self.inputs["recency_days"] = QSpinBox()
        self.inputs["recency_days"].setRange(0, 10000)
        self.inputs["recency_days"].setValue(10)
        grid.addWidget(self.inputs["recency_days"], 3, 1)

        grid.addWidget(QLabel("Frequency (orders):"), 3, 2)
        self.inputs["frequency"] = QSpinBox()
        self.inputs["frequency"].setRange(0, 10000)
        self.inputs["frequency"].setValue(5)
        grid.addWidget(self.inputs["frequency"], 3, 3)

        # Row 4: Spend metrics
        grid.addWidget(QLabel("Monetary (Spend):"), 4, 0)
        self.inputs["monetary"] = QLineEdit()
        self.inputs["monetary"].setText("500.00")
        grid.addWidget(self.inputs["monetary"], 4, 1)

        grid.addWidget(QLabel("Avg Order Value:"), 4, 2)
        self.inputs["avg_order_value"] = QLineEdit()
        self.inputs["avg_order_value"].setText("100.00")
        grid.addWidget(self.inputs["avg_order_value"], 4, 3)

        # Row 5: Shopping behaviors
        grid.addWidget(QLabel("Categories Purchased:"), 5, 0)
        self.inputs["num_categories_purchased"] = QSpinBox()
        self.inputs["num_categories_purchased"].setRange(0, 100)
        self.inputs["num_categories_purchased"].setValue(3)
        grid.addWidget(self.inputs["num_categories_purchased"], 5, 1)

        grid.addWidget(QLabel("Num Returns:"), 5, 2)
        self.inputs["num_returns"] = QSpinBox()
        self.inputs["num_returns"].setRange(0, 1000)
        self.inputs["num_returns"].setValue(0)
        grid.addWidget(self.inputs["num_returns"], 5, 3)

        # Row 6: Return Rates & Support
        grid.addWidget(QLabel("Return Rate (0-1):"), 6, 0)
        self.inputs["return_rate"] = QLineEdit()
        self.inputs["return_rate"].setText("0.0")
        grid.addWidget(self.inputs["return_rate"], 6, 1)

        grid.addWidget(QLabel("Support Tickets:"), 6, 2)
        self.inputs["support_tickets"] = QSpinBox()
        self.inputs["support_tickets"].setRange(0, 1000)
        self.inputs["support_tickets"].setValue(0)
        grid.addWidget(self.inputs["support_tickets"], 6, 3)

        # Row 7: Satisfaction & Email
        grid.addWidget(QLabel("Avg Satisfaction (1-5):"), 7, 0)
        self.inputs["avg_satisfaction_score"] = QLineEdit()
        self.inputs["avg_satisfaction_score"].setText("4.0")
        grid.addWidget(self.inputs["avg_satisfaction_score"], 7, 1)

        grid.addWidget(QLabel("Email Open Rate (0-1):"), 7, 2)
        self.inputs["email_open_rate"] = QLineEdit()
        self.inputs["email_open_rate"].setText("0.5")
        grid.addWidget(self.inputs["email_open_rate"], 7, 3)

        # Row 8: Discount & Program memberships
        grid.addWidget(QLabel("Discount Usage (0-1):"), 8, 0)
        self.inputs["discount_usage_rate"] = QLineEdit()
        self.inputs["discount_usage_rate"].setText("0.2")
        grid.addWidget(self.inputs["discount_usage_rate"], 8, 1)

        grid.addWidget(QLabel("Loyalty Member:"), 8, 2)
        self.inputs["loyalty_member"] = QComboBox()
        self.inputs["loyalty_member"].addItems(["No (0)", "Yes (1)"])
        grid.addWidget(self.inputs["loyalty_member"], 8, 3)

        # Row 9: Churn Status
        grid.addWidget(QLabel("Churned Target:"), 9, 0)
        self.inputs["churned"] = QComboBox()
        self.inputs["churned"].addItems(["No (0)", "Yes (1)"])
        grid.addWidget(self.inputs["churned"], 9, 1)

        scroll.setWidget(form_container)
        right_layout.addWidget(scroll, stretch=1)

        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Customer")
        self.save_btn.clicked.connect(self.save_customer)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setStyleSheet(f"background-color: {RED}; color: white;")
        self.delete_btn.clicked.connect(self.delete_customer)
        
        self.clear_btn = QPushButton("New / Clear Form")
        self.clear_btn.setObjectName("secondary")
        self.clear_btn.clicked.connect(self.clear_form)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.clear_btn)
        right_layout.addLayout(btn_layout)

        main_layout.addWidget(right_widget, stretch=2)

    def refresh(self):
        """Loads or refreshes the customer list from app state."""
        df = self.app_state.raw_df
        if df is not None and not df.empty:
            self.filtered_df = df.copy()
            # Select subset of key fields for the list view to keep it neat
            list_cols = ["customer_id", "age", "gender", "preferred_channel", "monetary"]
            list_cols = [c for c in list_cols if c in df.columns]
            self.list_model.set_dataframe(df[list_cols])
            self.list_table.resizeColumnsToContents()
        else:
            self.filtered_df = pd.DataFrame()
            self.list_model.set_dataframe(pd.DataFrame())

    def search_changed(self, text):
        df = self.app_state.raw_df
        if df is None or df.empty:
            return
        if not text:
            self.filtered_df = df.copy()
        else:
            self.filtered_df = df[
                df["customer_id"].str.contains(text, case=False, na=False)
            ]
        
        list_cols = ["customer_id", "age", "gender", "preferred_channel", "monetary"]
        list_cols = [c for c in list_cols if c in df.columns]
        self.list_model.set_dataframe(self.filtered_df[list_cols])
        self.list_table.resizeColumnsToContents()

    def customer_selected(self, index):
        if not index.isValid() or self.filtered_df.empty:
            return
        
        row_id = index.row()
        cust_id = self.filtered_df.iloc[row_id]["customer_id"]
        
        # Fetch the complete customer record from the raw data
        full_df = self.app_state.raw_df
        record = full_df[full_df["customer_id"] == cust_id]
        if record.empty:
            return
        
        self.selected_customer_id = cust_id
        row_data = record.iloc[0]
        
        # Populate form
        self.inputs["customer_id"].setText(str(row_data["customer_id"]))
        self.inputs["customer_id"].setReadOnly(True)  # Don't allow changing ID while editing
        self.inputs["age"].setValue(int(row_data["age"]))
        
        gender = str(row_data["gender"])
        gender_idx = self.inputs["gender"].findText(gender)
        if gender_idx >= 0:
            self.inputs["gender"].setCurrentIndex(gender_idx)
            
        self.inputs["signup_date"].setText(str(row_data["signup_date"]))
        self.inputs["tenure_days"].setValue(int(row_data["tenure_days"]))
        
        channel = str(row_data["preferred_channel"])
        chan_idx = self.inputs["preferred_channel"].findText(channel)
        if chan_idx >= 0:
            self.inputs["preferred_channel"].setCurrentIndex(chan_idx)
            
        self.inputs["recency_days"].setValue(int(row_data["recency_days"]))
        self.inputs["frequency"].setValue(int(row_data["frequency"]))
        self.inputs["monetary"].setText(f"{float(row_data['monetary']):.2f}")
        self.inputs["avg_order_value"].setText(f"{float(row_data['avg_order_value']):.2f}")
        self.inputs["num_categories_purchased"].setValue(int(row_data["num_categories_purchased"]))
        self.inputs["num_returns"].setValue(int(row_data["num_returns"]))
        self.inputs["return_rate"].setText(f"{float(row_data['return_rate']):.3f}")
        self.inputs["support_tickets"].setValue(int(row_data["support_tickets"]))
        self.inputs["avg_satisfaction_score"].setText(f"{float(row_data['avg_satisfaction_score']):.2f}")
        self.inputs["email_open_rate"].setText(f"{float(row_data['email_open_rate']):.3f}")
        self.inputs["discount_usage_rate"].setText(f"{float(row_data['discount_usage_rate']):.3f}")
        
        loyalty = int(row_data["loyalty_member"])
        self.inputs["loyalty_member"].setCurrentIndex(1 if loyalty == 1 else 0)
        
        churned = int(row_data["churned"])
        self.inputs["churned"].setCurrentIndex(1 if churned == 1 else 0)

    def clear_form(self):
        self.selected_customer_id = None
        self.inputs["customer_id"].clear()
        self.inputs["customer_id"].setReadOnly(False)
        self.inputs["age"].setValue(30)
        self.inputs["gender"].setCurrentIndex(0)
        self.inputs["signup_date"].setText(datetime.now().strftime("%Y-%m-%d"))
        self.inputs["tenure_days"].setValue(100)
        self.inputs["preferred_channel"].setCurrentIndex(0)
        self.inputs["recency_days"].setValue(10)
        self.inputs["frequency"].setValue(5)
        self.inputs["monetary"].setText("500.00")
        self.inputs["avg_order_value"].setText("100.00")
        self.inputs["num_categories_purchased"].setValue(3)
        self.inputs["num_returns"].setValue(0)
        self.inputs["return_rate"].setText("0.0")
        self.inputs["support_tickets"].setValue(0)
        self.inputs["avg_satisfaction_score"].setText("4.0")
        self.inputs["email_open_rate"].setText("0.5")
        self.inputs["discount_usage_rate"].setText("0.2")
        self.inputs["loyalty_member"].setCurrentIndex(0)
        self.inputs["churned"].setCurrentIndex(0)

    def save_customer(self):
        df = self.app_state.raw_df
        if df is None:
            # Initialize empty df with proper column names
            cols = [
                "customer_id", "age", "gender", "signup_date", "tenure_days",
                "recency_days", "frequency", "monetary", "avg_order_value",
                "num_categories_purchased", "num_returns", "return_rate",
                "support_tickets", "avg_satisfaction_score", "email_open_rate",
                "discount_usage_rate", "preferred_channel", "loyalty_member", "churned"
            ]
            df = pd.DataFrame(columns=cols)
            self.app_state.raw_df = df

        cust_id = self.inputs["customer_id"].text().strip()
        if not cust_id:
            QMessageBox.warning(self, "Validation Error", "Customer ID cannot be empty.")
            return

        # Extract values
        try:
            record_data = {
                "customer_id": cust_id,
                "age": self.inputs["age"].value(),
                "gender": self.inputs["gender"].currentText(),
                "signup_date": self.inputs["signup_date"].text().strip(),
                "tenure_days": self.inputs["tenure_days"].value(),
                "recency_days": self.inputs["recency_days"].value(),
                "frequency": self.inputs["frequency"].value(),
                "monetary": float(self.inputs["monetary"].text()),
                "avg_order_value": float(self.inputs["avg_order_value"].text()),
                "num_categories_purchased": self.inputs["num_categories_purchased"].value(),
                "num_returns": self.inputs["num_returns"].value(),
                "return_rate": float(self.inputs["return_rate"].text()),
                "support_tickets": self.inputs["support_tickets"].value(),
                "avg_satisfaction_score": float(self.inputs["avg_satisfaction_score"].text()),
                "email_open_rate": float(self.inputs["email_open_rate"].text()),
                "discount_usage_rate": float(self.inputs["discount_usage_rate"].text()),
                "preferred_channel": self.inputs["preferred_channel"].currentText(),
                "loyalty_member": 1 if self.inputs["loyalty_member"].currentIndex() == 1 else 0,
                "churned": 1 if self.inputs["churned"].currentIndex() == 1 else 0
            }
        except ValueError as ve:
            QMessageBox.critical(self, "Validation Error", f"Ensure all numeric fields are correctly formatted:\n{ve}")
            return

        # If editing
        if self.selected_customer_id:
            idx = df[df["customer_id"] == self.selected_customer_id].index
            if not idx.empty:
                for key, val in record_data.items():
                    df.at[idx[0], key] = val
                msg = f"Customer '{cust_id}' updated successfully."
            else:
                QMessageBox.critical(self, "Error", "Could not locate customer to edit.")
                return
        else:
            # Check duplicates for new addition
            if cust_id in df["customer_id"].values:
                QMessageBox.warning(self, "Conflict", f"Customer ID '{cust_id}' already exists.")
                return
            
            # Append new record
            new_row = pd.DataFrame([record_data])
            df = pd.concat([df, new_row], ignore_index=True)
            self.app_state.raw_df = df
            msg = f"Customer '{cust_id}' added successfully."

        # Save to DB
        try:
            self.app_state.db.save_customers(self.app_state.raw_df, "customers")
        except Exception as e:
            QMessageBox.warning(self, "Database Error", f"Failed to save changes to DB:\n{e}")

        # Refresh
        self.refresh()
        self.search_changed(self.search_box.text())
        self.data_changed.emit(self.app_state.raw_df)
        
        QMessageBox.information(self, "Success", msg)
        self.clear_form()

    def delete_customer(self):
        if not self.selected_customer_id:
            QMessageBox.warning(self, "Selection Required", "Select a customer from the directory to delete.")
            return

        confirm = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to permanently delete customer '{self.selected_customer_id}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.No:
            return

        df = self.app_state.raw_df
        idx = df[df["customer_id"] == self.selected_customer_id].index
        if not idx.empty:
            df = df.drop(idx).reset_index(drop=True)
            self.app_state.raw_df = df
            
            # Save to SQLite database
            try:
                self.app_state.db.save_customers(df, "customers")
            except Exception as e:
                QMessageBox.warning(self, "Database Error", f"Failed to save deletion to DB:\n{e}")

            # Refresh views
            self.refresh()
            self.search_changed(self.search_box.text())
            self.data_changed.emit(df)
            
            QMessageBox.information(self, "Deleted", f"Customer '{self.selected_customer_id}' has been deleted.")
            self.clear_form()
        else:
            QMessageBox.critical(self, "Error", "Customer not found.")
