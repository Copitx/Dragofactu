"""
Dragofactu UI Design System Stylesheet
Apple-inspired, clean, minimal

Design tokens from CLAUDE.md:
- Backgrounds: #FAFAFA (app), white cards
- Text: #1D1D1F primary, #6E6E73 secondary
- Accent: #007AFF
- Font: system-ui / SF Pro / Segoe UI fallback
- Border radius: 8px standard, 12px cards
- Spacing: 4px grid, 16px card gaps
"""

# Color palette
COLORS = {
    'bg_app': '#FAFAFA',
    'bg_card': '#FFFFFF',
    'bg_hover': '#F5F5F7',
    'bg_pressed': '#E8E8ED',

    'text_primary': '#1D1D1F',
    'text_secondary': '#6E6E73',
    'text_tertiary': '#86868B',
    'text_inverse': '#FFFFFF',

    'accent': '#007AFF',
    'accent_hover': '#0056CC',
    'accent_pressed': '#004499',

    'danger': '#FF3B30',
    'danger_hover': '#CC2F26',

    'success': '#34C759',
    'warning': '#FF9500',

    'border': '#D2D2D7',
    'border_light': '#E5E5EA',
    'divider': '#C6C6C8',
}

# Typography
FONTS = {
    'family': 'system-ui, -apple-system, "SF Pro Display", "Segoe UI", sans-serif',
    'size_xs': '11px',
    'size_sm': '12px',
    'size_base': '13px',
    'size_lg': '15px',
    'size_xl': '17px',
    'size_2xl': '22px',
    'size_3xl': '28px',
}

# Spacing (4px grid)
SPACING = {
    'xs': '4px',
    'sm': '8px',
    'md': '12px',
    'lg': '16px',
    'xl': '20px',
    '2xl': '24px',
    '3xl': '32px',
}

# Border radius
RADIUS = {
    'sm': '4px',
    'md': '8px',
    'lg': '12px',
    'xl': '16px',
    'full': '9999px',
}


