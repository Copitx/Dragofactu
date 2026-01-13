"""
Dragofactu UI Design System Stylesheet
Apple-inspired, clean, minimal with Light and Dark theme support.

Design tokens from CLAUDE.md:
- Backgrounds: #FAFAFA (app), white cards
- Text: #1D1D1F primary, #6E6E73 secondary
- Accent: #007AFF
- Font: system-ui / SF Pro / Segoe UI fallback
- Border radius: 8px standard, 12px cards
- Spacing: 4px grid, 16px card gaps
"""
import json
import os
from typing import Dict, Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication


# Light theme color palette
LIGHT_COLORS = {
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

# Dark theme color palette
DARK_COLORS = {
    'bg_app': '#1C1C1E',
    'bg_card': '#2C2C2E',
    'bg_hover': '#3A3A3C',
    'bg_pressed': '#48484A',

    'text_primary': '#FFFFFF',
    'text_secondary': '#EBEBF5',
    'text_tertiary': '#8E8E93',
    'text_inverse': '#1D1D1F',

    'accent': '#0A84FF',
    'accent_hover': '#409CFF',
    'accent_pressed': '#0056CC',

    'danger': '#FF453A',
    'danger_hover': '#FF6961',

    'success': '#30D158',
    'warning': '#FF9F0A',

    'border': '#48484A',
    'border_light': '#3A3A3C',
    'divider': '#545456',
}

# Default to light colors (will be updated by ThemeManager)
COLORS = LIGHT_COLORS.copy()

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


class ThemeManager(QObject):
    """
    Theme manager with dynamic theme switching support.
    Emits theme_changed signal when theme is changed so UI can update.
    """
    # Signal emitted when theme changes
    theme_changed = Signal(str)

    # Theme constants
    LIGHT = 'light'
    DARK = 'dark'
    AUTO = 'auto'

    def __init__(self):
        super().__init__()
        self._current_theme = self.LIGHT
        self._app: Optional[QApplication] = None
        self._settings_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'config', 'user_settings.json'
        )
        self._load_saved_theme()

    @property
    def current_theme(self) -> str:
        return self._current_theme

    def _load_saved_theme(self):
        """Load saved theme preference from settings file"""
        try:
            if os.path.exists(self._settings_file):
                with open(self._settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    saved_theme = settings.get('theme', self.LIGHT)
                    if saved_theme in [self.LIGHT, self.DARK, self.AUTO]:
                        self._current_theme = saved_theme
        except Exception:
            pass  # Use default theme if loading fails

    def _save_theme(self):
        """Save current theme to settings file"""
        try:
            settings = {}
            if os.path.exists(self._settings_file):
                with open(self._settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

            settings['theme'] = self._current_theme

            # Ensure directory exists
            os.makedirs(os.path.dirname(self._settings_file), exist_ok=True)

            with open(self._settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
        except Exception:
            pass  # Silently fail if saving fails

    def set_app(self, app: QApplication):
        """Set the QApplication instance for stylesheet updates"""
        self._app = app

    def get_effective_theme(self) -> str:
        """Get the effective theme (resolves AUTO to actual theme)"""
        if self._current_theme == self.AUTO:
            # Try to detect system theme
            try:
                from PySide6.QtGui import QPalette
                if self._app:
                    palette = self._app.palette()
                    bg_color = palette.color(QPalette.ColorRole.Window)
                    # If background is dark, use dark theme
                    if bg_color.lightness() < 128:
                        return self.DARK
            except Exception:
                pass
            return self.LIGHT
        return self._current_theme

    def set_theme(self, theme: str) -> bool:
        """
        Set current theme and emit signal for UI updates.
        Returns True if theme was changed successfully.
        """
        if theme not in [self.LIGHT, self.DARK, self.AUTO]:
            return False

        old_theme = self._current_theme
        self._current_theme = theme
        self._save_theme()

        # Update global COLORS
        global COLORS
        effective_theme = self.get_effective_theme()
        if effective_theme == self.DARK:
            COLORS.clear()
            COLORS.update(DARK_COLORS)
        else:
            COLORS.clear()
            COLORS.update(LIGHT_COLORS)

        # Apply stylesheet immediately
        if self._app:
            self._app.setStyleSheet(get_base_stylesheet())

        if old_theme != theme:
            self.theme_changed.emit(theme)

        return True

    def get_colors(self) -> Dict[str, str]:
        """Get current color palette based on theme"""
        if self.get_effective_theme() == self.DARK:
            return DARK_COLORS.copy()
        return LIGHT_COLORS.copy()

    def get_available_themes(self) -> Dict[str, str]:
        """Get available themes with display names"""
        return {
            self.LIGHT: 'Claro',
            self.DARK: 'Oscuro',
            self.AUTO: 'Auto'
        }

    def get_theme_code_from_name(self, name: str) -> Optional[str]:
        """Get theme code from display name"""
        name_to_code = {
            'Claro': self.LIGHT,
            'Oscuro': self.DARK,
            'Auto': self.AUTO
        }
        return name_to_code.get(name)

    def get_theme_name_from_code(self, code: str) -> str:
        """Get display name from theme code"""
        return self.get_available_themes().get(code, 'Claro')


# Global theme manager instance
theme_manager = ThemeManager()


def get_base_stylesheet() -> str:
    """
    Returns the global Qt stylesheet implementing the design system.
    Apply this to QApplication for app-wide styling.
    Uses current theme colors.
    """
    # Use current colors from theme manager
    colors = theme_manager.get_colors()

    return f"""
    /* ========================================
       GLOBAL APPLICATION STYLES
       ======================================== */

    QMainWindow, QDialog {{
        background-color: {colors['bg_app']};
        font-family: {FONTS['family']};
        font-size: {FONTS['size_base']};
        color: {colors['text_primary']};
    }}

    QWidget {{
        font-family: {FONTS['family']};
        font-size: {FONTS['size_base']};
        color: {colors['text_primary']};
    }}

    /* ========================================
       MENU BAR
       ======================================== */

    QMenuBar {{
        background-color: {colors['bg_card']};
        border-bottom: 1px solid {colors['border_light']};
        padding: {SPACING['xs']} {SPACING['sm']};
        font-size: {FONTS['size_base']};
    }}

    QMenuBar::item {{
        background-color: transparent;
        padding: {SPACING['xs']} {SPACING['sm']};
        border-radius: {RADIUS['sm']};
        color: {colors['text_primary']};
    }}

    QMenuBar::item:selected {{
        background-color: {colors['bg_hover']};
    }}

    QMenuBar::item:pressed {{
        background-color: {colors['bg_pressed']};
    }}

    QMenu {{
        background-color: {colors['bg_card']};
        border: 1px solid {colors['border']};
        border-radius: {RADIUS['md']};
        padding: {SPACING['xs']} 0;
    }}

    QMenu::item {{
        padding: {SPACING['sm']} {SPACING['lg']};
        color: {colors['text_primary']};
    }}

    QMenu::item:selected {{
        background-color: {colors['accent']};
        color: {colors['text_inverse']};
    }}

    QMenu::separator {{
        height: 1px;
        background-color: {colors['border_light']};
        margin: {SPACING['xs']} {SPACING['sm']};
    }}

    /* ========================================
       TOOLBAR
       ======================================== */

    QToolBar {{
        background-color: {colors['bg_card']};
        border-bottom: 1px solid {colors['border_light']};
        spacing: {SPACING['sm']};
        padding: {SPACING['sm']} {SPACING['md']};
    }}

    QToolBar::separator {{
        width: 1px;
        background-color: {colors['border_light']};
        margin: {SPACING['xs']} {SPACING['sm']};
    }}

    QToolButton {{
        background-color: transparent;
        border: none;
        border-radius: {RADIUS['sm']};
        padding: {SPACING['sm']} {SPACING['md']};
        color: {colors['text_primary']};
    }}

    QToolButton:hover {{
        background-color: {colors['bg_hover']};
    }}

    QToolButton:pressed {{
        background-color: {colors['bg_pressed']};
    }}

    /* ========================================
       TAB WIDGET (NAVIGATION)
       ======================================== */

    QTabWidget::pane {{
        background-color: {colors['bg_card']};
        border: 1px solid {colors['border_light']};
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
        color: {colors['text_secondary']};
        font-weight: 500;
    }}

    QTabBar::tab:selected {{
        color: {colors['accent']};
        border-bottom: 2px solid {colors['accent']};
    }}

    QTabBar::tab:hover:!selected {{
        color: {colors['text_primary']};
    }}

    /* ========================================
       STATUS BAR
       ======================================== */

    QStatusBar {{
        background-color: {colors['bg_card']};
        border-top: 1px solid {colors['border_light']};
        padding: {SPACING['xs']} {SPACING['md']};
        font-size: {FONTS['size_sm']};
        color: {colors['text_secondary']};
    }}

    QStatusBar::item {{
        border: none;
    }}

    /* ========================================
       BUTTONS
       ======================================== */

    /* Primary Button */
    QPushButton {{
        background-color: {colors['accent']};
        color: {colors['text_inverse']};
        border: none;
        border-radius: {RADIUS['md']};
        padding: {SPACING['sm']} {SPACING['lg']};
        font-weight: 500;
        font-size: {FONTS['size_base']};
        min-height: 32px;
    }}

    QPushButton:hover {{
        background-color: {colors['accent_hover']};
    }}

    QPushButton:pressed {{
        background-color: {colors['accent_pressed']};
    }}

    QPushButton:disabled {{
        background-color: {colors['bg_pressed']};
        color: {colors['text_tertiary']};
    }}

    /* Secondary Button (object name: secondary) */
    QPushButton[secondary="true"] {{
        background-color: transparent;
        color: {colors['accent']};
        border: 1px solid {colors['accent']};
    }}

    QPushButton[secondary="true"]:hover {{
        background-color: {colors['bg_hover']};
    }}

    /* Danger Button (object name: danger) */
    QPushButton[danger="true"] {{
        background-color: {colors['danger']};
        color: {colors['text_inverse']};
        border: none;
    }}

    QPushButton[danger="true"]:hover {{
        background-color: {colors['danger_hover']};
    }}

    /* ========================================
       INPUT FIELDS
       ======================================== */

    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit {{
        background-color: {colors['bg_card']};
        border: 1px solid {colors['border']};
        border-radius: {RADIUS['md']};
        padding: {SPACING['sm']} {SPACING['md']};
        color: {colors['text_primary']};
        font-size: {FONTS['size_base']};
        min-height: 20px;
    }}

    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
    QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QTimeEdit:focus {{
        border-color: {colors['accent']};
        outline: none;
    }}

    QLineEdit:disabled, QTextEdit:disabled {{
        background-color: {colors['bg_app']};
        color: {colors['text_tertiary']};
    }}

    QLineEdit::placeholder {{
        color: {colors['text_tertiary']};
    }}

    /* ========================================
       COMBO BOX
       ======================================== */

    QComboBox {{
        background-color: {colors['bg_card']};
        border: 1px solid {colors['border']};
        border-radius: {RADIUS['md']};
        padding: {SPACING['sm']} {SPACING['md']};
        color: {colors['text_primary']};
        min-height: 20px;
    }}

    QComboBox:focus {{
        border-color: {colors['accent']};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {colors['bg_card']};
        border: 1px solid {colors['border']};
        border-radius: {RADIUS['md']};
        selection-background-color: {colors['accent']};
        selection-color: {colors['text_inverse']};
    }}

    /* ========================================
       TABLES
       ======================================== */

    QTableWidget, QTableView {{
        background-color: {colors['bg_card']};
        border: 1px solid {colors['border_light']};
        border-radius: {RADIUS['md']};
        gridline-color: {colors['border_light']};
        selection-background-color: {colors['accent']};
        selection-color: {colors['text_inverse']};
    }}

    QTableWidget::item, QTableView::item {{
        padding: {SPACING['sm']} {SPACING['md']};
        border-bottom: 1px solid {colors['border_light']};
    }}

    QTableWidget::item:hover, QTableView::item:hover {{
        background-color: {colors['bg_hover']};
    }}

    QHeaderView::section {{
        background-color: {colors['bg_app']};
        color: {colors['text_secondary']};
        font-weight: 600;
        font-size: {FONTS['size_xs']};
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: {SPACING['sm']} {SPACING['md']};
        border: none;
        border-bottom: 1px solid {colors['border']};
    }}

    /* ========================================
       CARDS (QFrame with class)
       ======================================== */

    QFrame[frameShape="1"] {{
        background-color: {colors['bg_card']};
        border: 1px solid {colors['border_light']};
        border-radius: {RADIUS['lg']};
        padding: {SPACING['lg']};
    }}

    /* ========================================
       GROUP BOX
       ======================================== */

    QGroupBox {{
        background-color: {colors['bg_card']};
        border: 1px solid {colors['border_light']};
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
        color: {colors['text_primary']};
        font-size: {FONTS['size_sm']};
    }}

    /* ========================================
       LABELS
       ======================================== */

    QLabel {{
        color: {colors['text_primary']};
    }}

    QLabel[secondary="true"] {{
        color: {colors['text_secondary']};
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
        background-color: {colors['border']};
        border-radius: 4px;
        min-height: 20px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {colors['text_tertiary']};
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
        background-color: {colors['border']};
        border-radius: 4px;
        min-width: 20px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background-color: {colors['text_tertiary']};
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}

    /* ========================================
       CHECKBOXES & RADIO BUTTONS
       ======================================== */

    QCheckBox {{
        spacing: {SPACING['sm']};
        color: {colors['text_primary']};
    }}

    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 1px solid {colors['border']};
        border-radius: {RADIUS['sm']};
        background-color: {colors['bg_card']};
    }}

    QCheckBox::indicator:checked {{
        background-color: {colors['accent']};
        border-color: {colors['accent']};
    }}

    QRadioButton {{
        spacing: {SPACING['sm']};
        color: {colors['text_primary']};
    }}

    QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border: 1px solid {colors['border']};
        border-radius: 9px;
        background-color: {colors['bg_card']};
    }}

    QRadioButton::indicator:checked {{
        background-color: {colors['accent']};
        border: 4px solid {colors['bg_card']};
        border-color: {colors['accent']};
    }}

    /* ========================================
       MESSAGE BOX
       ======================================== */

    QMessageBox {{
        background-color: {colors['bg_card']};
    }}

    QMessageBox QLabel {{
        color: {colors['text_primary']};
        font-size: {FONTS['size_base']};
    }}

    /* ========================================
       TOOLTIPS
       ======================================== */

    QToolTip {{
        background-color: {colors['text_primary']};
        color: {colors['text_inverse']};
        border: none;
        border-radius: {RADIUS['sm']};
        padding: {SPACING['xs']} {SPACING['sm']};
        font-size: {FONTS['size_sm']};
    }}

    /* ========================================
       LIST WIDGET
       ======================================== */

    QListWidget {{
        background-color: {colors['bg_card']};
        border: 1px solid {colors['border_light']};
        border-radius: {RADIUS['md']};
        color: {colors['text_primary']};
    }}

    QListWidget::item {{
        padding: {SPACING['sm']} {SPACING['md']};
        border-bottom: 1px solid {colors['border_light']};
    }}

    QListWidget::item:hover {{
        background-color: {colors['bg_hover']};
    }}

    QListWidget::item:selected {{
        background-color: {colors['accent']};
        color: {colors['text_inverse']};
    }}
    """


def get_card_style(accent_color: str = None) -> str:
    """
    Returns stylesheet for a card widget.
    Use this for summary cards, info panels, etc.

    Args:
        accent_color: Optional accent color for the card border
    """
    colors = theme_manager.get_colors()
    border_color = accent_color if accent_color else colors['border_light']
    return f"""
        QFrame {{
            background-color: {colors['bg_card']};
            border: 1px solid {border_color};
            border-radius: {RADIUS['lg']};
            padding: {SPACING['lg']};
        }}
    """


def get_primary_button_style() -> str:
    """Primary action button style"""
    colors = theme_manager.get_colors()
    return f"""
        QPushButton {{
            background-color: {colors['accent']};
            color: {colors['text_inverse']};
            border: none;
            border-radius: {RADIUS['md']};
            padding: {SPACING['sm']} {SPACING['lg']};
            font-weight: 500;
            min-height: 36px;
        }}
        QPushButton:hover {{
            background-color: {colors['accent_hover']};
        }}
        QPushButton:pressed {{
            background-color: {colors['accent_pressed']};
        }}
    """


def get_secondary_button_style() -> str:
    """Secondary/outline button style"""
    colors = theme_manager.get_colors()
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {colors['accent']};
            border: 1px solid {colors['accent']};
            border-radius: {RADIUS['md']};
            padding: {SPACING['sm']} {SPACING['lg']};
            font-weight: 500;
            min-height: 36px;
        }}
        QPushButton:hover {{
            background-color: {colors['bg_hover']};
        }}
        QPushButton:pressed {{
            background-color: {colors['bg_pressed']};
        }}
    """


def get_subtle_button_style() -> str:
    """Subtle but visible button style (for save buttons, etc.)"""
    colors = theme_manager.get_colors()
    return f"""
        QPushButton {{
            background-color: {colors['bg_hover']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: {RADIUS['md']};
            padding: {SPACING['sm']} {SPACING['lg']};
            font-weight: 500;
            min-height: 36px;
        }}
        QPushButton:hover {{
            background-color: {colors['bg_pressed']};
            border-color: {colors['accent']};
        }}
        QPushButton:pressed {{
            background-color: {colors['accent']};
            color: {colors['text_inverse']};
            border-color: {colors['accent']};
        }}
    """


def get_danger_button_style() -> str:
    """Danger/destructive action button style"""
    colors = theme_manager.get_colors()
    return f"""
        QPushButton {{
            background-color: {colors['danger']};
            color: {colors['text_inverse']};
            border: none;
            border-radius: {RADIUS['md']};
            padding: {SPACING['sm']} {SPACING['lg']};
            font-weight: 500;
            min-height: 36px;
        }}
        QPushButton:hover {{
            background-color: {colors['danger_hover']};
        }}
    """


# Convenience function to apply stylesheet to app
def apply_stylesheet(app) -> None:
    """
    Apply the design system stylesheet to a QApplication.
    Also registers the app with theme_manager for dynamic updates.

    Usage:
        from dragofactu.ui.styles import apply_stylesheet

        app = QApplication(sys.argv)
        apply_stylesheet(app)
    """
    theme_manager.set_app(app)
    # Initialize theme from saved settings
    theme_manager.set_theme(theme_manager.current_theme)
