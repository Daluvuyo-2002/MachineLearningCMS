"""Shared visual theme: navy/blue, matching a clean professional dark dashboard look."""

NAVY_DARK = "#181818"     # deep grey
NAVY = "#f3f4f6"          # off-white
NAVY_LIGHT = "#2d2d2d"     # medium grey hover
BLUE_ACCENT = "#3b82f6"    # vibrant blue accent
BLUE_SOFT = "#2b3c5c"      # selection bg
GREEN = "#22c55e"
AMBER = "#f59e0b"
RED = "#ef4444"
GREY_BG = "#121212"       # dark charcoal bg
WHITE = "#1e1e1e"         # card/surface bg
TEXT_DARK = "#f3f4f6"     # primary text
TEXT_MUTED = "#a3a3a3"    # muted text
BORDER_COLOR = "#2c2c2c"  # border grey

APP_STYLESHEET = f"""
QMainWindow {{
    background-color: {GREY_BG};
}}

QWidget {{
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
    color: {TEXT_DARK};
}}

QTabWidget::pane {{
    border: none;
    background-color: {GREY_BG};
}}

QTabBar::tab {{
    background-color: {NAVY_DARK};
    color: {TEXT_MUTED};
    padding: 11px 28px;
    margin-right: 2px;
    font-weight: 600;
    font-size: 12px;
    letter-spacing: 0.4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}}

QTabBar::tab:selected {{
    background-color: {BLUE_ACCENT};
    color: white;
}}

QTabBar::tab:hover:!selected {{
    background-color: {NAVY_LIGHT};
    color: white;
}}

QPushButton {{
    background-color: {BLUE_ACCENT};
    color: white;
    border: none;
    padding: 9px 18px;
    border-radius: 6px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: #2563eb;
}}

QPushButton:disabled {{
    background-color: #475569;
    color: #94a3b8;
}}

QPushButton#secondary {{
    background-color: {WHITE};
    color: {TEXT_DARK};
    border: 1px solid {BORDER_COLOR};
}}

QPushButton#secondary:hover {{
    background-color: {NAVY_LIGHT};
}}

QTableView {{
    background-color: {WHITE};
    alternate-background-color: #182235;
    gridline-color: {BORDER_COLOR};
    selection-background-color: {BLUE_SOFT};
    selection-color: {TEXT_DARK};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
}}

QHeaderView::section {{
    background-color: {NAVY_DARK};
    color: {TEXT_DARK};
    padding: 6px;
    border: none;
    border-bottom: 1px solid {BORDER_COLOR};
    font-weight: 600;
}}

QLabel#kpiValue {{
    font-size: 26px;
    font-weight: 700;
    color: white;
}}

QLabel#kpiLabel {{
    font-size: 12px;
    color: {TEXT_MUTED};
    font-weight: 600;
    letter-spacing: 0.5px;
}}

QFrame#kpiCard {{
    background-color: {WHITE};
    border-radius: 10px;
    border: 1px solid {BORDER_COLOR};
}}

QLabel#sectionTitle {{
    font-size: 17px;
    font-weight: 700;
    color: {NAVY};
    padding: 4px 0px;
}}

QLabel#pageSubtitle {{
    color: {TEXT_MUTED};
    font-size: 12px;
}}

QComboBox, QLineEdit, QSpinBox {{
    background-color: {WHITE};
    color: {TEXT_DARK};
    border: 1px solid {BORDER_COLOR};
    border-radius: 5px;
    padding: 6px 10px;
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 4px;
}}

QStatusBar {{
    background-color: {NAVY_DARK};
    color: {TEXT_MUTED};
}}
"""
