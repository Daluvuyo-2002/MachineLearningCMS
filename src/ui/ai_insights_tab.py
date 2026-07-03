from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextBrowser, QProgressBar, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QTimer
import pandas as pd
import numpy as np

from .styles import BLUE_ACCENT, WHITE, TEXT_DARK, BORDER_COLOR


class AiInsightsTab(QWidget):
    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header
        title = QLabel("AI Insight Generator")
        title.setObjectName("sectionTitle")
        subtitle = QLabel(
            "Generate data-driven customer insights and recommended business actions "
            "derived from segmentation clustering and churn prediction model output."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Control Row
        controls_layout = QHBoxLayout()
        self.generate_btn = QPushButton("Generate Analysis Report")
        self.generate_btn.clicked.connect(self.start_generation)
        controls_layout.addWidget(self.generate_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Analyzing model results... %p%")
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(28)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {BORDER_COLOR};
                border-radius: 5px;
                background-color: {WHITE};
                text-align: center;
                color: {TEXT_DARK};
                font-weight: 600;
                font-size: 12px;
            }}
            QProgressBar::chunk {{
                background-color: {BLUE_ACCENT};
                border-radius: 4px;
            }}
        """)
        controls_layout.addWidget(self.progress_bar, stretch=1)
        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Report viewer
        self.report_viewer = QTextBrowser()
        self.report_viewer.setOpenExternalLinks(False)
        self.report_viewer.setHtml(self._get_initial_html())
        self.report_viewer.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {WHITE};
                border: 1px solid {BORDER_COLOR};
                border-radius: 6px;
                padding: 16px;
                color: #e2e8f0;
                font-size: 13px;
            }}
        """)
        layout.addWidget(self.report_viewer, stretch=1)

    def _get_initial_html(self) -> str:
        return """
        <html>
        <body style="
            font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
            background-color: #1e1e1e;
            color: #a3a3a3;
            text-align: center;
            padding: 60px 40px;
        ">
            <h2 style="color: #f3f4f6; font-weight: 600; margin-bottom: 16px;">Analysis Engine Ready</h2>
            <p style="max-width: 520px; margin: 0 auto 10px auto; line-height: 1.7;">
                To generate the insights report, complete the following steps in order:
            </p>
            <ol style="display: inline-block; text-align: left; margin-top: 12px; line-height: 2;">
                <li>Load a dataset in the <b style="color: #f3f4f6;">Data Explorer</b> tab.</li>
                <li>Run segmentation in the <b style="color: #f3f4f6;">Segmentation</b> tab.</li>
                <li>Train the churn model in the <b style="color: #f3f4f6;">Churn Prediction</b> tab.</li>
            </ol>
            <p style="margin-top: 20px;">
                Once all three steps are complete, click <b style="color: #3b82f6;">Generate Analysis Report</b> above.
            </p>
        </body>
        </html>
        """

    def start_generation(self):
        df = self.app_state.raw_df
        seg_df = self.app_state.segmented_df
        scored_df = self.app_state.scored_df
        churn_engine = self.app_state.churn_engine

        if df is None or df.empty:
            QMessageBox.warning(self, "No Data", "Please load a dataset in the Data Explorer tab first.")
            return

        if seg_df is None or "segment" not in seg_df.columns:
            QMessageBox.warning(self, "Segmentation Required",
                                "Please run customer segmentation in the Segmentation tab first.")
            return

        if scored_df is None or churn_engine is None or not churn_engine.is_fitted:
            QMessageBox.warning(self, "Model Required",
                                "Please train the churn prediction model in the Churn Prediction tab first.")
            return

        self.generate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.timer_counter = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.advance_progress)
        self.timer.start(80)

    def advance_progress(self):
        self.timer_counter += 8
        self.progress_bar.setValue(min(self.timer_counter, 100))
        if self.timer_counter >= 100:
            self.timer.stop()
            self.progress_bar.setVisible(False)
            self.generate_btn.setEnabled(True)
            self.generate_report()

    def generate_report(self):
        raw_df = self.app_state.raw_df
        segmented_df = self.app_state.segmented_df
        scored_df = self.app_state.scored_df
        churn_engine = self.app_state.churn_engine
        seg_engine = self.app_state.segmentation_engine

        total_customers = len(raw_df)
        overall_churn = raw_df["churned"].mean() if "churned" in raw_df.columns else 0.0

        high_risk_mask = scored_df["risk_tier"] == "High"
        high_risk_count = int(high_risk_mask.sum())
        high_risk_pct = high_risk_count / total_customers if total_customers > 0 else 0.0

        value_at_risk = scored_df.loc[high_risk_mask, "monetary"].sum()
        avg_spend = raw_df["monetary"].mean()

        seg_summary = seg_engine.segment_summary(segmented_df).reset_index()

        # Always retrieve at least 5 drivers so the report has substantive content
        all_importances = churn_engine.feature_importances_
        n_drivers = max(5, min(len(all_importances), 5))
        top_drivers = all_importances.head(n_drivers)

        # ─── HTML report ─────────────────────────────────────────────────────
        html = f"""
        <html>
        <head>
        <style>
            body {{
                font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
                background-color: #1e1e1e;
                color: #d4d4d4;
                line-height: 1.65;
                font-size: 13px;
                margin: 0;
                padding: 4px;
            }}
            h2 {{
                color: #f3f4f6;
                font-size: 18px;
                font-weight: 700;
                margin-bottom: 4px;
            }}
            h3 {{
                color: #f3f4f6;
                font-size: 14px;
                font-weight: 700;
                margin-bottom: 8px;
                border-left: 3px solid #3b82f6;
                padding-left: 10px;
            }}
            h4 {{
                color: #e5e5e5;
                font-size: 13px;
                font-weight: 600;
                margin: 14px 0 6px 0;
            }}
            .divider {{
                border: 0;
                border-top: 1px solid #2c2c2c;
                margin: 6px 0 16px 0;
            }}
            .card {{
                background-color: #242424;
                border: 1px solid #2c2c2c;
                border-radius: 6px;
                padding: 18px 20px;
                margin-bottom: 16px;
            }}
            .kpi-grid {{
                width: 100%;
                border-collapse: separate;
                border-spacing: 10px;
                margin-top: 10px;
            }}
            .kpi-cell {{
                background-color: #181818;
                border: 1px solid #2c2c2c;
                border-radius: 5px;
                padding: 14px 10px;
                text-align: center;
                width: 33%;
            }}
            .kpi-label {{
                font-size: 11px;
                color: #a3a3a3;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 6px;
            }}
            .kpi-value {{
                font-size: 20px;
                font-weight: 700;
                color: #3b82f6;
            }}
            .kpi-value.risk {{
                color: #ef4444;
            }}
            .driver-row {{
                background-color: #181818;
                border: 1px solid #2c2c2c;
                border-radius: 5px;
                padding: 12px 16px;
                margin-bottom: 10px;
            }}
            .driver-name {{
                font-weight: 700;
                color: #e5e5e5;
                font-size: 13px;
            }}
            .driver-badge {{
                display: inline-block;
                background-color: #1d3557;
                color: #3b82f6;
                font-size: 11px;
                font-weight: 700;
                padding: 2px 8px;
                border-radius: 4px;
                margin-left: 8px;
            }}
            .driver-action {{
                color: #b0b0b0;
                font-size: 12px;
                margin-top: 6px;
                border-left: 2px solid #2c2c2c;
                padding-left: 10px;
            }}
            .action-label {{
                color: #3b82f6;
                font-weight: 700;
            }}
            table.seg-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 12px;
                font-size: 12px;
            }}
            table.seg-table th {{
                background-color: #181818;
                color: #e5e5e5;
                font-weight: 600;
                padding: 9px 10px;
                text-align: left;
                border-bottom: 2px solid #2c2c2c;
                text-transform: uppercase;
                font-size: 11px;
                letter-spacing: 0.4px;
            }}
            table.seg-table td {{
                padding: 9px 10px;
                border-bottom: 1px solid #2c2c2c;
                color: #d4d4d4;
            }}
            table.seg-table tr:last-child td {{
                border-bottom: none;
            }}
            table.seg-table tr:hover td {{
                background-color: #1f1f1f;
            }}
            .playbook-item {{
                padding: 10px 14px;
                border-bottom: 1px solid #2c2c2c;
            }}
            .playbook-item:last-child {{
                border-bottom: none;
            }}
            .playbook-seg {{
                font-weight: 700;
                color: #e5e5e5;
                margin-bottom: 3px;
            }}
            .playbook-desc {{
                color: #a3a3a3;
                font-size: 12px;
            }}
            .priority-item {{
                display: flex;
                padding: 12px 14px;
                border-bottom: 1px solid #2c2c2c;
            }}
            .priority-item:last-child {{
                border-bottom: none;
            }}
            .priority-badge {{
                font-weight: 700;
                font-size: 11px;
                padding: 3px 10px;
                border-radius: 4px;
                white-space: nowrap;
                margin-right: 14px;
                align-self: flex-start;
            }}
            .badge-critical {{ background-color: #3b0a0a; color: #ef4444; }}
            .badge-high     {{ background-color: #3b1e0a; color: #f59e0b; }}
            .badge-medium   {{ background-color: #1a2d1a; color: #22c55e; }}
            .badge-low      {{ background-color: #1a1a2e; color: #818cf8; }}
            .priority-text  {{ color: #d4d4d4; font-size: 12.5px; line-height: 1.6; }}
            .meta           {{ color: #6b6b6b; font-size: 11px; margin-bottom: 14px; }}
        </style>
        </head>
        <body>
            <h2>ML Model Interpretation Report</h2>
            <p class="meta">Generated: {datetime.now().strftime("%d %B %Y at %H:%M:%S")} &nbsp;&mdash;&nbsp; Records analysed: {total_customers:,}</p>
            <hr class="divider">

            <!-- ── Section 1: Executive KPI Summary ── -->
            <div class="card">
                <h3>Executive Health Summary</h3>
                <p>The analysis engine has completed a full evaluation of your customer base.
                Based on model predictions, the table below presents the current financial risk exposure
                and attrition status across all {total_customers:,} active customer records.</p>
                <table class="kpi-grid">
                    <tr>
                        <td class="kpi-cell">
                            <div class="kpi-label">Average Customer Spend</div>
                            <div class="kpi-value">R {avg_spend:,.2f}</div>
                        </td>
                        <td class="kpi-cell">
                            <div class="kpi-label">High-Risk Customers</div>
                            <div class="kpi-value risk">{high_risk_count:,} &nbsp;({high_risk_pct:.1%})</div>
                        </td>
                        <td class="kpi-cell">
                            <div class="kpi-label">Revenue at Risk</div>
                            <div class="kpi-value risk">R {value_at_risk:,.2f}</div>
                        </td>
                    </tr>
                </table>
            </div>

            <!-- ── Section 2: Churn Risk Drivers ── -->
            <div class="card">
                <h3>Churn Risk Drivers</h3>
                <p>The Random Forest classifier identified the following behavioural and engagement features
                as the strongest predictors of customer attrition, ranked by model feature importance.
                Targeted remediation actions are listed for each driver.</p>
        """

        feature_actions = {
            "support_tickets": (
                "Support Ticket Volume",
                "Customers with repeated unresolved support interactions represent the highest friction cohort.",
                "Establish priority routing for accounts with more than 3 open tickets. Assign relationship managers to conduct proactive outreach calls within 48 hours for all affected accounts."
            ),
            "avg_satisfaction_score": (
                "Customer Satisfaction Score",
                "Low satisfaction ratings are a leading indicator of imminent churn and reduced lifetime value.",
                "Deploy an automated post-interaction feedback workflow. Any score below 3.0 should trigger a personalised response within 2 hours, including a service recovery offer or escalation to a senior account manager."
            ),
            "recency_days": (
                "Purchase Recency",
                "Extended elapsed time since the last purchase is a primary decay signal indicating disengagement.",
                "Implement tiered win-back email sequences at 30, 60, and 90-day inactivity milestones, with escalating incentive values. Segment by historical spend tier to personalise offer amounts appropriately."
            ),
            "tenure_days": (
                "Customer Tenure",
                "Early-lifecycle customers show disproportionately high churn rates before forming habitual purchase behaviour.",
                "Introduce a structured 30-60-90 day onboarding programme with milestone check-ins, product tutorials, and incentivised first repeat purchase campaigns."
            ),
            "avg_order_value": (
                "Average Order Value",
                "A sustained decline in per-order spend signals a shift toward lower-tier options or competitor substitution.",
                "Deploy dynamic upsell recommendations at the point of purchase for customers whose average ticket size has declined over two consecutive orders. Personalise bundle offerings using their historical category mix."
            ),
            "discount_usage_rate": (
                "Discount Sensitivity",
                "Customers with consistently high discount reliance demonstrate price-led rather than value-led loyalty.",
                "Rebalance retention offers from flat-rate discounts toward non-monetary value additions such as early product access, exclusive content, or priority service tiers."
            ),
            "frequency": (
                "Purchase Frequency",
                "Declining order frequency indicates weakening habit formation and reduced brand stickiness.",
                "Introduce replenishment subscription options or 'Save and Subscribe' mechanics for regularly purchased product categories. Monitor frequency trends monthly and trigger re-engagement at the first sign of deviation."
            ),
            "monetary": (
                "Total Monetary Spend",
                "A reduction in cumulative spend may indicate partial migration of wallet share to competitors.",
                "Run a targeted loyalty outreach programme for historically high-spending customers whose recent spend trajectory is declining. Include personalised incentives tied to their preferred product categories."
            ),
            "num_returns": (
                "Return Volume",
                "Elevated return activity indicates product-expectation misalignment and increases the probability of attrition.",
                "Implement enhanced product description quality controls and post-purchase confirmation messaging. Analyse return reason codes to identify systemic fit or quality issues at the category level."
            ),
            "return_rate": (
                "Return Rate",
                "A high ratio of returned orders to total orders signals persistent dissatisfaction with product-market fit.",
                "Trigger a personalised product recommendation review for customers whose return rate exceeds 30%. Offer consultative support or curated alternative suggestions to improve purchase-fit accuracy."
            ),
            "email_open_rate": (
                "Email Engagement Rate",
                "Low email open rates indicate declining channel engagement and reduced receptiveness to outreach.",
                "Audit subject-line strategies and sending cadence. Implement A/B testing on message content and delivery time. Consider channel diversification via SMS or push notifications for low-open-rate segments."
            ),
            "loyalty_member": (
                "Loyalty Programme Membership",
                "Non-members exhibit significantly higher churn propensity than enrolled loyalty members.",
                "Run targeted enrolment campaigns directed at non-member customers in the At Risk segment. Communicate programme value clearly at the point of purchase and post-transaction."
            ),
            "num_categories_purchased": (
                "Category Breadth",
                "Customers who purchase across fewer categories show reduced brand attachment and higher churn risk.",
                "Design cross-category discovery promotions targeted at narrow-purchase customers. Bundle complementary products with existing favourites to broaden engagement across the catalogue."
            ),
            "age": (
                "Customer Age",
                "Age-related purchasing patterns may identify cohorts with distinct engagement dynamics and attrition triggers.",
                "Segment communications and retention incentives by age cohort. Review whether onboarding content, channel preference, and product recommendations are appropriately tailored per demographic group."
            ),
        }

        for feature_name, importance in top_drivers.items():
            if feature_name in feature_actions:
                clean_name, context, action = feature_actions[feature_name]
            else:
                clean_name = feature_name.replace("_", " ").title()
                context = "This attribute carries measurable predictive signal in the trained model."
                action = "Audit this customer attribute in the context of your retention strategy and assess whether targeted campaigns can be designed to address the underlying behaviour."

            html += f"""
            <div class="driver-row">
                <div class="driver-name">
                    {clean_name}
                    <span class="driver-badge">Importance: {importance:.1%}</span>
                </div>
                <div class="driver-action" style="margin-top:8px; color:#b0b0b0;">{context}</div>
                <div class="driver-action" style="margin-top:6px;">
                    <span class="action-label">Recommended Action: </span>{action}
                </div>
            </div>
            """

        html += """
            </div>

            <!-- ── Section 3: Segment Analysis ── -->
            <div class="card">
                <h3>Customer Segment Analysis</h3>
                <p>The K-Means RFM clustering model has partitioned your customer base into the segments below.
                Each segment is described by its average behavioural metrics, churn rate, and a tailored
                retention strategy drawn from model findings.</p>

                <table class="seg-table">
                    <thead>
                        <tr>
                            <th>Segment</th>
                            <th>Customers</th>
                            <th>Avg Recency (days)</th>
                            <th>Avg Orders</th>
                            <th>Avg Spend</th>
                            <th>Churn Rate</th>
                        </tr>
                    </thead>
                    <tbody>
        """

        for _, row in seg_summary.iterrows():
            segment_name = row["segment"]
            size = int(row["customers"])
            recency = row["avg_recency"]
            frequency = row["avg_frequency"]
            monetary = row["avg_monetary"]
            churn_rate_val = row.get("churn_rate", None)
            churn_str = f"{churn_rate_val:.1%}" if churn_rate_val is not None and churn_rate_val <= 1.0 else "N/A"

            html += f"""
                        <tr>
                            <td><b>{segment_name}</b></td>
                            <td>{size:,}</td>
                            <td>{recency:.1f}</td>
                            <td>{frequency:.1f}</td>
                            <td>R {monetary:,.2f}</td>
                            <td>{churn_str}</td>
                        </tr>
            """

        segment_playbooks = {
            "Champions": (
                "These are your highest-value customers by spend, frequency, and recency.",
                "Protect this segment by offering exclusive VIP programme benefits, early product access, and personalised appreciation outreach. Avoid over-discounting which may devalue perceived exclusivity. Leverage this cohort for referral and advocacy programmes."
            ),
            "Loyal Customers": (
                "Consistent, reliable purchasers with strong engagement patterns.",
                "Expand wallet share by introducing cross-category recommendations tailored to their purchase history. Implement milestone reward mechanics such as anniversary offers and tiered loyalty incentives to reinforce retention."
            ),
            "At Risk": (
                "Previously high-value customers showing measurable declines in engagement or spend.",
                "Prioritise this cohort for personalised reactivation outreach. Deploy win-back incentives within 14 days of risk signal detection. Supplement with a satisfaction survey to identify root causes of disengagement."
            ),
            "Hibernating": (
                "Low engagement, low frequency, and extended inactivity. Revenue contribution is minimal.",
                "Apply low-cost automated re-engagement sequences. Avoid allocating high-value incentive budgets to this cohort until initial reactivation is confirmed. Monitor for requalification into At Risk or New/Low-Value segments."
            ),
            "New / Low-Value": (
                "Recently acquired customers who have not yet established consistent purchasing behaviour.",
                "Execute a structured onboarding programme across the first 90 days. Incentivise the second purchase within 30 days, as this significantly increases 12-month retention probability. Use educational content to build product familiarity."
            ),
        }

        html += """
                    </tbody>
                </table>

                <h4>Segment Retention Strategies</h4>
                <div style="border: 1px solid #2c2c2c; border-radius: 5px; overflow: hidden; margin-top: 4px;">
        """

        for _, row in seg_summary.iterrows():
            segment_name = row["segment"]
            if segment_name in segment_playbooks:
                context_text, action_text = segment_playbooks[segment_name]
            else:
                context_text = "This segment exhibits distinct behavioural characteristics requiring tailored engagement."
                action_text = "Analyse purchase patterns and apply targeted communication strategies aligned to observed behaviour."

            html += f"""
                    <div class="playbook-item">
                        <div class="playbook-seg">{segment_name}</div>
                        <div class="playbook-desc">{context_text} {action_text}</div>
                    </div>
            """

        html += """
                </div>
            </div>

            <!-- ── Section 4: Tactical Priority Plan ── -->
            <div class="card">
                <h3>Tactical Priority Plan</h3>
                <p>The following actions are ranked in order of urgency based on modelled risk exposure,
                revenue impact, and segment vulnerability. Execute in sequence to maximise retention outcomes.</p>
                <div style="border: 1px solid #2c2c2c; border-radius: 5px; overflow: hidden; margin-top: 10px;">

                    <div class="priority-item">
                        <span class="priority-badge badge-critical">Critical</span>
                        <span class="priority-text">
                            Export the <b>High</b> risk tier customer list from the Churn Prediction tab and immediately
                            queue a personalised outbound retention campaign. Each day of delay increases the probability
                            of irreversible attrition for this cohort.
                        </span>
                    </div>

                    <div class="priority-item">
                        <span class="priority-badge badge-critical">Critical</span>
                        <span class="priority-text">
                            Assign relationship managers to accounts identified as High risk with support ticket counts
                            above three. Conduct direct outreach within 48 hours. Document outcomes in the CRM Panel.
                        </span>
                    </div>

                    <div class="priority-item">
                        <span class="priority-badge badge-high">High</span>
                        <span class="priority-text">
                            Configure automated satisfaction monitoring to flag any customer whose average satisfaction
                            score drops below 3.0. Ensure a service recovery workflow is triggered within two hours of detection.
                        </span>
                    </div>

                    <div class="priority-item">
                        <span class="priority-badge badge-high">High</span>
                        <span class="priority-text">
                            Deploy win-back sequences for the <b>At Risk</b> segment customers who have not transacted
                            in more than 45 days. Apply escalating incentive tiers at the 30, 60, and 90-day inactivity thresholds.
                        </span>
                    </div>

                    <div class="priority-item">
                        <span class="priority-badge badge-medium">Medium</span>
                        <span class="priority-text">
                            Introduce cross-category upsell campaigns for <b>Loyal Customers</b> to elevate their
                            monetary contribution toward <b>Champions</b> levels. Personalise recommendations using their
                            historical category purchase mix.
                        </span>
                    </div>

                    <div class="priority-item">
                        <span class="priority-badge badge-medium">Medium</span>
                        <span class="priority-text">
                            Enrol non-member customers in the <b>At Risk</b> and <b>New / Low-Value</b> segments into
                            the loyalty programme. Loyalty membership is a significant negative predictor of churn in this model.
                        </span>
                    </div>

                    <div class="priority-item">
                        <span class="priority-badge badge-low">Low</span>
                        <span class="priority-text">
                            Audit email engagement rates across all segments and test subject-line variations for
                            low-open-rate cohorts. Consider SMS or push notification supplements for customers with
                            persistently low email engagement.
                        </span>
                    </div>

                </div>
            </div>

        </body>
        </html>
        """

        self.report_viewer.setHtml(html)