def get_base_stylesheet() -> str:
    """
    Returns the global Qt stylesheet implementing the design system.
    Apply this to QApplication for app-wide styling.
    """
    return f"""
    /* ========================================
       GLOBAL APPLICATION STYLES
       ======================================== */

    QMainWindow, QDialog {{
        background-color: {COLORS['bg_app']};
        font-family: {FONTS['family']};
        font-size: {FONTS['size_base']};
        color: {COLORS['text_primary']};
    }}

    QWidget {{
        font-family: {FONTS['family']};
        font-size: {FONTS['size_base']};
        color: {COLORS['text_primary']};
    }}

    /* ========================================
       MENU BAR
       ======================================== */

    QMenuBar {{
        background-color: {COLORS['bg_card']};
        border-bottom: 1px solid {COLORS['border_light']};
        padding: {SPACING['xs']} {SPACING['sm']};
        font-size: {FONTS['size_base']};
    }}

    QMenuBar::item {{
        background-color: transparent;
        padding: {SPACING['xs']} {SPACING['sm']};
        border-radius: {RADIUS['sm']};
        color: {COLORS['text_primary']};
    }}

    QMenuBar::item:selected {{
        background-color: {COLORS['bg_hover']};
    }}

    QMenuBar::item:pressed {{
        background-color: {COLORS['bg_pressed']};
    }}

    QMenu {{
        background-color: {COLORS['bg_card']};
        border: 1px solid {COLORS['border']};
        border-radius: {RADIUS['md']};
        padding: {SPACING['xs']} 0;
    }}

    QMenu::item {{
        padding: {SPACING['sm']} {SPACING['lg']};
        color: {COLORS['text_primary']};
    }}

    QMenu::item:selected {{
        background-color: {COLORS['accent']};
        color: {COLORS['text_inverse']};
    }}

    QMenu::separator {{
        height: 1px;
        background-color: {COLORS['border_light']};
        margin: {SPACING['xs']} {SPACING['sm']};
    }}

    /* ========================================
       TOOLBAR
       ======================================== */

    QToolBar {{
        background-color: {COLORS['bg_card']};
        border-bottom: 1px solid {COLORS['border_light']};
        spacing: {SPACING['sm']};
        padding: {SPACING['sm']} {SPACING['md']};
    }}

    QToolBar::separator {{
        width: 1px;
        background-color: {COLORS['border_light']};
        margin: {SPACING['xs']} {SPACING['sm']};
    }}

    QToolButton {{
        background-color: transparent;
        border: none;
        border-radius: {RADIUS['sm']};
        padding: {SPACING['sm']} {SPACING['md']};
        color: {COLORS['text_primary']};
    }}

    QToolButton:hover {{
        background-color: {COLORS['bg_hover']};
    }}

    QToolButton:pressed {{
        background-color: {COLORS['bg_pressed']};
    }}

    /* ========================================
       TAB WIDGET (NAVIGATION)
       ======================================== */

    QTabWidget::pane {{
        background-color: {COLORS['bg_card']};
        border: 1px solid {COLORS['border_light']};
        border-radius: {RADIUS['lg']};
        margin-top: -{SPACING['xs']};
    }}

    QTabBar {{
        background-color: transparent;
    }}

    QTabBar::tab {{
        background-color: transparent;
        border: none;
        padding: {SPACING['sm']} {SPACING['lg']};
        margin-right: {SPACING['xs']};
        color: {COLORS['text_secondary']};
        font-weight: 500;
    }}

    QTabBar::tab:selected {{
        color: {COLORS['accent']};
        border-bottom: 2px solid {COLORS['accent']};
    }}

    QTabBar::tab:hover:!selected {{
        color: {COLORS['text_primary']};
    }}

    /* ========================================
       STATUS BAR
       ======================================== */

    QStatusBar {{
        background-color: {COLORS['bg_card']};
        border-top: 1px solid {COLORS['border_light']};
        padding: {SPACING['xs']} {SPACING['md']};
        font-size: {FONTS['size_sm']};
        color: {COLORS['text_secondary']};
    }}

    QStatusBar::item {{
        border: none;
    }}

    /* ========================================
       BUTTONS
       ======================================== */

    /* Primary Button */
    QPushButton {{
        background-color: {COLORS['accent']};
        color: {COLORS['text_inverse']};
        border: none;
        border-radius: {RADIUS['md']};
        padding: {SPACING['sm']} {SPACING['lg']};
        font-weight: 500;
        font-size: {FONTS['size_base']};
        min-height: 32px;
    }}

    QPushButton:hover {{
        background-color: {COLORS['accent_hover']};
    }}

    QPushButton:pressed {{
        background-color: {COLORS['accent_pressed']};
    }}

    QPushButton:disabled {{
        background-color: {COLORS['bg_pressed']};
        color: {COLORS['text_tertiary']};
    }}

    /* Secondary Button (object name: secondary) */
    QPushButton[secondary="true"] {{
        background-color: transparent;
        color: {COLORS['accent']};
        border: 1px solid {COLORS['accent']};
    }}

    QPushButton[secondary="true"]:hover {{
        background-color: {COLORS['bg_hover']};
    }}

    /* Danger Button (object name: danger) */
    QPushButton[danger="true"] {{
        background-color: {COLORS['danger']};
        color: {COLORS['text_inverse']};
        border: none;
    }}

    QPushButton[danger="true"]:hover {{
        background-color: {COLORS['danger_hover']};
    }}

    /* ========================================
       INPUT FIELDS
       ======================================== */

    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit {{
        background-color: {COLORS['bg_card']};
        border: 1px solid {COLORS['border']};
        border-radius: {RADIUS['md']};
        padding: {SPACING['sm']} {SPACING['md']};
        color: {COLORS['text_primary']};
        font-size: {FONTS['size_base']};
        min-height: 20px;
    }}

    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
    QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QTimeEdit:focus {{
        border-color: {COLORS['accent']};
        outline: none;
    }}

    QLineEdit:disabled, QTextEdit:disabled {{
        background-color: {COLORS['bg_app']};
        color: {COLORS['text_tertiary']};
    }}

    QLineEdit::placeholder {{
        color: {COLORS['text_tertiary']};
    }}

    /* ========================================
       COMBO BOX
       ======================================== */

    QComboBox {{
        background-color: {COLORS['bg_card']};
        border: 1px solid {COLORS['border']};
        border-radius: {RADIUS['md']};
        padding: {SPACING['sm']} {SPACING['md']};
        color: {COLORS['text_primary']};
        min-height: 20px;
    }}

    QComboBox:focus {{
        border-color: {COLORS['accent']};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {COLORS['bg_card']};
        border: 1px solid {COLORS['border']};
        border-radius: {RADIUS['md']};
        selection-background-color: {COLORS['accent']};
        selection-color: {COLORS['text_inverse']};
    }}

    /* ========================================
       TABLES
       ======================================== */

    QTableWidget, QTableView {{
        background-color: {COLORS['bg_card']};
        border: 1px solid {COLORS['border_light']};
        border-radius: {RADIUS['md']};
        gridline-color: {COLORS['border_light']};
        selection-background-color: {COLORS['accent']};
        selection-color: {COLORS['text_inverse']};
    }}

    QTableWidget::item, QTableView::item {{
        padding: {SPACING['sm']} {SPACING['md']};
        border-bottom: 1px solid {COLORS['border_light']};
    }}

    QTableWidget::item:hover, QTableView::item:hover {{
        background-color: {COLORS['bg_hover']};
    }}

    QHeaderView::section {{
        background-color: {COLORS['bg_app']};
        color: {COLORS['text_secondary']};
        font-weight: 600;
        font-size: {FONTS['size_xs']};
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: {SPACING['sm']} {SPACING['md']};
        border: none;
        border-bottom: 1px solid {COLORS['border']};
    }}

    /* ========================================
       CARDS (QFrame with class)
       ======================================== */

    QFrame[frameShape="1"] {{
        background-color: {COLORS['bg_card']};
        border: 1px solid {COLORS['border_light']};
        border-radius: {RADIUS['lg']};
        padding: {SPACING['lg']};
    }}

    /* ========================================
       GROUP BOX
       ======================================== */

    QGroupBox {{
        background-color: {COLORS['bg_card']};
        border: 1px solid {COLORS['border_light']};
        border-radius: {RADIUS['lg']};
        margin-top: {SPACING['lg']};
        padding: {SPACING['lg']};
        padding-top: {SPACING['2xl']};
        font-weight: 600;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 {SPACING['sm']};
        color: {COLORS['text_primary']};
        font-size: {FONTS['size_sm']};
    }}

    /* ========================================
       LABELS
       ======================================== */

    QLabel {{
        color: {COLORS['text_primary']};
    }}

    QLabel[secondary="true"] {{
        color: {COLORS['text_secondary']};
        font-size: {FONTS['size_sm']};
    }}

    /* ========================================
       SCROLL BARS
       ======================================== */

    QScrollBar:vertical {{
        background-color: transparent;
        width: 8px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background-color: {COLORS['border']};
        border-radius: 4px;
        min-height: 20px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {COLORS['text_tertiary']};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    QScrollBar:horizontal {{
        background-color: transparent;
        height: 8px;
        margin: 0;
    }}

    QScrollBar::handle:horizontal {{
        background-color: {COLORS['border']};
        border-radius: 4px;
        min-width: 20px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background-color: {COLORS['text_tertiary']};
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}

    /* ========================================
       CHECKBOXES & RADIO BUTTONS
       ======================================== */

    QCheckBox {{
        spacing: {SPACING['sm']};
        color: {COLORS['text_primary']};
    }}

    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 1px solid {COLORS['border']};
        border-radius: {RADIUS['sm']};
        background-color: {COLORS['bg_card']};
    }}

    QCheckBox::indicator:checked {{
        background-color: {COLORS['accent']};
        border-color: {COLORS['accent']};
    }}

    QRadioButton {{
        spacing: {SPACING['sm']};
        color: {COLORS['text_primary']};
    }}

    QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border: 1px solid {COLORS['border']};
        border-radius: 9px;
        background-color: {COLORS['bg_card']};
    }}

    QRadioButton::indicator:checked {{
        background-color: {COLORS['accent']};
        border: 4px solid {COLORS['bg_card']};
        border-color: {COLORS['accent']};
    }}

    /* ========================================
       MESSAGE BOX
       ======================================== */

    QMessageBox {{
        background-color: {COLORS['bg_card']};
    }}

    QMessageBox QLabel {{
        color: {COLORS['text_primary']};
        font-size: {FONTS['size_base']};
    }}

    /* ========================================
       TOOLTIPS
       ======================================== */

    QToolTip {{
        background-color: {COLORS['text_primary']};
        color: {COLORS['text_inverse']};
        border: none;
        border-radius: {RADIUS['sm']};
        padding: {SPACING['xs']} {SPACING['sm']};
        font-size: {FONTS['size_sm']};
    }}
    """


def get_card_style(accent_color: str = None) -> str:
    """
    Returns stylesheet for a card widget.
    Use this for summary cards, info panels, etc.

    Args:
        accent_color: Optional accent color for the card border
    """
    border_color = accent_color if accent_color else COLORS['border_light']
    return f"""
        QFrame {{
            background-color: {COLORS['bg_card']};
            border: 1px solid {border_color};
            border-radius: {RADIUS['lg']};
            padding: {SPACING['lg']};
        }}
    """


def get_primary_button_style() -> str:
    """Primary action button style"""
    return f"""
        QPushButton {{
            background-color: {COLORS['accent']};
            color: {COLORS['text_inverse']};
            border: none;
            border-radius: {RADIUS['md']};
            padding: {SPACING['sm']} {SPACING['lg']};
            font-weight: 500;
            min-height: 36px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['accent_hover']};
        }}
        QPushButton:pressed {{
            background-color: {COLORS['accent_pressed']};
        }}
    """


def get_secondary_button_style() -> str:
    """Secondary/outline button style"""
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {COLORS['accent']};
            border: 1px solid {COLORS['accent']};
            border-radius: {RADIUS['md']};
            padding: {SPACING['sm']} {SPACING['lg']};
            font-weight: 500;
            min-height: 36px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['bg_hover']};
        }}
        QPushButton:pressed {{
            background-color: {COLORS['bg_pressed']};
        }}
    """


def get_danger_button_style() -> str:
    """Danger/destructive action button style"""
    return f"""
        QPushButton {{
            background-color: {COLORS['danger']};
            color: {COLORS['text_inverse']};
            border: none;
            border-radius: {RADIUS['md']};
            padding: {SPACING['sm']} {SPACING['lg']};
            font-weight: 500;
            min-height: 36px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['danger_hover']};
        }}
    """


# Convenience function to apply stylesheet to app
def apply_stylesheet(app) -> None:
    """
    Apply the design system stylesheet to a QApplication.

    Usage:
        from dragofactu.ui.styles import apply_stylesheet

        app = QApplication(sys.argv)
        apply_stylesheet(app)
    """
    app.setStyleSheet(get_base_stylesheet())
