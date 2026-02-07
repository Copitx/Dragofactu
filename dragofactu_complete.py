#!/usr/bin/env python3
"""
DRAGOFACTU - Complete Business Management System
Fixed version with proper data persistence and full functionality
v2.0.0 - Multi-tenant with optional API backend support
"""

import sys
import os
import logging
import uuid
import json
from datetime import datetime, date
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('dragofactu')


# ============================================================================
# APPLICATION MODE (Local vs Remote API)
# ============================================================================

MODE_LOCAL = "local"
MODE_REMOTE = "remote"


class AppMode:
    """
    Singleton to manage application mode (local SQLite vs remote API).

    Usage:
        mode = get_app_mode()
        mode.set_remote("https://tu-app.railway.app")

        if mode.is_remote:
            clients = mode.api.list_clients()
        else:
            # Use local SQLite
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._mode = MODE_LOCAL
            cls._instance._api_client = None
            cls._instance._server_url = ""
            cls._instance._load_config()
        return cls._instance

    def _get_config_path(self) -> Path:
        return Path.home() / ".dragofactu" / "app_mode.json"

    def _load_config(self):
        """Load saved configuration."""
        config_path = self._get_config_path()
        if config_path.exists():
            try:
                data = json.loads(config_path.read_text())
                self._server_url = data.get("server_url", "")
                self._mode = data.get("mode", MODE_LOCAL)
            except Exception as e:
                logger.warning(f"Error loading app mode config: {e}")

    def _save_config(self):
        """Save configuration."""
        config_path = self._get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "server_url": self._server_url,
            "mode": self._mode
        }
        config_path.write_text(json.dumps(data, indent=2))

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def is_remote(self) -> bool:
        return self._mode == MODE_REMOTE

    @property
    def is_local(self) -> bool:
        return self._mode == MODE_LOCAL

    @property
    def server_url(self) -> str:
        return self._server_url

    @property
    def api(self):
        """Get API client using singleton (creates if needed)."""
        if self._api_client is None and self._server_url:
            from dragofactu.services.api_client import get_api_client
            self._api_client = get_api_client(self._server_url)
        return self._api_client

    def set_remote(self, server_url: str) -> bool:
        """
        Set remote mode with server URL.
        Returns True if connection successful.
        """
        try:
            from dragofactu.services.api_client import get_api_client, reset_api_client
        except ImportError as e:
            logger.error(f"Failed to import APIClient: {e}")
            raise RuntimeError(f"Falta el módulo 'requests'. Ejecuta: pip install requests")

        self._server_url = server_url.rstrip("/")
        # Reset and get new client with new URL
        reset_api_client()
        self._api_client = get_api_client(self._server_url)

        # Test connection
        try:
            health = self._api_client.health_check()
            if health.get("status") == "healthy":
                self._mode = MODE_REMOTE
                self._save_config()
                logger.info(f"Connected to remote server: {server_url}")
                return True
            else:
                logger.warning(f"Server returned unhealthy status: {health}")
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}")
            raise RuntimeError(f"No se pudo conectar: {e}")

        return False

    def set_local(self):
        """Set local mode (SQLite)."""
        self._mode = MODE_LOCAL
        self._api_client = None
        try:
            from dragofactu.services.api_client import reset_api_client
            reset_api_client()
        except ImportError:
            pass
        self._save_config()
        logger.info("Switched to local mode")

    def clear_api_tokens(self):
        """Clear saved API tokens (for logout)."""
        if self._api_client:
            self._api_client.logout()


def get_app_mode() -> AppMode:
    """Get the application mode singleton."""
    return AppMode()

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QLineEdit, QComboBox, QDialog, QDialogButtonBox,
    QFormLayout, QSpinBox, QMenuBar, QStatusBar,
    QHeaderView, QTextEdit, QDateEdit, QFrame,
    QDoubleSpinBox, QCheckBox, QGroupBox, QGridLayout,
    QTimeEdit, QInputDialog, QFileDialog, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QDate, QTime, QTimer, QPropertyAnimation
from PySide6.QtGui import QFont, QAction, QColor, QPixmap
from PySide6.QtWidgets import QGraphicsOpacityEffect

from sqlalchemy.orm import joinedload

from dragofactu.models.database import SessionLocal, engine, Base
from dragofactu.models.entities import User, Client, Product, Document, DocumentLine, DocumentType, DocumentStatus, Reminder, Worker, Course
from dragofactu.services.auth.auth_service import AuthService
from dragofactu.config.translation import translator
from dragofactu.ui.styles import apply_stylesheet


class UIStyles:
    """Shared UI styles for Apple-inspired design system"""

    # Light color palette
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
        'success': '#34C759',
        'warning': '#FF9500',
        'danger': '#FF3B30',
        'danger_hover': '#CC2F26',
        'border': '#D2D2D7',
        'border_light': '#E5E5EA',
    }

    # Dark color palette
    DARK_COLORS = {
        'bg_app': '#1C1C1E',
        'bg_card': '#2C2C2E',
        'bg_hover': '#3A3A3C',
        'bg_pressed': '#48484A',
        'text_primary': '#FFFFFF',
        'text_secondary': '#AEAEB2',
        'text_tertiary': '#636366',
        'text_inverse': '#FFFFFF',
        'accent': '#0A84FF',
        'accent_hover': '#409CFF',
        'success': '#30D158',
        'warning': '#FF9F0A',
        'danger': '#FF453A',
        'danger_hover': '#FF6961',
        'border': '#48484A',
        'border_light': '#38383A',
    }

    _dark_mode = False

    # Active palette (starts as light)
    COLORS = dict(LIGHT_COLORS)

    @classmethod
    def set_dark_mode(cls, enabled: bool):
        """Toggle dark/light mode and update the active palette."""
        cls._dark_mode = enabled
        source = cls.DARK_COLORS if enabled else cls.LIGHT_COLORS
        cls.COLORS.update(source)

    @classmethod
    def is_dark_mode(cls) -> bool:
        return cls._dark_mode

    @classmethod
    def get_panel_style(cls):
        """Style for main panels/tabs"""
        return f"""
            QWidget {{
                background-color: {cls.COLORS['bg_app']};
            }}
        """

    @classmethod
    def get_card_style(cls):
        """Style for card containers"""
        return f"""
            QFrame {{
                background-color: {cls.COLORS['bg_card']};
                border: none;
                border-radius: 12px;
            }}
        """

    @classmethod
    def get_primary_button_style(cls):
        """Style for primary action buttons"""
        return f"""
            QPushButton {{
                background-color: {cls.COLORS['accent']};
                color: {cls.COLORS['text_inverse']};
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 500;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {cls.COLORS['accent_hover']};
            }}
            QPushButton:pressed {{
                background-color: #004499;
            }}
        """

    @classmethod
    def get_secondary_button_style(cls):
        """Style for secondary buttons"""
        return f"""
            QPushButton {{
                background-color: {cls.COLORS['bg_card']};
                color: {cls.COLORS['text_primary']};
                border: 1px solid {cls.COLORS['border']};
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 500;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {cls.COLORS['bg_hover']};
            }}
        """

    @classmethod
    def get_danger_button_style(cls):
        """Style for danger/delete buttons"""
        return f"""
            QPushButton {{
                background-color: {cls.COLORS['danger']};
                color: {cls.COLORS['text_inverse']};
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 500;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {cls.COLORS['danger_hover']};
            }}
        """

    @classmethod
    def get_table_style(cls):
        """Style for data tables"""
        return f"""
            QTableWidget {{
                background-color: {cls.COLORS['bg_card']};
                border: 1px solid {cls.COLORS['border_light']};
                border-radius: 12px;
                gridline-color: {cls.COLORS['border_light']};
                selection-background-color: {cls.COLORS['accent']};
                selection-color: {cls.COLORS['text_inverse']};
            }}
            QTableWidget::item {{
                padding: 8px 12px;
                border-bottom: 1px solid {cls.COLORS['border_light']};
            }}
            QTableWidget::item:hover {{
                background-color: {cls.COLORS['bg_hover']};
            }}
            QHeaderView::section {{
                background-color: {cls.COLORS['bg_app']};
                color: {cls.COLORS['text_secondary']};
                font-weight: 600;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                padding: 10px 12px;
                border: none;
                border-bottom: 1px solid {cls.COLORS['border']};
            }}
        """

    @classmethod
    def get_input_style(cls):
        """Style for input fields"""
        return f"""
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {{
                background-color: {cls.COLORS['bg_card']};
                border: 1px solid {cls.COLORS['border']};
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 13px;
                color: {cls.COLORS['text_primary']};
                min-height: 20px;
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
                border-color: {cls.COLORS['accent']};
            }}
        """

    @classmethod
    def get_section_title_style(cls):
        """Style for section titles"""
        return f"""
            font-size: 17px;
            font-weight: 600;
            color: {cls.COLORS['text_primary']};
            background: transparent;
        """

    @classmethod
    def get_label_style(cls):
        """Style for labels"""
        return f"""
            color: {cls.COLORS['text_secondary']};
            font-size: 13px;
            background: transparent;
        """

    @classmethod
    def get_status_label_style(cls):
        """Style for status labels"""
        return f"""
            color: {cls.COLORS['text_tertiary']};
            font-size: 12px;
            background: transparent;
            padding: 8px 0;
        """

    @classmethod
    def get_group_box_style(cls):
        """Style for group boxes"""
        return f"""
            QGroupBox {{
                background-color: {cls.COLORS['bg_card']};
                border: 1px solid {cls.COLORS['border_light']};
                border-radius: 12px;
                margin-top: 16px;
                padding: 20px;
                padding-top: 32px;
                font-weight: 600;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                color: {cls.COLORS['text_primary']};
                font-size: 13px;
            }}
        """

    @classmethod
    def get_dialog_style(cls):
        """Style for dialogs"""
        return f"""
            QDialog {{
                background-color: {cls.COLORS['bg_app']};
            }}
            QDialogButtonBox QPushButton {{
                background-color: {cls.COLORS['accent']};
                color: {cls.COLORS['text_inverse']};
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 500;
                font-size: 13px;
                min-width: 80px;
            }}
            QDialogButtonBox QPushButton:hover {{
                background-color: {cls.COLORS['accent_hover']};
            }}
            QDialogButtonBox QPushButton[text="Cancel"],
            QDialogButtonBox QPushButton[text="Cancelar"],
            QDialogButtonBox QPushButton[text="No"] {{
                background-color: {cls.COLORS['bg_card']};
                color: {cls.COLORS['text_primary']};
                border: 1px solid {cls.COLORS['border']};
            }}
            QDialogButtonBox QPushButton[text="Cancel"]:hover,
            QDialogButtonBox QPushButton[text="Cancelar"]:hover,
            QDialogButtonBox QPushButton[text="No"]:hover {{
                background-color: {cls.COLORS['bg_hover']};
            }}
        """

    @classmethod
    def get_toolbar_button_style(cls):
        """Style for small toolbar icon buttons"""
        return f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
                padding: 6px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {cls.COLORS['bg_hover']};
            }}
        """


# =============================================================================
# Toast Notification System
# =============================================================================

class ToastNotification(QWidget):
    """Non-intrusive floating notification that auto-dismisses."""

    TOAST_COLORS = {
        "success": {"bg": "#34C759", "icon": "OK"},
        "warning": {"bg": "#FF9500", "icon": "!"},
        "error": {"bg": "#FF3B30", "icon": "X"},
        "info": {"bg": "#007AFF", "icon": "i"},
    }

    def __init__(self, message, toast_type="success", duration=3000, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self._duration = duration
        self._toast_type = toast_type
        colors = self.TOAST_COLORS.get(toast_type, self.TOAST_COLORS["info"])

        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(10)

        # Icon
        icon_label = QLabel(colors["icon"])
        icon_label.setFixedSize(24, 24)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(f"""
            background-color: rgba(255,255,255,0.3);
            border-radius: 12px;
            font-weight: 700;
            font-size: 12px;
            color: white;
        """)
        layout.addWidget(icon_label)

        # Message
        msg_label = QLabel(message)
        msg_label.setStyleSheet("color: white; font-size: 13px; font-weight: 500; background: transparent;")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label, 1)

        # Close button
        close_btn = QPushButton("x")
        close_btn.setFixedSize(20, 20)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton { background: transparent; border: none; color: rgba(255,255,255,0.7); font-size: 14px; font-weight: 600; }
            QPushButton:hover { color: white; }
        """)
        close_btn.clicked.connect(self._fade_out)
        layout.addWidget(close_btn)

        # Background styling
        self._bg_color = colors["bg"]
        self.setMinimumWidth(320)
        self.setMaximumWidth(420)

        # Opacity effect for fade animation
        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity)

        # Timer for auto-close
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._fade_out)

    def paintEvent(self, event):
        """Custom paint for rounded background."""
        from PySide6.QtGui import QPainter, QColor, QPainterPath
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect().toRectF(), 10, 10)
        painter.fillPath(path, QColor(self._bg_color))
        painter.end()

    def show_toast(self, parent_widget=None):
        """Show the toast with fade-in animation at top-right of parent."""
        if parent_widget:
            parent_geo = parent_widget.geometry()
            x = parent_geo.right() - self.sizeHint().width() - 20
            y = parent_geo.top() + 60
            self.move(x, y)

        self.show()
        self.raise_()

        # Fade in
        self._fade_anim = QPropertyAnimation(self._opacity, b"opacity")
        self._fade_anim.setDuration(200)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.start()

        self._timer.start(self._duration)

    def _fade_out(self):
        """Fade out and close."""
        self._timer.stop()
        anim = QPropertyAnimation(self._opacity, b"opacity")
        anim.setDuration(300)
        anim.setStartValue(self._opacity.opacity())
        anim.setEndValue(0.0)
        anim.finished.connect(self.close)
        anim.finished.connect(self.deleteLater)
        anim.start()
        self._close_anim = anim  # prevent GC


def show_toast(parent, message, toast_type="success", duration=3000):
    """Convenience function to show a toast notification."""
    toast = ToastNotification(message, toast_type, duration)
    toast.show_toast(parent)
    return toast


# =============================================================================
# Document Status Translation (Spanish)
# =============================================================================

# Map DocumentStatus enum values to Spanish labels
STATUS_LABELS_ES = {
    "draft": "Borrador",
    "not_sent": "No Enviado",
    "sent": "Enviado",
    "accepted": "Aceptado",
    "rejected": "Rechazado",
    "paid": "Pagado",
    "partially_paid": "Pago Parcial",
    "cancelled": "Cancelado",
}

# Reverse map: Spanish labels to DocumentStatus enum values
STATUS_VALUES = {v: k for k, v in STATUS_LABELS_ES.items()}

# All status labels for dropdowns (in order)
STATUS_OPTIONS_ES = [
    "Borrador",
    "No Enviado",
    "Enviado",
    "Aceptado",
    "Rechazado",
    "Pagado",
    "Pago Parcial",
    "Cancelado",
]

def get_status_label(status_value):
    """Get Spanish label for a status value"""
    if hasattr(status_value, 'value'):
        status_value = status_value.value
    return STATUS_LABELS_ES.get(str(status_value), str(status_value))

def get_status_value(status_label):
    """Get status value from Spanish label"""
    return STATUS_VALUES.get(status_label, status_label)


# =============================================================================
# PDF Generation for Spanish Invoices
# =============================================================================

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from decimal import Decimal
import json
import shutil


class PDFSettingsManager:
    """
    Manages PDF configuration settings with persistence.

    Settings are stored in a JSON file in the config directory.
    Allows users to customize company info, logo, and footer text.
    """

    # Default settings
    DEFAULT_SETTINGS = {
        'company_name': 'Your Company Name',
        'company_address': 'Your Address',
        'company_phone': 'Your Phone',
        'company_email': 'your-email@company.com',
        'company_cif': 'Your CIF',
        'logo_path': '',
        'footer_text': 'Este documento es valido como factura segun la normativa fiscal vigente.\nForma de pago: Transferencia bancaria | Plazo de pago: 30 dias\nGracias por confiar en nosotros.',
    }

    _instance = None
    _settings = None
    _config_path = None

    @classmethod
    def get_instance(cls):
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = PDFSettingsManager()
        return cls._instance

    def __init__(self):
        """Initialize settings manager"""
        # Determine config file path
        self._config_path = self._get_config_path()
        self._settings = self._load_settings()

    def _get_config_path(self):
        """Get the path to the config file"""
        # Try to use user's config directory
        config_dir = os.path.join(os.path.expanduser('~'), '.dragofactu')
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, 'pdf_settings.json')

    def _load_settings(self):
        """Load settings from file or return defaults"""
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    settings = self.DEFAULT_SETTINGS.copy()
                    settings.update(loaded)
                    return settings
            except Exception as e:
                logger.error(f"Error loading PDF settings: {e}")
                return self.DEFAULT_SETTINGS.copy()
        return self.DEFAULT_SETTINGS.copy()

    def save_settings(self, settings):
        """Save settings to file"""
        try:
            self._settings = settings
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            logger.info(f"PDF settings saved to {self._config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving PDF settings: {e}")
            return False

    def get_settings(self):
        """Get current settings"""
        return self._settings.copy()

    def get(self, key, default=None):
        """Get a specific setting"""
        return self._settings.get(key, default)

    def set(self, key, value):
        """Set a specific setting and save"""
        self._settings[key] = value
        self.save_settings(self._settings)

    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self._settings = self.DEFAULT_SETTINGS.copy()
        self.save_settings(self._settings)

    def copy_logo(self, source_path):
        """
        Copy logo file to config directory and update settings.

        Args:
            source_path: Path to the source logo file

        Returns:
            New path to the copied logo, or None on error
        """
        if not source_path or not os.path.exists(source_path):
            return None

        try:
            config_dir = os.path.dirname(self._config_path)
            ext = os.path.splitext(source_path)[1].lower()
            logo_filename = f"company_logo{ext}"
            dest_path = os.path.join(config_dir, logo_filename)

            shutil.copy2(source_path, dest_path)
            self.set('logo_path', dest_path)
            logger.info(f"Logo copied to {dest_path}")
            return dest_path
        except Exception as e:
            logger.error(f"Error copying logo: {e}")
            return None

    def remove_logo(self):
        """Remove current logo"""
        current_logo = self._settings.get('logo_path', '')
        if current_logo and os.path.exists(current_logo):
            try:
                os.remove(current_logo)
            except Exception as e:
                logger.warning(f"Could not remove logo file: {e}")
        self.set('logo_path', '')


# Global function to get PDF settings
def get_pdf_settings():
    """Get PDF settings manager instance"""
    return PDFSettingsManager.get_instance()


class InvoicePDFGenerator:
    """
    Professional Spanish Invoice PDF Generator

    Generates clean, professional invoices following Spanish standards:
    - Company header with logo (optional)
    - Client details
    - Invoice number and dates
    - Line items table
    - Subtotal, IVA (21%), and Total
    """

    # Colors matching UIStyles
    COLORS = {
        'primary': colors.HexColor('#1D1D1F'),
        'secondary': colors.HexColor('#6E6E73'),
        'accent': colors.HexColor('#007AFF'),
        'border': colors.HexColor('#D2D2D7'),
        'bg_light': colors.HexColor('#F5F5F7'),
        'white': colors.white,
    }

    # Default IVA rate in Spain
    IVA_RATE = Decimal('0.21')

    def __init__(self):
        """Initialize PDF generator with company configuration from PDFSettingsManager"""
        # Load settings from persistent config (user-editable via Settings dialog)
        pdf_settings = get_pdf_settings()
        settings = pdf_settings.get_settings()

        self.company_name = settings.get('company_name', 'Your Company Name')
        self.company_address = settings.get('company_address', 'Your Address')
        self.company_phone = settings.get('company_phone', 'Your Phone')
        self.company_email = settings.get('company_email', 'your-email@company.com')
        self.company_cif = settings.get('company_cif', 'Your CIF')
        self.logo_path = settings.get('logo_path', '')
        self.footer_text = settings.get('footer_text', 'Este documento es valido como factura segun la normativa fiscal vigente.\nForma de pago: Transferencia bancaria | Plazo de pago: 30 dias\nGracias por confiar en nosotros.')

        # Page dimensions
        self.page_width, self.page_height = A4
        self.margin = 20 * mm

    def generate(self, document, lines, client, output_path):
        """
        Generate PDF invoice from document data

        Args:
            document: Document model instance
            lines: List of DocumentLine model instances
            client: Client model instance
            output_path: Path to save the PDF
        """
        # Create document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )

        # Build story (content)
        story = []

        # Styles
        styles = self._get_styles()

        # Header with company info and invoice details
        story.append(self._create_header(document, styles))
        story.append(Spacer(1, 10 * mm))

        # Client information
        story.append(self._create_client_section(client, styles))
        story.append(Spacer(1, 8 * mm))

        # Line items table
        story.append(self._create_items_table(lines, styles))
        story.append(Spacer(1, 6 * mm))

        # Totals section
        story.append(self._create_totals_section(document, lines, styles))
        story.append(Spacer(1, 10 * mm))

        # Notes (if any)
        if document.notes:
            story.append(self._create_notes_section(document.notes, styles))
            story.append(Spacer(1, 6 * mm))

        # Footer with payment info and legal text
        story.append(self._create_footer(styles))

        # Build PDF
        doc.build(story)

        return output_path

    def _get_styles(self):
        """Create custom paragraph styles"""
        styles = getSampleStyleSheet()

        # Company name style
        styles.add(ParagraphStyle(
            'CompanyName',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=self.COLORS['primary'],
            spaceAfter=2 * mm,
            leading=22,
        ))

        # Company info style
        styles.add(ParagraphStyle(
            'CompanyInfo',
            parent=styles['Normal'],
            fontSize=9,
            textColor=self.COLORS['secondary'],
            leading=12,
        ))

        # Invoice title style
        styles.add(ParagraphStyle(
            'InvoiceTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=self.COLORS['accent'],
            alignment=TA_RIGHT,
            spaceAfter=3 * mm,
        ))

        # Invoice info style
        styles.add(ParagraphStyle(
            'InvoiceInfo',
            parent=styles['Normal'],
            fontSize=10,
            textColor=self.COLORS['primary'],
            alignment=TA_RIGHT,
            leading=14,
        ))

        # Section header style
        styles.add(ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=11,
            textColor=self.COLORS['secondary'],
            spaceBefore=3 * mm,
            spaceAfter=2 * mm,
            leading=14,
        ))

        # Client info style
        styles.add(ParagraphStyle(
            'ClientInfo',
            parent=styles['Normal'],
            fontSize=10,
            textColor=self.COLORS['primary'],
            leading=14,
        ))

        # Table header style
        styles.add(ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontSize=9,
            textColor=self.COLORS['white'],
            alignment=TA_CENTER,
        ))

        # Notes style
        styles.add(ParagraphStyle(
            'Notes',
            parent=styles['Normal'],
            fontSize=9,
            textColor=self.COLORS['secondary'],
            leading=12,
        ))

        # Footer style
        styles.add(ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=self.COLORS['secondary'],
            alignment=TA_CENTER,
            leading=10,
        ))

        return styles

    def _create_header(self, document, styles):
        """Create header with company info, logo (optional) and invoice details"""
        # Determine document type label
        doc_type_labels = {
            DocumentType.INVOICE: 'FACTURA',
            DocumentType.QUOTE: 'PRESUPUESTO',
            DocumentType.DELIVERY_NOTE: 'ALBARAN',
        }
        doc_type_label = doc_type_labels.get(document.type, 'DOCUMENTO')

        # Company info (left side)
        company_info = []

        # Add logo if exists
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                # Create logo image with max height of 20mm
                logo = Image(self.logo_path)
                # Scale logo to fit - max width 40mm, max height 20mm
                logo_width, logo_height = logo.imageWidth, logo.imageHeight
                max_width = 40 * mm
                max_height = 20 * mm
                # Calculate scale factor
                scale = min(max_width / logo_width, max_height / logo_height)
                logo.drawWidth = logo_width * scale
                logo.drawHeight = logo_height * scale
                company_info.append(logo)
                company_info.append(Spacer(1, 2 * mm))
            except Exception as e:
                logger.warning(f"Could not load logo: {e}")

        company_info.append(Paragraph(self.company_name, styles['CompanyName']))

        company_details = f"""
        {self.company_address}<br/>
        Tel: {self.company_phone}<br/>
        Email: {self.company_email}<br/>
        CIF/NIF: {self.company_cif}
        """
        company_info.append(Paragraph(company_details, styles['CompanyInfo']))

        # Invoice info (right side)
        invoice_info = []
        invoice_info.append(Paragraph(doc_type_label, styles['InvoiceTitle']))

        issue_date = document.issue_date.strftime('%d/%m/%Y') if document.issue_date else '-'
        due_date = document.due_date.strftime('%d/%m/%Y') if document.due_date else '-'

        invoice_details = f"""
        <b>N:</b> {document.code}<br/>
        <b>Fecha:</b> {issue_date}<br/>
        <b>Vencimiento:</b> {due_date}
        """
        invoice_info.append(Paragraph(invoice_details, styles['InvoiceInfo']))

        # Create two-column table for header
        header_data = [[company_info, invoice_info]]
        header_table = Table(header_data, colWidths=[95 * mm, 75 * mm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))

        return header_table

    def _create_client_section(self, client, styles):
        """Create client information section"""
        elements = []

        # Section header
        elements.append(Paragraph('DATOS DEL CLIENTE', styles['SectionHeader']))

        # Client details
        client_name = client.name if client else 'Cliente no especificado'
        client_cif = client.tax_id if client and client.tax_id else '-'
        client_address = client.address if client and client.address else ''
        client_city = ''
        if client:
            city_parts = []
            if client.postal_code:
                city_parts.append(client.postal_code)
            if client.city:
                city_parts.append(client.city)
            if client.province:
                city_parts.append(f'({client.province})')
            client_city = ' '.join(city_parts)

        client_contact = ''
        if client:
            contact_parts = []
            if client.phone:
                contact_parts.append(f'Tel: {client.phone}')
            if client.email:
                contact_parts.append(f'Email: {client.email}')
            client_contact = ' | '.join(contact_parts)

        client_info = f"""
        <b>{client_name}</b><br/>
        CIF/NIF: {client_cif}<br/>
        {client_address}<br/>
        {client_city}<br/>
        {client_contact}
        """
        elements.append(Paragraph(client_info, styles['ClientInfo']))

        # Create container table with border
        container_data = [[elements]]
        container = Table(container_data, colWidths=[170 * mm])
        container.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, self.COLORS['border']),
            ('BACKGROUND', (0, 0), (-1, -1), self.COLORS['bg_light']),
            ('TOPPADDING', (0, 0), (-1, -1), 3 * mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3 * mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 4 * mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4 * mm),
        ]))

        return container

    def _create_items_table(self, lines, styles):
        """Create line items table"""
        # Table headers
        headers = ['DESCRIPCION', 'CANTIDAD', 'PRECIO UNIT.', 'DTO.', 'SUBTOTAL']

        # Calculate column widths
        col_widths = [85 * mm, 20 * mm, 25 * mm, 15 * mm, 25 * mm]

        # Build table data
        table_data = [headers]

        for line in lines:
            description = line.description or '-'
            quantity = f"{float(line.quantity or 0):.2f}"
            unit_price = f"{float(line.unit_price or 0):.2f} EUR"
            discount = f"{float(line.discount_percent or 0):.0f}%"
            subtotal = f"{float(line.subtotal or 0):.2f} EUR"

            table_data.append([description, quantity, unit_price, discount, subtotal])

        # If no lines, add empty row
        if not lines:
            table_data.append(['(Sin lineas)', '-', '-', '-', '-'])

        # Create table
        items_table = Table(table_data, colWidths=col_widths, repeatRows=1)

        # Style the table
        table_style = TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['accent']),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.COLORS['white']),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, 0), 3 * mm),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 3 * mm),

            # Body styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Description left
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),  # Numbers right
            ('TOPPADDING', (0, 1), (-1, -1), 2.5 * mm),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 2.5 * mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 2 * mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2 * mm),

            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [self.COLORS['white'], self.COLORS['bg_light']]),

            # Borders
            ('BOX', (0, 0), (-1, -1), 0.5, self.COLORS['border']),
            ('LINEBELOW', (0, 0), (-1, 0), 1, self.COLORS['accent']),
            ('LINEBELOW', (0, 1), (-1, -2), 0.25, self.COLORS['border']),
        ])

        items_table.setStyle(table_style)

        return items_table

    def _create_totals_section(self, document, lines, styles):
        """Create totals section with subtotal, IVA, and total"""
        # Calculate values
        subtotal = Decimal(str(document.subtotal or 0))

        # If subtotal is 0, calculate from lines
        if subtotal == 0 and lines:
            subtotal = sum(Decimal(str(line.subtotal or 0)) for line in lines)

        # Use stored tax_amount or calculate
        tax_amount = Decimal(str(document.tax_amount or 0))
        if tax_amount == 0:
            tax_amount = subtotal * self.IVA_RATE

        total = Decimal(str(document.total or 0))
        if total == 0:
            total = subtotal + tax_amount

        # Format values
        subtotal_str = f"{subtotal:.2f} EUR"
        tax_str = f"{tax_amount:.2f} EUR"
        total_str = f"{total:.2f} EUR"

        # Create totals table (right-aligned)
        totals_data = [
            ['', 'Base Imponible:', subtotal_str],
            ['', f'IVA ({int(self.IVA_RATE * 100)}%):', tax_str],
            ['', 'TOTAL:', total_str],
        ]

        col_widths = [100 * mm, 40 * mm, 30 * mm]
        totals_table = Table(totals_data, colWidths=col_widths)

        totals_table.setStyle(TableStyle([
            # Labels
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (1, 0), (1, -1), 10),
            ('TEXTCOLOR', (1, 0), (1, 1), self.COLORS['secondary']),

            # Values
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('FONTNAME', (2, 0), (2, 1), 'Helvetica'),
            ('FONTSIZE', (2, 0), (2, 1), 10),

            # Total row (bold and larger)
            ('FONTNAME', (1, 2), (2, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (1, 2), (2, 2), 12),
            ('TEXTCOLOR', (1, 2), (2, 2), self.COLORS['primary']),
            ('LINEABOVE', (1, 2), (2, 2), 1, self.COLORS['accent']),
            ('TOPPADDING', (1, 2), (2, 2), 3 * mm),

            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 1.5 * mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
            ('RIGHTPADDING', (2, 0), (2, -1), 3 * mm),
        ]))

        return totals_table

    def _create_notes_section(self, notes, styles):
        """Create notes section"""
        elements = []
        elements.append(Paragraph('OBSERVACIONES', styles['SectionHeader']))
        elements.append(Paragraph(notes, styles['Notes']))

        container_data = [[elements]]
        container = Table(container_data, colWidths=[170 * mm])
        container.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, self.COLORS['border']),
            ('BACKGROUND', (0, 0), (-1, -1), self.COLORS['bg_light']),
            ('TOPPADDING', (0, 0), (-1, -1), 2 * mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2 * mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 3 * mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3 * mm),
        ]))

        return container

    def _create_footer(self, styles):
        """Create footer with customizable legal text"""
        # Use custom footer text, replacing newlines with <br/> for HTML
        footer_content = self.footer_text.replace('\n', '<br/>')
        return Paragraph(footer_content, styles['Footer'])


class Dashboard(QWidget):
    """Modern Apple-inspired dashboard with clean design"""

    # Design tokens from styles.py
    COLORS = {
        'bg_app': '#FAFAFA',
        'bg_card': '#FFFFFF',
        'bg_hover': '#F5F5F7',
        'text_primary': '#1D1D1F',
        'text_secondary': '#6E6E73',
        'text_tertiary': '#86868B',
        'accent': '#007AFF',
        'accent_hover': '#0056CC',
        'success': '#34C759',
        'warning': '#FF9500',
        'danger': '#FF3B30',
        'border_light': '#E5E5EA',
    }

    def __init__(self):
        super().__init__()
        self.metric_labels = {}
        self.metric_titles = {}
        self.translatable_labels = {}
        self.setup_ui()

    def setup_ui(self):
        """Setup modern dashboard UI"""
        # Main layout with generous margins
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # Set background
        self.setStyleSheet(f"background-color: {self.COLORS['bg_app']};")

        # 1. Welcome Section
        self._create_welcome_section(layout)

        # 2. Metrics Cards
        self._create_metrics_section(layout)

        # 3. Pending Reminders Section
        self._create_pending_reminders(layout)

        # 4. Quick Actions
        self._create_quick_actions(layout)

        # 5. Recent Documents
        self._create_recent_documents(layout)

        layout.addStretch()

    def _update_datetime(self):
        """Update date and time labels"""
        from datetime import datetime
        now = datetime.now()
        # Date in Spanish format
        days = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
        months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        day_name = days[now.weekday()]
        month_name = months[now.month - 1]
        date_str = f"{day_name}, {now.day} de {month_name} de {now.year}"
        time_str = now.strftime("%H:%M:%S")

        if hasattr(self, 'date_label'):
            self.date_label.setText(date_str)
        if hasattr(self, 'time_label'):
            self.time_label.setText(time_str)

    def _create_welcome_section(self, parent_layout):
        """Create welcome header section"""
        welcome_widget = QWidget()
        welcome_layout = QHBoxLayout(welcome_widget)
        welcome_layout.setContentsMargins(0, 0, 0, 0)
        welcome_layout.setSpacing(16)

        # Left side: Welcome text
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        # Welcome title
        self.welcome_label = QLabel(translator.t("dashboard.welcome"))
        self.welcome_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 600;
            color: {self.COLORS['text_primary']};
            background: transparent;
        """)
        left_layout.addWidget(self.welcome_label)

        # Subtitle
        self.subtitle_label = QLabel(translator.t("app.subtitle"))
        self.subtitle_label.setStyleSheet(f"""
            font-size: 15px;
            color: {self.COLORS['text_secondary']};
            background: transparent;
        """)
        left_layout.addWidget(self.subtitle_label)

        welcome_layout.addWidget(left_widget)
        welcome_layout.addStretch()

        # Right side: Date and time
        datetime_widget = QWidget()
        datetime_layout = QVBoxLayout(datetime_widget)
        datetime_layout.setContentsMargins(0, 0, 0, 0)
        datetime_layout.setSpacing(2)
        datetime_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Date
        self.date_label = QLabel()
        self.date_label.setStyleSheet(f"""
            font-size: 15px;
            font-weight: 500;
            color: {self.COLORS['text_primary']};
            background: transparent;
        """)
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        datetime_layout.addWidget(self.date_label)

        # Time
        self.time_label = QLabel()
        self.time_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 600;
            color: {self.COLORS['accent']};
            background: transparent;
        """)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        datetime_layout.addWidget(self.time_label)

        welcome_layout.addWidget(datetime_widget)

        # Update date/time immediately and start timer
        self._update_datetime()
        from PySide6.QtCore import QTimer
        self.datetime_timer = QTimer(self)
        self.datetime_timer.timeout.connect(self._update_datetime)
        self.datetime_timer.start(1000)  # Update every second

        parent_layout.addWidget(welcome_widget)

    def _create_metrics_section(self, parent_layout):
        """Create metrics cards row"""
        metrics_widget = QWidget()
        metrics_layout = QHBoxLayout(metrics_widget)
        metrics_layout.setContentsMargins(0, 0, 0, 0)
        metrics_layout.setSpacing(16)

        # Define metrics with translation keys
        metrics = [
            ('clients', 'dashboard.total_clients', self.get_client_count()),
            ('products', 'dashboard.active_products', self.get_product_count()),
            ('documents', 'dashboard.pending_documents', self.get_document_count()),
            ('low_stock', 'dashboard.low_stock_items', self.get_low_stock_count()),
        ]

        for key, title_key, value in metrics:
            card = self._create_metric_card(key, title_key, value)
            metrics_layout.addWidget(card)

        parent_layout.addWidget(metrics_widget)

    def _create_metric_card(self, key, title_key, value):
        """Create a single metric card"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.COLORS['bg_card']};
                border: none;
                border-radius: 12px;
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(8)

        # Title label (translated)
        title_label = QLabel(translator.t(title_key))
        title_label.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 500;
            color: {self.COLORS['text_secondary']};
            background: transparent;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        """)
        card_layout.addWidget(title_label)

        # Value label
        value_label = QLabel(str(value))
        value_label.setStyleSheet(f"""
            font-size: 32px;
            font-weight: 600;
            color: {self.COLORS['text_primary']};
            background: transparent;
        """)
        card_layout.addWidget(value_label)

        # Store references for updates
        self.metric_labels[key] = value_label
        self.metric_titles[key] = (title_label, title_key)

        return card

    def _create_pending_reminders(self, parent_layout):
        """Create pending documents and user reminders sections side by side"""
        # Container for both sections
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(16)

        # LEFT SIDE: Pending Documents
        pending_widget = QWidget()
        pending_main_layout = QVBoxLayout(pending_widget)
        pending_main_layout.setContentsMargins(0, 0, 0, 0)
        pending_main_layout.setSpacing(8)

        # Pending title
        self.pending_title = QLabel("Documentos Pendientes")
        self.pending_title.setStyleSheet(f"""
            font-size: 17px;
            font-weight: 600;
            color: {self.COLORS['text_primary']};
            background: transparent;
        """)
        pending_main_layout.addWidget(self.pending_title)

        # Pending frame
        self.pending_frame = QFrame()
        self.pending_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.COLORS['bg_card']};
                border: none;
                border-radius: 12px;
            }}
        """)

        self.pending_layout = QVBoxLayout(self.pending_frame)
        self.pending_layout.setContentsMargins(0, 0, 0, 0)
        self.pending_layout.setSpacing(0)

        self._populate_pending_documents()
        pending_main_layout.addWidget(self.pending_frame)

        container_layout.addWidget(pending_widget, 1)

        # RIGHT SIDE: User Reminders
        reminders_widget = QWidget()
        reminders_main_layout = QVBoxLayout(reminders_widget)
        reminders_main_layout.setContentsMargins(0, 0, 0, 0)
        reminders_main_layout.setSpacing(8)

        # Reminders title
        self.user_reminders_title = QLabel("Recordatorios")
        self.user_reminders_title.setStyleSheet(f"""
            font-size: 17px;
            font-weight: 600;
            color: {self.COLORS['text_primary']};
            background: transparent;
        """)
        reminders_main_layout.addWidget(self.user_reminders_title)

        # Reminders frame
        self.user_reminders_frame = QFrame()
        self.user_reminders_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.COLORS['bg_card']};
                border: none;
                border-radius: 12px;
            }}
        """)

        self.user_reminders_layout = QVBoxLayout(self.user_reminders_frame)
        self.user_reminders_layout.setContentsMargins(0, 0, 0, 0)
        self.user_reminders_layout.setSpacing(0)

        self._populate_user_reminders()
        reminders_main_layout.addWidget(self.user_reminders_frame)

        container_layout.addWidget(reminders_widget, 1)

        parent_layout.addWidget(container)

    def _populate_pending_documents(self):
        """Populate pending documents list"""
        # Clear existing items
        while self.pending_layout.count():
            child = self.pending_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        pending_items = self._get_pending_items()

        if pending_items:
            for i, item in enumerate(pending_items[:5]):  # Max 5 items
                is_last = (i == len(pending_items[:5]) - 1)
                row = self._create_pending_row(item, is_last)
                self.pending_layout.addWidget(row)
        else:
            empty_label = QLabel("No hay documentos pendientes")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet(f"""
                font-size: 14px;
                color: {self.COLORS['text_tertiary']};
                padding: 24px;
                background: transparent;
            """)
            self.pending_layout.addWidget(empty_label)

    def _populate_user_reminders(self):
        """Populate user reminders list"""
        # Clear existing items
        while self.user_reminders_layout.count():
            child = self.user_reminders_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        reminders = self._get_user_reminders()

        if reminders:
            for i, reminder in enumerate(reminders[:5]):  # Max 5 items
                is_last = (i == len(reminders[:5]) - 1)
                row = self._create_user_reminder_row(reminder, is_last)
                self.user_reminders_layout.addWidget(row)
        else:
            empty_label = QLabel("No hay recordatorios")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet(f"""
                font-size: 14px;
                color: {self.COLORS['text_tertiary']};
                padding: 24px;
                background: transparent;
            """)
            self.user_reminders_layout.addWidget(empty_label)

    def _get_user_reminders(self):
        """Get user reminders - supports local and remote"""
        app_mode = get_app_mode()
        try:
            if app_mode.is_remote:
                # Fetch from API
                response = app_mode.api.list_reminders(pending_only=True)
                items = response.get("items", [])
                result = []
                for r in items:
                    result.append({
                        'id': str(r.get('id', '')),
                        'title': r.get('title', ''),
                        'description': r.get('description', ''),
                        'due_date': r.get('due_date'),
                        'priority': r.get('priority', 'normal'),
                    })
                return result
            else:
                # Fetch from local database
                with SessionLocal() as db:
                    reminders = db.query(Reminder).filter(
                        Reminder.is_completed == False
                    ).order_by(Reminder.due_date.asc().nullslast(), Reminder.created_at.desc()).limit(10).all()

                    result = []
                    for r in reminders:
                        result.append({
                            'id': str(r.id),
                            'title': r.title,
                            'description': r.description,
                            'due_date': r.due_date,
                            'priority': r.priority or 'normal',
                        })
                    return result
        except Exception as e:
            logger.error(f"Error getting reminders: {e}")
            return []

    def _create_user_reminder_row(self, reminder, is_last=False):
        """Create a single user reminder row"""
        row = QWidget()
        border_style = "" if is_last else f"border-bottom: 1px solid {self.COLORS['border_light']};"

        priority_colors = {
            'high': self.COLORS['danger'],
            'normal': self.COLORS['accent'],
            'low': self.COLORS['text_tertiary'],
        }
        left_border_color = priority_colors.get(reminder.get('priority', 'normal'), self.COLORS['accent'])

        row.setStyleSheet(f"""
            QWidget {{
                background: transparent;
                border-left: 3px solid {left_border_color};
                {border_style}
            }}
            QWidget:hover {{
                background-color: {self.COLORS['bg_hover']};
            }}
        """)

        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(16, 12, 16, 12)
        row_layout.setSpacing(12)

        # Title
        title_label = QLabel(reminder.get('title', 'Sin título'))
        title_label.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 500;
            color: {self.COLORS['text_primary']};
            background: transparent;
        """)
        title_label.setWordWrap(True)
        row_layout.addWidget(title_label, 1)

        # Due date if exists
        due_date = reminder.get('due_date')
        if due_date:
            date_str = due_date.strftime('%d/%m') if hasattr(due_date, 'strftime') else str(due_date)[:10]
            date_label = QLabel(date_str)
            date_label.setStyleSheet(f"""
                font-size: 11px;
                color: {self.COLORS['text_tertiary']};
                background: transparent;
            """)
            row_layout.addWidget(date_label)

        return row

    # Keep old method name for compatibility - now calls the new methods
    def _populate_reminders(self):
        """Backward compatibility - populate pending documents and reminders"""
        if hasattr(self, '_populate_pending_documents'):
            self._populate_pending_documents()
        if hasattr(self, '_populate_user_reminders'):
            self._populate_user_reminders()

    def _get_pending_items(self):
        """Get pending documents (drafts, sent, accepted, partially paid, not_sent) - supports local and remote"""
        app_mode = get_app_mode()
        try:
            if app_mode.is_remote:
                # Fetch from API
                response = app_mode.api.list_documents(limit=10, doc_status="pending")
                docs = response.get("items", [])
                result = []
                for doc in docs:
                    status_value = doc.get("status", "draft")
                    status_text = get_status_label(status_value)

                    urgency = "normal"
                    if status_value == "draft":
                        urgency = "warning"
                    elif doc.get("due_date"):
                        try:
                            due_str = doc["due_date"][:10]  # YYYY-MM-DD
                            due = datetime.strptime(due_str, "%Y-%m-%d").date()
                            if due < date.today():
                                urgency = "danger"
                        except:
                            pass

                    doc_type = doc.get("type", "quote")
                    type_text = "Factura" if doc_type == "invoice" else "Presupuesto" if doc_type == "quote" else "Albaran"

                    result.append({
                        'code': doc.get('code', 'N/A'),
                        'client': doc.get('client_name', 'Sin cliente'),
                        'total': float(doc.get('total', 0)),
                        'status': status_text,
                        'urgency': urgency,
                        'type': type_text
                    })
                return result
            else:
                with SessionLocal() as db:
                    # Build list of pending statuses
                    pending_statuses = [
                        DocumentStatus.DRAFT,
                        DocumentStatus.SENT,
                        DocumentStatus.ACCEPTED,
                        DocumentStatus.PARTIALLY_PAID,
                        DocumentStatus.NOT_SENT
                    ]

                    # Get all documents that are pending action
                    pending_docs = db.query(Document).options(joinedload(Document.client)).filter(
                        Document.status.in_(pending_statuses)
                    ).order_by(Document.issue_date.desc()).limit(10).all()

                    result = []
                    for doc in pending_docs:
                        status_text = get_status_label(doc.status)

                        # Determine urgency
                        urgency = "normal"
                        if doc.status == DocumentStatus.DRAFT:
                            urgency = "warning"
                        elif doc.due_date:
                            try:
                                due = doc.due_date.date() if hasattr(doc.due_date, 'date') else doc.due_date
                                if due < date.today():
                                    urgency = "danger"
                            except:
                                pass

                        result.append({
                            'code': doc.code or 'N/A',
                            'client': doc.client.name if doc.client else 'Sin cliente',
                            'total': float(doc.total or 0),
                            'status': status_text,
                            'urgency': urgency,
                            'type': "Factura" if doc.type == DocumentType.INVOICE else "Presupuesto" if doc.type == DocumentType.QUOTE else "Albaran"
                        })
                    return result
        except Exception as e:
            logger.error(f"Error getting pending items: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _create_pending_row(self, item, is_last=False):
        """Create a single pending document row"""
        row = QWidget()
        border_style = "" if is_last else f"border-bottom: 1px solid {self.COLORS['border_light']};"

        urgency_colors = {
            'warning': self.COLORS['warning'],
            'danger': self.COLORS['danger'],
            'normal': self.COLORS['accent'],
        }
        left_border_color = urgency_colors.get(item.get('urgency', 'normal'), self.COLORS['accent'])

        row.setStyleSheet(f"""
            QWidget {{
                background: transparent;
                border-left: 3px solid {left_border_color};
                {border_style}
            }}
            QWidget:hover {{
                background-color: {self.COLORS['bg_hover']};
            }}
        """)

        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(16, 12, 20, 12)
        row_layout.setSpacing(12)

        # Type badge
        type_label = QLabel(item.get('type', 'Doc'))
        type_label.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 500;
            color: {self.COLORS['text_tertiary']};
            background: transparent;
            min-width: 70px;
        """)
        row_layout.addWidget(type_label)

        # Document code
        code_label = QLabel(item.get('code', 'N/A'))
        code_label.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 600;
            color: {self.COLORS['text_primary']};
            background: transparent;
            min-width: 100px;
        """)
        row_layout.addWidget(code_label)

        # Client name
        client_label = QLabel(item.get('client', 'Sin cliente'))
        client_label.setStyleSheet(f"""
            font-size: 13px;
            color: {self.COLORS['text_primary']};
            background: transparent;
        """)
        row_layout.addWidget(client_label, 1)

        # Amount
        amount = item.get('total', 0)
        amount_label = QLabel(f"{amount:,.2f} EUR")
        amount_label.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 500;
            color: {self.COLORS['text_primary']};
            background: transparent;
        """)
        amount_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row_layout.addWidget(amount_label)

        # Status badge
        status_label = QLabel(item.get('status', 'Pendiente'))
        status_label.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 500;
            color: {left_border_color};
            background: transparent;
            min-width: 60px;
        """)
        status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row_layout.addWidget(status_label)

        return row

    def _create_quick_actions(self, parent_layout):
        """Create quick action cards"""
        # Section title
        self.quick_actions_title = QLabel(translator.t("dashboard.quick_actions"))
        self.quick_actions_title.setStyleSheet(f"""
            font-size: 17px;
            font-weight: 600;
            color: {self.COLORS['text_primary']};
            background: transparent;
            padding-top: 8px;
        """)
        parent_layout.addWidget(self.quick_actions_title)

        # Actions container
        self.actions_widget = QWidget()
        self.actions_layout = QHBoxLayout(self.actions_widget)
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setSpacing(16)

        self._populate_quick_actions()
        parent_layout.addWidget(self.actions_widget)

    def _populate_quick_actions(self):
        """Populate quick action cards (for retranslation)"""
        # Clear existing
        while self.actions_layout.count():
            item = self.actions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Define actions with translation keys
        actions = [
            ('buttons.new_invoice', self.add_invoice),
            ('buttons.new_quote', self.add_quote),
            ('buttons.new_client', self.add_client),
            ('buttons.new_product', self.add_product),
        ]

        for title_key, callback in actions:
            action_card = self._create_action_card(translator.t(title_key), callback)
            self.actions_layout.addWidget(action_card)

    def _create_action_card(self, title, callback):
        """Create a clickable action card"""
        card = QFrame()
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.COLORS['bg_card']};
                border: none;
                border-radius: 12px;
            }}
            QFrame:hover {{
                background-color: {self.COLORS['bg_hover']};
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(6)

        # Plus icon
        icon_label = QLabel("+")
        icon_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 300;
            color: {self.COLORS['accent']};
            background: transparent;
        """)
        card_layout.addWidget(icon_label)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 15px;
            font-weight: 600;
            color: {self.COLORS['text_primary']};
            background: transparent;
        """)
        card_layout.addWidget(title_label)

        # Make card clickable
        card.mousePressEvent = lambda e: callback()

        return card

    def _create_recent_documents(self, parent_layout):
        """Create recent documents section"""
        # Section title
        self.recent_docs_title = QLabel(translator.t("dashboard.recent_documents"))
        self.recent_docs_title.setStyleSheet(f"""
            font-size: 17px;
            font-weight: 600;
            color: {self.COLORS['text_primary']};
            background: transparent;
            padding-top: 8px;
        """)
        parent_layout.addWidget(self.recent_docs_title)

        # Documents container - save reference for updates
        self.recent_docs_frame = QFrame()
        self.recent_docs_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.COLORS['bg_card']};
                border: none;
                border-radius: 12px;
            }}
        """)

        self.recent_docs_layout = QVBoxLayout(self.recent_docs_frame)
        self.recent_docs_layout.setContentsMargins(0, 0, 0, 0)
        self.recent_docs_layout.setSpacing(0)

        # Populate recent documents
        self._populate_recent_documents()

        parent_layout.addWidget(self.recent_docs_frame)

    def _populate_recent_documents(self):
        """Populate or refresh recent documents list"""
        # Clear existing items
        while self.recent_docs_layout.count():
            child = self.recent_docs_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Get recent documents
        recent_docs = self._get_recent_documents()

        if recent_docs:
            for i, doc in enumerate(recent_docs):
                doc_row = self._create_document_row(doc, is_last=(i == len(recent_docs) - 1))
                self.recent_docs_layout.addWidget(doc_row)
        else:
            # Empty state
            empty_label = QLabel("No hay documentos recientes")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet(f"""
                font-size: 14px;
                color: {self.COLORS['text_tertiary']};
                padding: 40px;
                background: transparent;
            """)
            self.recent_docs_layout.addWidget(empty_label)

    def _create_document_row(self, doc, is_last=False):
        """Create a single document row"""
        row = QWidget()
        border_style = "" if is_last else f"border-bottom: 1px solid {self.COLORS['border_light']};"
        row.setStyleSheet(f"""
            QWidget {{
                background: transparent;
                {border_style}
            }}
            QWidget:hover {{
                background-color: {self.COLORS['bg_hover']};
            }}
        """)

        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(20, 16, 20, 16)
        row_layout.setSpacing(16)

        # Document code
        code_label = QLabel(doc.get('code', 'N/A'))
        code_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {self.COLORS['text_primary']};
            background: transparent;
            min-width: 80px;
        """)
        row_layout.addWidget(code_label)

        # Client name
        client_label = QLabel(doc.get('client', 'Sin cliente'))
        client_label.setStyleSheet(f"""
            font-size: 14px;
            color: {self.COLORS['text_primary']};
            background: transparent;
        """)
        row_layout.addWidget(client_label, 1)

        # Amount
        amount = doc.get('total', 0)
        amount_label = QLabel(f"€{amount:,.2f}")
        amount_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 500;
            color: {self.COLORS['text_primary']};
            background: transparent;
            min-width: 80px;
        """)
        amount_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row_layout.addWidget(amount_label)

        # Status badge - get both value and label
        status_value = doc.get('status_value', doc.get('status', 'draft'))
        status_label_text = doc.get('status_label', get_status_label(status_value))

        status_colors = {
            'draft': self.COLORS['text_tertiary'],
            'not_sent': self.COLORS['warning'],
            'sent': self.COLORS['accent'],
            'accepted': self.COLORS['success'],
            'rejected': self.COLORS['danger'],
            'paid': self.COLORS['success'],
            'partially_paid': self.COLORS['warning'],
            'cancelled': self.COLORS['text_tertiary'],
        }
        status_color = status_colors.get(str(status_value).lower(), self.COLORS['text_tertiary'])

        status_label = QLabel(status_label_text)
        status_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 500;
            color: {status_color};
            background: transparent;
            padding: 4px 8px;
            min-width: 70px;
        """)
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row_layout.addWidget(status_label)

        return row

    def _get_recent_documents(self):
        """Get recent documents from database - supports local and remote"""
        app_mode = get_app_mode()
        try:
            if app_mode.is_remote:
                # Fetch from API
                response = app_mode.api.list_documents(limit=5)
                docs = response.get("items", [])
                result = []
                for doc in docs:
                    status_value = doc.get("status", "draft")
                    result.append({
                        'code': doc.get('code', 'N/A'),
                        'client': doc.get('client_name', 'Sin cliente'),
                        'total': float(doc.get('total', 0)),
                        'status_value': status_value,
                        'status_label': get_status_label(status_value),
                    })
                return result
            else:
                with SessionLocal() as db:
                    documents = db.query(Document).options(joinedload(Document.client)).order_by(
                        Document.created_at.desc()
                    ).limit(5).all()

                    result = []
                    for doc in documents:
                        status_value = doc.status.value if doc.status else 'draft'
                        result.append({
                            'code': doc.code or 'N/A',
                            'client': doc.client.name if doc.client else 'Sin cliente',
                            'total': float(doc.total or 0),
                            'status_value': status_value,
                            'status_label': get_status_label(status_value),
                        })
                    return result
        except Exception as e:
            logger.error(f"Error getting recent documents: {e}")
            return []

    def refresh_data(self):
        """Refresh dashboard data - supports local and remote"""
        # Invalidate cache to force fresh fetch
        self._invalidate_stats_cache()

        # Update metric values
        if 'clients' in self.metric_labels:
            self.metric_labels['clients'].setText(str(self.get_client_count()))
        if 'products' in self.metric_labels:
            self.metric_labels['products'].setText(str(self.get_product_count()))
        if 'documents' in self.metric_labels:
            self.metric_labels['documents'].setText(str(self.get_document_count()))
        if 'low_stock' in self.metric_labels:
            self.metric_labels['low_stock'].setText(str(self.get_low_stock_count()))

        # Update pending reminders
        if hasattr(self, '_populate_reminders'):
            self._populate_reminders()

        # Update recent documents
        if hasattr(self, '_populate_recent_documents'):
            self._populate_recent_documents()

        # Show cache indicator if data came from offline cache
        if hasattr(self, 'subtitle_label') and hasattr(self, '_cached_stats'):
            stats = self._cached_stats or {}
            if isinstance(stats, dict) and stats.get("_from_cache"):
                self.subtitle_label.setText(translator.t("app.subtitle") + " (datos en cache - sin conexion)")
            else:
                self.subtitle_label.setText(translator.t("app.subtitle"))

    def retranslate_ui(self):
        """Update all translatable text"""
        # Welcome section
        if hasattr(self, 'welcome_label'):
            self.welcome_label.setText(translator.t("dashboard.welcome"))
        if hasattr(self, 'subtitle_label'):
            self.subtitle_label.setText(translator.t("app.subtitle"))

        # Metric titles
        for key, (label, title_key) in self.metric_titles.items():
            label.setText(translator.t(title_key))

        # Section titles
        if hasattr(self, 'quick_actions_title'):
            self.quick_actions_title.setText(translator.t("dashboard.quick_actions"))
        if hasattr(self, 'recent_docs_title'):
            self.recent_docs_title.setText(translator.t("dashboard.recent_documents"))

        # Rebuild quick actions with new translations
        if hasattr(self, '_populate_quick_actions'):
            self._populate_quick_actions()

    def _get_remote_stats(self):
        """Fetch stats from remote API (cached for session)."""
        if not hasattr(self, '_cached_stats') or self._cached_stats is None:
            app_mode = get_app_mode()
            if app_mode.is_remote:
                try:
                    self._cached_stats = app_mode.api.get_dashboard_stats()
                except Exception as e:
                    logger.error(f"Error fetching remote stats: {e}")
                    self._cached_stats = {}
            else:
                self._cached_stats = {}
        return self._cached_stats

    def _invalidate_stats_cache(self):
        """Invalidate cached stats (call after data changes)."""
        self._cached_stats = None

    def get_client_count(self):
        """Get total clients - supports local and remote"""
        app_mode = get_app_mode()
        try:
            if app_mode.is_remote:
                return self._get_remote_stats().get("clients", 0)
            else:
                with SessionLocal() as db:
                    return db.query(Client).filter(Client.is_active == True).count()
        except Exception as e:
            logger.error(f"Error getting client count: {e}")
            return 0

    def get_product_count(self):
        """Get total products - supports local and remote"""
        app_mode = get_app_mode()
        try:
            if app_mode.is_remote:
                return self._get_remote_stats().get("products", 0)
            else:
                with SessionLocal() as db:
                    return db.query(Product).filter(Product.is_active == True).count()
        except Exception as e:
            logger.error(f"Error getting product count: {e}")
            return 0

    def get_document_count(self):
        """Get total documents - supports local and remote"""
        app_mode = get_app_mode()
        try:
            if app_mode.is_remote:
                return self._get_remote_stats().get("pending_documents", 0)
            else:
                with SessionLocal() as db:
                    return db.query(Document).count()
        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return 0

    def get_low_stock_count(self):
        """Get products with low stock - supports local and remote"""
        app_mode = get_app_mode()
        try:
            if app_mode.is_remote:
                return self._get_remote_stats().get("low_stock", 0)
            else:
                with SessionLocal() as db:
                    return db.query(Product).filter(
                        Product.current_stock <= Product.minimum_stock,
                        Product.is_active == True
                    ).count()
        except Exception as e:
            logger.error(f"Error getting low stock count: {e}")
            return 0

    def add_client(self):
        """Add new client"""
        dialog = ClientDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            show_toast(self, "Cliente añadido correctamente", "success")
            self.refresh_data()

    def add_product(self):
        """Add new product"""
        dialog = ProductDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            show_toast(self, "Producto añadido correctamente", "success")
            self.refresh_data()

    def add_quote(self):
        """Add new quote"""
        dialog = DocumentDialog(self, "quote")
        dialog.exec()
        self.refresh_data()

    def add_invoice(self):
        """Add new invoice"""
        dialog = DocumentDialog(self, "invoice")
        dialog.exec()
        self.refresh_data()

    def import_external_file(self):
        """Import external files"""
        from PySide6.QtWidgets import QFileDialog
        import json
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Archivo para Importar",
            "",
            "Todos los Archivos (*.csv *.json *.txt);;CSV Files (*.csv);;JSON Files (*.json);;Text Files (*.txt)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    self.import_csv_file(file_path)
                elif file_path.endswith('.json'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.process_imported_json(data)
                elif file_path.endswith('.txt'):
                    self.import_text_file(file_path)
                
                QMessageBox.information(self, "✅ Éxito", f"Archivo importado correctamente: {os.path.basename(file_path)}")
            except Exception as e:
                logger.error(f"Error importing file: {e}")
                QMessageBox.critical(self, "❌ Error", f"Error al importar archivo: {str(e)}")

class ConfirmationDialog(QDialog):
    """Custom styled confirmation dialog"""
    def __init__(self, parent=None, title="Confirmar", message="¿Está seguro?", 
                 confirm_text="Confirmar", cancel_text="Cancelar", is_danger=False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedWidth(400)
        
        # Style
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {UIStyles.COLORS['bg_app']};
            }}
            QLabel {{
                color: {UIStyles.COLORS['text_primary']};
                font-size: 14px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Icon and Message container
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)
        
        # Warning Icon
        icon_label = QLabel("⚠️")
        icon_label.setStyleSheet("font-size: 32px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        content_layout.addWidget(icon_label)
        
        # Message
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet(f"color: {UIStyles.COLORS['text_secondary']}; line-height: 1.4;")
        content_layout.addWidget(msg_label, 1)
        
        layout.addLayout(content_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton(cancel_text)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        confirm_btn = QPushButton(confirm_text)
        confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if is_danger:
            confirm_btn.setStyleSheet(UIStyles.get_danger_button_style())
        else:
            confirm_btn.setStyleSheet(UIStyles.get_primary_button_style())
        confirm_btn.clicked.connect(self.accept)
        btn_layout.addWidget(confirm_btn)
        
        layout.addLayout(btn_layout)

class ClientDialog(QDialog):
    """Dialog for creating and editing clients"""
    def __init__(self, parent=None, client_id=None):
        super().__init__(parent)
        self.client_id = client_id
        self.is_edit_mode = client_id is not None
        self.setWindowTitle("✏️ Editar Cliente" if self.is_edit_mode else "👤 Nuevo Cliente")
        self.setModal(True)
        # Increased height to ensure buttons are visible
        self.resize(500, 650)
        self.setup_ui()
        if self.is_edit_mode:
            self.load_client_data()

    def setup_ui(self):
        layout = QFormLayout(self)

        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("C-001")
        if self.is_edit_mode:
            self.code_edit.setReadOnly(True)
            self.code_edit.setStyleSheet("background-color: #f0f0f0;")
        layout.addRow("Código:", self.code_edit)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nombre del cliente")
        layout.addRow("Nombre (*):", self.name_edit)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("email@ejemplo.com")
        layout.addRow("Email:", self.email_edit)

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("+34 600 000 000")
        layout.addRow("Teléfono:", self.phone_edit)

        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("Dirección completa")
        layout.addRow("Dirección:", self.address_edit)

        self.city_edit = QLineEdit()
        self.city_edit.setPlaceholderText("Ciudad")
        layout.addRow("Ciudad:", self.city_edit)

        self.postal_code_edit = QLineEdit()
        self.postal_code_edit.setPlaceholderText("Código Postal")
        layout.addRow("C. Postal:", self.postal_code_edit)

        self.nif_edit = QLineEdit()
        self.nif_edit.setPlaceholderText("CIF/NIF")
        layout.addRow("CIF/NIF:", self.nif_edit)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Notas adicionales...")
        self.notes_edit.setMaximumHeight(80)
        layout.addRow("Notas:", self.notes_edit)

        self.active_check = QCheckBox()
        self.active_check.setChecked(True)
        layout.addRow("Activo:", self.active_check)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Guardar Cliente")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(UIStyles.get_primary_button_style())
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)
        
        layout.addRow(btn_layout)

    def load_client_data(self):
        """Load existing client data for editing - supports local and remote"""
        app_mode = get_app_mode()
        try:
            if app_mode.is_remote:
                client = app_mode.api.get_client(str(self.client_id))
                self.code_edit.setText(client.get("code", ""))
                self.name_edit.setText(client.get("name", ""))
                self.email_edit.setText(client.get("email", "") or "")
                self.phone_edit.setText(client.get("phone", "") or "")
                self.address_edit.setText(client.get("address", "") or "")
                self.city_edit.setText(client.get("city", "") or "")
                self.postal_code_edit.setText(client.get("postal_code", "") or "")
                self.nif_edit.setText(client.get("tax_id", "") or "")
                self.notes_edit.setPlainText(client.get("notes", "") or "")
                self.active_check.setChecked(client.get("is_active", True))
            else:
                with SessionLocal() as db:
                    client = db.query(Client).filter(Client.id == self.client_id).first()
                    if client:
                        self.code_edit.setText(client.code or "")
                        self.name_edit.setText(client.name or "")
                        self.email_edit.setText(client.email or "")
                        self.phone_edit.setText(client.phone or "")
                        self.address_edit.setText(client.address or "")
                        self.city_edit.setText(client.city or "")
                        self.postal_code_edit.setText(client.postal_code or "")
                        self.nif_edit.setText(client.tax_id or "")
                        self.notes_edit.setPlainText(client.notes or "")
                        self.active_check.setChecked(client.is_active)
                    else:
                        QMessageBox.warning(self, "Error", "Cliente no encontrado")
                        self.reject()
        except Exception as e:
            logger.error(f"Error loading client data: {e}")
            QMessageBox.critical(self, "Error", f"Error cargando cliente: {str(e)}")
            self.reject()

    def accept(self):
        """Save or update client - supports local and remote"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Error", "El nombre es obligatorio")
            return

        app_mode = get_app_mode()
        client_data = {
            "name": self.name_edit.text().strip(),
            "email": self.email_edit.text().strip() or None,
            "phone": self.phone_edit.text().strip() or None,
            "address": self.address_edit.text().strip() or None,
            "city": self.city_edit.text().strip() or None,
            "postal_code": self.postal_code_edit.text().strip() or None,
            "tax_id": self.nif_edit.text().strip() or None,
            "notes": self.notes_edit.toPlainText().strip() or None,
            "is_active": self.active_check.isChecked()
        }

        try:
            if app_mode.is_remote:
                if self.is_edit_mode:
                    app_mode.api.update_client(str(self.client_id), **client_data)
                else:
                    code = self.code_edit.text().strip() or f"C-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    app_mode.api.create_client(code=code, **client_data)
                super().accept()
            else:
                with SessionLocal() as db:
                    if self.is_edit_mode:
                        client = db.query(Client).filter(Client.id == self.client_id).first()
                        if not client:
                            QMessageBox.warning(self, "Error", "Cliente no encontrado")
                            return
                        for key, value in client_data.items():
                            setattr(client, key, value)
                    else:
                        code = self.code_edit.text().strip() or f"C-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        client = Client(code=code, **client_data)
                        db.add(client)
                    db.commit()
                    super().accept()
        except Exception as e:
            logger.error(f"Error saving client: {e}")
            error_msg = str(e)
            if hasattr(e, 'detail') and e.detail:
                error_msg = e.detail
            QMessageBox.critical(self, "Error", f"Error al guardar: {error_msg}")

class ProductDialog(QDialog):
    """Dialog for creating and editing products"""
    def __init__(self, parent=None, product_id=None):
        super().__init__(parent)
        self.product_id = product_id
        self.is_edit_mode = product_id is not None
        self.setWindowTitle("✏️ Editar Producto" if self.is_edit_mode else "📦 Nuevo Producto")
        self.setModal(True)
        # Increased size to prevent cut-off elements
        self.resize(550, 700)
        self.setup_ui()
        if self.is_edit_mode:
            self.load_product_data()

    def setup_ui(self):
        layout = QFormLayout(self)

        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("P-001")
        if self.is_edit_mode:
            self.code_edit.setReadOnly(True)
            self.code_edit.setStyleSheet("background-color: #f0f0f0;")
        layout.addRow("Código:", self.code_edit)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nombre del producto")
        layout.addRow("Nombre (*):", self.name_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Descripción del producto")
        self.description_edit.setMaximumHeight(60)
        layout.addRow("Descripción:", self.description_edit)

        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("Categoría")
        layout.addRow("Categoría:", self.category_edit)

        self.cost_price_edit = QDoubleSpinBox()
        self.cost_price_edit.setRange(0, 999999)
        self.cost_price_edit.setDecimals(2)
        self.cost_price_edit.setSuffix(" €")
        self.cost_price_edit.setValue(0)
        layout.addRow("Precio Coste:", self.cost_price_edit)

        self.sale_price_edit = QDoubleSpinBox()
        self.sale_price_edit.setRange(0, 999999)
        self.sale_price_edit.setDecimals(2)
        self.sale_price_edit.setSuffix(" €")
        self.sale_price_edit.setValue(0)
        layout.addRow("Precio Venta:", self.sale_price_edit)

        self.stock_spin = QSpinBox()
        self.stock_spin.setMinimum(0)
        self.stock_spin.setMaximum(999999)
        self.stock_spin.setValue(0)
        stock_label = "Stock Actual:" if self.is_edit_mode else "Stock Inicial:"
        layout.addRow(stock_label, self.stock_spin)

        self.min_stock_spin = QSpinBox()
        self.min_stock_spin.setMinimum(0)
        self.min_stock_spin.setMaximum(999999)
        self.min_stock_spin.setValue(5)
        layout.addRow("Stock Mínimo:", self.min_stock_spin)

        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["Unidades", "Kg", "Litros", "Metros", "Horas", "Piezas", "Cajas"])
        layout.addRow("Unidad:", self.unit_combo)

        self.active_check = QCheckBox()
        self.active_check.setChecked(True)
        layout.addRow("Activo:", self.active_check)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Guardar Producto")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(UIStyles.get_primary_button_style())
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)
        
        layout.addRow(btn_layout)

    def load_product_data(self):
        """Load existing product data for editing"""
        try:
            app_mode = get_app_mode()
            if app_mode.is_remote:
                product = app_mode.api.get_product(str(self.product_id))
                self.code_edit.setText(product.get("code", ""))
                self.name_edit.setText(product.get("name", ""))
                self.description_edit.setPlainText(product.get("description", "") or "")
                self.category_edit.setText(product.get("category", "") or "")
                self.cost_price_edit.setValue(float(product.get("purchase_price", 0) or 0))
                self.sale_price_edit.setValue(float(product.get("sale_price", 0) or 0))
                self.stock_spin.setValue(int(product.get("current_stock", 0) or 0))
                self.min_stock_spin.setValue(int(product.get("minimum_stock", 0) or 0))

                unit_value = product.get("stock_unit", "Unidades") or "Unidades"
                for i in range(self.unit_combo.count()):
                    if self.unit_combo.itemText(i).lower() == str(unit_value).lower():
                        self.unit_combo.setCurrentIndex(i)
                        break
                self.active_check.setChecked(product.get("is_active", True))
            else:
                with SessionLocal() as db:
                    product = db.query(Product).filter(Product.id == self.product_id).first()
                    if product:
                        self.code_edit.setText(product.code or "")
                        self.name_edit.setText(product.name or "")
                        self.description_edit.setPlainText(product.description or "")
                        self.category_edit.setText(product.category or "")
                        self.cost_price_edit.setValue(float(product.purchase_price or 0))
                        self.sale_price_edit.setValue(float(product.sale_price or 0))
                        self.stock_spin.setValue(product.current_stock or 0)
                        self.min_stock_spin.setValue(product.minimum_stock or 0)
                        # Set unit combo
                        unit_index = self.unit_combo.findText(product.stock_unit or "Unidades")
                        if unit_index >= 0:
                            self.unit_combo.setCurrentIndex(unit_index)
                        self.active_check.setChecked(product.is_active)
                    else:
                        QMessageBox.warning(self, "❌ Error", "Producto no encontrado")
                        self.reject()
        except Exception as e:
            logger.error(f"Error loading product data: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error cargando producto: {str(e)}")
            self.reject()

    def accept(self):
        """Save or update product"""
        # Validation
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Error", "El nombre es obligatorio")
            return

        app_mode = get_app_mode()
        product_payload = {
            "name": self.name_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip() or None,
            "category": self.category_edit.text().strip() or None,
            "purchase_price": self.cost_price_edit.value(),
            "sale_price": self.sale_price_edit.value(),
            "current_stock": self.stock_spin.value(),
            "minimum_stock": self.min_stock_spin.value(),
            "stock_unit": self.unit_combo.currentText(),
        }

        if app_mode.is_remote:
            try:
                if self.is_edit_mode:
                    app_mode.api.update_product(str(self.product_id), **product_payload)
                else:
                    product_code = self.code_edit.text().strip()
                    if not product_code:
                        from datetime import datetime
                        product_code = f"P-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:17]}"
                    app_mode.api.create_product(code=product_code, **product_payload)
                super().accept()
            except Exception as e:
                logger.error(f"Error saving product (remote): {e}")
                error_msg = str(e)
                if hasattr(e, 'detail') and e.detail:
                    error_msg = e.detail
                QMessageBox.critical(self, "Error", f"Error al guardar producto: {error_msg}")
            return

        try:
            with SessionLocal() as db:
                if self.is_edit_mode:
                    # Update existing product
                    product = db.query(Product).filter(Product.id == self.product_id).first()
                    if not product:
                        QMessageBox.warning(self, "Error", "Producto no encontrado")
                        return

                    product.name = product_payload["name"]
                    product.description = product_payload["description"]
                    product.category = product_payload["category"]
                    product.purchase_price = product_payload["purchase_price"]
                    product.sale_price = product_payload["sale_price"]
                    product.current_stock = product_payload["current_stock"]
                    product.minimum_stock = product_payload["minimum_stock"]
                    product.stock_unit = product_payload["stock_unit"]
                    product.is_active = self.active_check.isChecked()
                else:
                    # Create new product
                    product_code = self.code_edit.text().strip()
                    if not product_code:
                        from datetime import datetime
                        product_code = f"P-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:17]}"

                    # Verify code doesn't exist
                    existing = db.query(Product).filter(Product.code == product_code).first()
                    if existing:
                        QMessageBox.warning(
                            self, "Error",
                            f"Ya existe un producto con el código '{product_code}'"
                        )
                        return

                    product = Product(
                        code=product_code,
                        name=product_payload["name"],
                        description=product_payload["description"],
                        category=product_payload["category"],
                        purchase_price=product_payload["purchase_price"],
                        sale_price=product_payload["sale_price"],
                        current_stock=product_payload["current_stock"],
                        minimum_stock=product_payload["minimum_stock"],
                        stock_unit=product_payload["stock_unit"],
                        is_active=self.active_check.isChecked()
                    )
                    db.add(product)
                    db.flush()  # Flush to catch any constraint violations before commit

                # Commit changes
                db.commit()
                logger.info(f"Product saved successfully: {product.code} - {product.name}")

            # Only close dialog after successful commit (outside the session context)
            super().accept()

        except Exception as e:
            logger.error(f"Error saving product: {e}")
            # Provide more specific error messages
            error_msg = str(e)
            if "UNIQUE constraint failed" in error_msg or "unique constraint" in error_msg.lower():
                QMessageBox.critical(
                    self, "Error",
                    "No se pudo guardar el producto. El código ya existe en el sistema."
                )
            else:
                QMessageBox.critical(self, "Error", f"Error al guardar producto: {error_msg}")
            # Don't close dialog on error
            return

class DocumentDialog(QDialog):
    """Document creation/editing dialog with client/product selection"""
    def __init__(self, parent=None, doc_type="quote", document_id=None):
        super().__init__(parent)
        self.doc_type = doc_type
        self.document_id = document_id
        self.is_edit_mode = document_id is not None
        if doc_type == "quote":
            self.doc_title = "Presupuesto"
        elif doc_type == "delivery":
            self.doc_title = "Albaran"
        else:
            self.doc_title = "Factura"
        title = f"Editar {self.doc_title}" if self.is_edit_mode else f"Nuevo {self.doc_title}"
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(1000, 750)
        self.setStyleSheet(UIStyles.get_dialog_style() + UIStyles.get_input_style())
        self.items = []
        self._remote_original_status = None
        self.setup_ui()
        if self.is_edit_mode:
            self.load_document_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Header
        header_label = QLabel(f"{'Editar' if self.is_edit_mode else 'Nuevo'} {self.doc_title}")
        header_label.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {UIStyles.COLORS['text_primary']};")
        layout.addWidget(header_label)

        # Main content in horizontal layout
        main_layout = QHBoxLayout()
        main_layout.setSpacing(16)

        # LEFT SIDE: Client and items
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        # Client selection
        client_layout = QHBoxLayout()
        client_label = QLabel("Cliente:")
        client_label.setStyleSheet(UIStyles.get_label_style())
        client_layout.addWidget(client_label)
        self.client_combo = QComboBox()
        self.client_combo.setMinimumWidth(300)
        self.setup_clients()
        client_layout.addWidget(self.client_combo)
        client_layout.addStretch()
        left_layout.addLayout(client_layout)

        # Product selection with quantity
        product_frame = QFrame()
        product_frame.setStyleSheet(f"QFrame {{ background-color: {UIStyles.COLORS['bg_hover']}; border-radius: 8px; padding: 8px; }}")
        product_inner = QHBoxLayout(product_frame)
        product_inner.setContentsMargins(12, 8, 12, 8)

        self.product_combo = QComboBox()
        self.product_combo.setMinimumWidth(250)
        self.setup_products()
        product_inner.addWidget(QLabel("Producto:"))
        product_inner.addWidget(self.product_combo)

        product_inner.addWidget(QLabel("Cantidad:"))
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 9999)
        self.quantity_spin.setValue(1)
        self.quantity_spin.setMinimumWidth(80)
        product_inner.addWidget(self.quantity_spin)

        add_btn = QPushButton("Agregar")
        add_btn.setStyleSheet(UIStyles.get_primary_button_style())
        add_btn.clicked.connect(self.add_item)
        product_inner.addWidget(add_btn)

        left_layout.addWidget(product_frame)

        # Items table
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels([
            "Producto", "Descripcion", "Cantidad", "Precio Unit.", "Dto %", "Total", "Acciones"
        ])
        self.items_table.setStyleSheet(UIStyles.get_table_style())
        self.items_table.setAlternatingRowColors(False)
        self.items_table.verticalHeader().setVisible(False)

        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.items_table.setColumnWidth(0, 150)
        self.items_table.setColumnWidth(2, 80)
        self.items_table.setColumnWidth(3, 100)
        self.items_table.setColumnWidth(4, 60)
        self.items_table.setColumnWidth(5, 100)
        self.items_table.setColumnWidth(6, 80)

        left_layout.addWidget(self.items_table)
        main_layout.addWidget(left_widget, 2)

        # RIGHT SIDE: Details, totals, notes
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        # Document details (for edit mode)
        if self.is_edit_mode:
            details_group = QGroupBox("Detalles")
            details_layout = QFormLayout(details_group)
            details_layout.setSpacing(8)

            self.status_combo = QComboBox()
            self.status_combo.addItems(STATUS_OPTIONS_ES)
            details_layout.addRow("Estado:", self.status_combo)

            self.due_date_edit = QDateEdit()
            self.due_date_edit.setCalendarPopup(True)
            self.due_date_edit.setDate(QDate.currentDate().addDays(30))
            details_layout.addRow("Vencimiento:", self.due_date_edit)

            right_layout.addWidget(details_group)

        # Totals
        totals_group = QGroupBox("Totales")
        totals_layout = QFormLayout(totals_group)
        totals_layout.setSpacing(8)

        self.subtotal_label = QLabel("0.00 EUR")
        self.subtotal_label.setStyleSheet("font-weight: 500;")
        totals_layout.addRow("Subtotal:", self.subtotal_label)

        self.tax_combo = QComboBox()
        self.tax_combo.addItems(["21% IVA", "10% IVA", "4% IVA", "Exento IVA"])
        self.tax_combo.currentTextChanged.connect(self.update_totals)
        totals_layout.addRow("IVA:", self.tax_combo)

        self.tax_amount_label = QLabel("0.00 EUR")
        totals_layout.addRow("Importe IVA:", self.tax_amount_label)

        self.total_label = QLabel("0.00 EUR")
        self.total_label.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {UIStyles.COLORS['accent']};")
        totals_layout.addRow("TOTAL:", self.total_label)

        right_layout.addWidget(totals_group)

        # Notes
        notes_group = QGroupBox("Notas")
        notes_layout = QVBoxLayout(notes_group)
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Notas adicionales...")
        self.notes_edit.setMaximumHeight(80)
        notes_layout.addWidget(self.notes_edit)

        # Internal notes (for edit mode)
        if self.is_edit_mode:
            self.internal_notes_edit = QTextEdit()
            self.internal_notes_edit.setPlaceholderText("Notas internas (no visibles en documento)...")
            self.internal_notes_edit.setMaximumHeight(60)
            notes_layout.addWidget(QLabel("Notas internas:"))
            notes_layout.addWidget(self.internal_notes_edit)

        right_layout.addWidget(notes_group)
        right_layout.addStretch()

        main_layout.addWidget(right_widget, 1)
        layout.addLayout(main_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton(f"Guardar {self.doc_title}")
        save_btn.setStyleSheet(UIStyles.get_primary_button_style())
        save_btn.clicked.connect(self.save_document)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)
        self.update_totals()
    
    def setup_clients(self):
        """Load clients into combo box - supports local and remote"""
        app_mode = get_app_mode()
        try:
            self.client_combo.addItem("Seleccione un cliente...", None)
            if app_mode.is_remote:
                response = app_mode.api.list_clients(limit=500, active_only=True)
                clients = response.get("items", [])
                for client in clients:
                    # Store ID as string for remote mode
                    self.client_combo.addItem(
                        f"{client.get('code', '')} - {client.get('name', '')}",
                        client.get('id', '')
                    )
            else:
                with SessionLocal() as db:
                    clients = db.query(Client).filter(Client.is_active == True).all()
                    for client in clients:
                        self.client_combo.addItem(f"{client.code} - {client.name}", client.id)
        except Exception as e:
            error_detail = str(e)
            if hasattr(e, 'detail'):
                error_detail = e.detail
            if hasattr(e, 'status_code'):
                error_detail = f"[{e.status_code}] {error_detail}"
            logger.error(f"Error loading clients into combo: {error_detail}")
            self.client_combo.addItem(f"Error: {error_detail[:50]}", None)

    def setup_products(self):
        """Load products into combo box - supports local and remote"""
        app_mode = get_app_mode()
        try:
            self.product_combo.addItem("Seleccione un producto...", None)
            if app_mode.is_remote:
                response = app_mode.api.list_products(limit=500)
                products = response.get("items", [])
                for product in products:
                    self.product_combo.addItem(
                        f"{product.get('code', '')} - {product.get('name', '')}",
                        product.get('id', '')
                    )
            else:
                with SessionLocal() as db:
                    products = db.query(Product).filter(Product.is_active == True).all()
                    for product in products:
                        self.product_combo.addItem(f"{product.code} - {product.name}", product.id)
        except Exception as e:
            error_detail = str(e)
            if hasattr(e, 'detail'):
                error_detail = e.detail
            if hasattr(e, 'status_code'):
                error_detail = f"[{e.status_code}] {error_detail}"
            logger.error(f"Error loading products into combo: {error_detail}")
            self.product_combo.addItem(f"Error: {error_detail[:50]}", None)
    
    def add_item(self):
        """Add selected product to table with quantity - supports local and remote"""
        product_id = self.product_combo.currentData()
        if not product_id:
            QMessageBox.warning(self, "Error", "Seleccione un producto primero")
            return

        quantity = self.quantity_spin.value()
        app_mode = get_app_mode()

        try:
            # Get product data based on mode
            if app_mode.is_remote:
                product_data = app_mode.api.get_product(str(product_id))
                product_name = product_data.get('name', '')
                product_desc = product_data.get('description', '') or ''
                price = float(product_data.get('sale_price', 0) or 0)
                stored_id = str(product_id)  # Keep as string for remote
            else:
                with SessionLocal() as db:
                    product = db.query(Product).filter(Product.id == product_id).first()
                    if not product:
                        QMessageBox.warning(self, "Error", "Producto no encontrado")
                        return
                    product_name = product.name
                    product_desc = product.description or ''
                    price = float(product.sale_price or 0)
                    stored_id = product.id  # UUID object for local

            row = self.items_table.rowCount()
            self.items_table.insertRow(row)
            total_line = price * quantity

            self.items_table.setItem(row, 0, QTableWidgetItem(product_name))
            self.items_table.setItem(row, 1, QTableWidgetItem(product_desc))

            # Quantity with spinbox
            qty_spin = QSpinBox()
            qty_spin.setRange(1, 9999)
            qty_spin.setValue(quantity)
            qty_spin.valueChanged.connect(lambda v, r=row: self._update_line_total(r))
            self.items_table.setCellWidget(row, 2, qty_spin)

            self.items_table.setItem(row, 3, QTableWidgetItem(f"{price:.2f}"))

            # Discount spinbox
            disc_spin = QSpinBox()
            disc_spin.setRange(0, 100)
            disc_spin.setValue(0)
            disc_spin.setSuffix("%")
            disc_spin.valueChanged.connect(lambda v, r=row: self._update_line_total(r))
            self.items_table.setCellWidget(row, 4, disc_spin)

            self.items_table.setItem(row, 5, QTableWidgetItem(f"{total_line:.2f}"))

            # Delete button
            del_btn = QPushButton("X")
            del_btn.setStyleSheet(f"background-color: {UIStyles.COLORS['danger']}; color: white; border: none; border-radius: 4px; padding: 4px 8px;")
            del_btn.clicked.connect(lambda checked, r=row: self._remove_row(r))
            self.items_table.setCellWidget(row, 6, del_btn)

            self.items.append({
                'product_id': stored_id,
                'quantity': quantity,
                'price': price,
                'discount': 0
            })

            # Reset quantity spinner
            self.quantity_spin.setValue(1)
            self.update_totals()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error añadiendo producto: {str(e)}")

    def _update_line_total(self, row):
        """Update line total when quantity or discount changes"""
        try:
            qty_widget = self.items_table.cellWidget(row, 2)
            disc_widget = self.items_table.cellWidget(row, 4)
            price_item = self.items_table.item(row, 3)

            if qty_widget and disc_widget and price_item:
                quantity = qty_widget.value()
                discount = disc_widget.value()
                price = float(price_item.text().replace('€', '').replace('EUR', '').strip())

                subtotal = price * quantity
                discount_amount = subtotal * (discount / 100)
                total = subtotal - discount_amount

                self.items_table.setItem(row, 5, QTableWidgetItem(f"{total:.2f}"))

                # Update items list
                if row < len(self.items):
                    self.items[row]['quantity'] = quantity
                    self.items[row]['discount'] = discount

                self.update_totals()
        except Exception as e:
            logger.warning(f"Error updating line total: {e}")

    def _remove_row(self, row):
        """Remove a specific row from table"""
        # Find actual row (may have shifted)
        for i in range(self.items_table.rowCount()):
            btn = self.items_table.cellWidget(i, 6)
            if btn and btn == self.sender():
                self.items_table.removeRow(i)
                if i < len(self.items):
                    self.items.pop(i)
                self.update_totals()
                return
        # Fallback
        if row < self.items_table.rowCount():
            self.items_table.removeRow(row)
            if row < len(self.items):
                self.items.pop(row)
            self.update_totals()

    def remove_item(self):
        """Remove selected row from table"""
        current_row = self.items_table.currentRow()
        if current_row >= 0:
            self.items_table.removeRow(current_row)
            if current_row < len(self.items):
                self.items.pop(current_row)
            self.update_totals()

    def update_totals(self):
        """Calculate and update totals"""
        subtotal = 0.0

        for row in range(self.items_table.rowCount()):
            total_item = self.items_table.item(row, 5)
            if total_item:
                try:
                    subtotal += float(total_item.text().replace('€', '').replace('EUR', '').strip())
                except ValueError as e:
                    logger.warning(f"Could not parse subtotal value at row {row}: {e}")

        tax_text = self.tax_combo.currentText()
        tax_rate = 0.21
        if "21%" in tax_text:
            tax_rate = 0.21
        elif "10%" in tax_text:
            tax_rate = 0.10
        elif "4%" in tax_text:
            tax_rate = 0.04
        elif "Exento" in tax_text:
            tax_rate = 0.0

        tax_amount = subtotal * tax_rate
        total = subtotal + tax_amount

        self.subtotal_label.setText(f"{subtotal:.2f} EUR")
        if hasattr(self, 'tax_amount_label'):
            self.tax_amount_label.setText(f"{tax_amount:.2f} EUR")
        self.total_label.setText(f"{total:.2f} EUR")

    def load_document_data(self):
        """Load existing document data for editing"""
        if not self.document_id:
            return
        try:
            app_mode = get_app_mode()
            if app_mode.is_remote:
                doc = app_mode.api.get_document(str(self.document_id))
                self._remote_original_status = doc.get("status", "draft")

                # Set client
                client_id = str(doc.get("client_id", ""))
                for i in range(self.client_combo.count()):
                    if str(self.client_combo.itemData(i)) == client_id:
                        self.client_combo.setCurrentIndex(i)
                        break

                # Set status if in edit mode
                if hasattr(self, 'status_combo'):
                    status_label = get_status_label(self._remote_original_status)
                    idx = self.status_combo.findText(status_label)
                    if idx >= 0:
                        self.status_combo.setCurrentIndex(idx)

                # Set due date
                if hasattr(self, 'due_date_edit'):
                    due_date = doc.get("due_date")
                    if due_date:
                        try:
                            if isinstance(due_date, str):
                                due_date = due_date.replace("Z", "+00:00")
                                due_dt = datetime.fromisoformat(due_date)
                            else:
                                due_dt = due_date
                            self.due_date_edit.setDate(QDate(due_dt.year, due_dt.month, due_dt.day))
                        except Exception:
                            pass

                # Set notes
                if doc.get("notes"):
                    self.notes_edit.setPlainText(doc.get("notes") or "")
                if hasattr(self, 'internal_notes_edit') and doc.get("internal_notes"):
                    self.internal_notes_edit.setPlainText(doc.get("internal_notes") or "")

                # Load line items
                for line in doc.get("lines", []):
                    self._add_line_from_api(line)

                self.update_totals()
                return

            # Convert string ID to UUID if needed
            doc_id = self.document_id
            if isinstance(doc_id, str):
                doc_id = uuid.UUID(doc_id)

            with SessionLocal() as db:
                doc = db.query(Document).options(
                    joinedload(Document.lines),
                    joinedload(Document.client)
                ).filter(Document.id == doc_id).first()

                if doc:
                    # Set client
                    for i in range(self.client_combo.count()):
                        if self.client_combo.itemData(i) == doc.client_id:
                            self.client_combo.setCurrentIndex(i)
                            break

                    # Set status if in edit mode
                    if hasattr(self, 'status_combo'):
                        status_label = get_status_label(doc.status)
                        idx = self.status_combo.findText(status_label)
                        if idx >= 0:
                            self.status_combo.setCurrentIndex(idx)

                    # Set due date
                    if hasattr(self, 'due_date_edit') and doc.due_date:
                        self.due_date_edit.setDate(QDate(doc.due_date.year, doc.due_date.month, doc.due_date.day))

                    # Set notes
                    if doc.notes:
                        self.notes_edit.setPlainText(doc.notes)
                    if hasattr(self, 'internal_notes_edit') and doc.internal_notes:
                        self.internal_notes_edit.setPlainText(doc.internal_notes)

                    # Load line items
                    for line in doc.lines:
                        self._add_line_to_table(line, db)

                    self.update_totals()
        except Exception as e:
            logger.error(f"Error loading document: {e}")
            QMessageBox.warning(self, "Error", f"Error cargando documento: {str(e)}")

    def _add_line_to_table(self, line, db):
        """Add a document line to the table"""
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)

        # Get product name if exists
        product_name = line.description or "Producto"
        if line.product_id:
            product = db.query(Product).filter(Product.id == line.product_id).first()
            if product:
                product_name = product.name

        quantity = int(line.quantity or 1)
        price = float(line.unit_price or 0)
        discount = float(line.discount_percent or 0)
        total_line = float(line.subtotal or (price * quantity))

        self.items_table.setItem(row, 0, QTableWidgetItem(product_name))
        self.items_table.setItem(row, 1, QTableWidgetItem(line.description or ""))

        # Quantity spinbox
        qty_spin = QSpinBox()
        qty_spin.setRange(1, 9999)
        qty_spin.setValue(quantity)
        qty_spin.valueChanged.connect(lambda v, r=row: self._update_line_total(r))
        self.items_table.setCellWidget(row, 2, qty_spin)

        self.items_table.setItem(row, 3, QTableWidgetItem(f"{price:.2f}"))

        # Discount spinbox
        disc_spin = QSpinBox()
        disc_spin.setRange(0, 100)
        disc_spin.setValue(int(discount))
        disc_spin.setSuffix("%")
        disc_spin.valueChanged.connect(lambda v, r=row: self._update_line_total(r))
        self.items_table.setCellWidget(row, 4, disc_spin)

        self.items_table.setItem(row, 5, QTableWidgetItem(f"{total_line:.2f}"))

        # Delete button
        del_btn = QPushButton("X")
        del_btn.setStyleSheet(f"background-color: {UIStyles.COLORS['danger']}; color: white; border: none; border-radius: 4px; padding: 4px 8px;")
        del_btn.clicked.connect(lambda checked, r=row: self._remove_row(r))
        self.items_table.setCellWidget(row, 6, del_btn)

        self.items.append({
            'product_id': line.product_id,
            'quantity': quantity,
            'price': price,
            'discount': discount,
            'line_id': line.id
        })

    def _add_line_from_api(self, line):
        """Add a document line from API data to the table"""
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)

        description = line.get("description", "") or ""
        product_name = description or "Producto"
        quantity = int(line.get("quantity", 1) or 1)
        price = float(line.get("unit_price", 0) or 0)
        discount = float(line.get("discount_percent", 0) or 0)
        subtotal = float(line.get("subtotal", price * quantity) or 0)

        self.items_table.setItem(row, 0, QTableWidgetItem(product_name))
        self.items_table.setItem(row, 1, QTableWidgetItem(description))

        qty_spin = QSpinBox()
        qty_spin.setRange(1, 9999)
        qty_spin.setValue(quantity)
        qty_spin.valueChanged.connect(lambda v, r=row: self._update_line_total(r))
        self.items_table.setCellWidget(row, 2, qty_spin)

        self.items_table.setItem(row, 3, QTableWidgetItem(f"{price:.2f}"))

        disc_spin = QSpinBox()
        disc_spin.setRange(0, 100)
        disc_spin.setValue(int(discount))
        disc_spin.setSuffix("%")
        disc_spin.valueChanged.connect(lambda v, r=row: self._update_line_total(r))
        self.items_table.setCellWidget(row, 4, disc_spin)

        self.items_table.setItem(row, 5, QTableWidgetItem(f"{subtotal:.2f}"))

        del_btn = QPushButton("X")
        del_btn.setStyleSheet(
            f"background-color: {UIStyles.COLORS['danger']}; color: white; border: none; border-radius: 4px; padding: 4px 8px;"
        )
        del_btn.clicked.connect(lambda checked, r=row: self._remove_row(r))
        self.items_table.setCellWidget(row, 6, del_btn)

        self.items.append({
            'product_id': line.get("product_id"),
            'quantity': quantity,
            'price': price,
            'discount': discount,
            'line_id': line.get("id")
        })
    
    def _get_current_user_id(self):
        """Get current user ID from MainWindow"""
        widget = self.parent()
        while widget is not None:
            if hasattr(widget, 'current_user') and widget.current_user:
                return widget.current_user.id
            widget = widget.parent()
        return None

    def _build_remote_lines(self):
        """Build line payloads for remote API."""
        lines = []
        for row in range(self.items_table.rowCount()):
            product_name = self.items_table.item(row, 0).text() if self.items_table.item(row, 0) else ""
            description = self.items_table.item(row, 1).text() if self.items_table.item(row, 1) else ""

            qty_widget = self.items_table.cellWidget(row, 2)
            quantity = float(qty_widget.value()) if qty_widget else 1.0

            price_item = self.items_table.item(row, 3)
            unit_price = float(price_item.text().replace('EUR', '').replace('€', '').strip()) if price_item else 0.0

            disc_widget = self.items_table.cellWidget(row, 4)
            discount = float(disc_widget.value()) if disc_widget else 0.0

            product_id = None
            if row < len(self.items) and self.items[row].get('product_id'):
                product_id = str(self.items[row]['product_id'])

            line = {
                "line_type": "product",
                "product_id": product_id,
                "description": description or product_name,
                "quantity": quantity,
                "unit_price": unit_price,
                "discount_percent": discount,
            }
            lines.append(line)
        return lines

    def _save_document_remote(self, api):
        """Save document using remote API."""
        client_id = self.client_combo.currentData()
        if not client_id:
            QMessageBox.warning(self, "Error", "Seleccione un cliente")
            return

        if self.items_table.rowCount() == 0:
            QMessageBox.warning(self, "Error", "Añada al menos un producto")
            return

        client_id = str(client_id)
        lines = self._build_remote_lines()

        notes = self.notes_edit.toPlainText().strip() or None
        internal_notes = self.internal_notes_edit.toPlainText().strip() if hasattr(self, 'internal_notes_edit') else None
        terms = None

        due_date = None
        if hasattr(self, 'due_date_edit'):
            qdate = self.due_date_edit.date()
            due_date = datetime(qdate.year(), qdate.month(), qdate.day()).isoformat()

        if self.is_edit_mode:
            doc_id = str(self.document_id)
            original_status = self._remote_original_status or "draft"

            try:
                if original_status == "draft":
                    api.update_document(
                        doc_id,
                        client_id=client_id,
                        due_date=due_date,
                        notes=notes,
                        internal_notes=internal_notes,
                        terms=terms,
                        lines=lines
                    )
                # Change status if requested
                if hasattr(self, 'status_combo'):
                    new_status = get_status_value(self.status_combo.currentText())
                    if new_status and new_status != original_status:
                        api.change_document_status(doc_id, new_status)

                QMessageBox.information(self, "Éxito", f"{self.doc_title} actualizado correctamente")
                self.accept()
            except Exception as e:
                logger.error(f"Error saving document (remote): {e}")
                error_msg = str(e)
                if hasattr(e, 'detail') and e.detail:
                    error_msg = e.detail
                QMessageBox.critical(self, "Error", f"Error guardando {self.doc_title.lower()}: {error_msg}")
            return

        # Create new document (remote)
        if self.doc_type == "quote":
            doc_type = "quote"
        elif self.doc_type == "delivery":
            doc_type = "delivery_note"
        else:
            doc_type = "invoice"

        issue_date = datetime.now().isoformat()

        try:
            api.create_document(
                doc_type=doc_type,
                client_id=client_id,
                issue_date=issue_date,
                lines=lines,
                due_date=due_date,
                notes=notes,
                internal_notes=internal_notes,
                terms=terms
            )
            QMessageBox.information(self, "Éxito", f"{self.doc_title} guardado correctamente")
            self.accept()
        except Exception as e:
            logger.error(f"Error creating document (remote): {e}")
            error_msg = str(e)
            if hasattr(e, 'detail') and e.detail:
                error_msg = e.detail
            QMessageBox.critical(self, "Error", f"Error guardando {self.doc_title.lower()}: {error_msg}")

    def save_document(self):
        """Save or update document with line items"""
        client_id = self.client_combo.currentData()
        if not client_id:
            QMessageBox.warning(self, "Error", "Seleccione un cliente")
            return

        if self.items_table.rowCount() == 0:
            QMessageBox.warning(self, "Error", "Añada al menos un producto")
            return

        app_mode = get_app_mode()
        if app_mode.is_remote:
            self._save_document_remote(app_mode.api)
            return

        # Get current user ID (local mode)
        user_id = self._get_current_user_id()
        if not user_id and not self.is_edit_mode:
            QMessageBox.warning(self, "Error", "No hay usuario autenticado")
            return

        try:
            with SessionLocal() as db:
                # Calculate totals
                total_text = self.total_label.text()
                total = float(total_text.replace('EUR', '').replace('€', '').strip())

                if self.is_edit_mode:
                    # Update existing document - convert string ID to UUID
                    doc_id = self.document_id
                    if isinstance(doc_id, str):
                        doc_id = uuid.UUID(doc_id)
                    document = db.query(Document).options(joinedload(Document.lines)).filter(Document.id == doc_id).first()
                    if not document:
                        QMessageBox.warning(self, "Error", "Documento no encontrado")
                        return

                    # Store original status for stock deduction check
                    original_status = document.status

                    document.client_id = client_id
                    document.total = total
                    document.notes = self.notes_edit.toPlainText().strip() or None

                    new_status = original_status
                    if hasattr(self, 'status_combo'):
                        status_value = get_status_value(self.status_combo.currentText())
                        new_status = DocumentStatus(status_value)
                        document.status = new_status

                    if hasattr(self, 'due_date_edit'):
                        qdate = self.due_date_edit.date()
                        document.due_date = date(qdate.year(), qdate.month(), qdate.day())

                    if hasattr(self, 'internal_notes_edit'):
                        document.internal_notes = self.internal_notes_edit.toPlainText().strip() or None

                    # Check if status changed to PAID - deduct stock from products
                    stock_deducted = []
                    if new_status == DocumentStatus.PAID and original_status != DocumentStatus.PAID:
                        # Use the items from the table (not document.lines since we're about to delete them)
                        for row in range(self.items_table.rowCount()):
                            if row < len(self.items) and self.items[row].get('product_id'):
                                product_id = self.items[row]['product_id']
                                qty_widget = self.items_table.cellWidget(row, 2)
                                quantity = qty_widget.value() if qty_widget else 1

                                product = db.query(Product).filter(Product.id == product_id).first()
                                if product:
                                    old_stock = product.current_stock or 0
                                    new_stock = max(0, old_stock - quantity)
                                    product.current_stock = new_stock
                                    stock_deducted.append(f"{product.name}: -{quantity} (Stock: {old_stock} → {new_stock})")

                    # Delete old lines and add new ones
                    db.query(DocumentLine).filter(DocumentLine.document_id == document.id).delete()

                    # Add updated lines
                    self._save_document_lines(db, document.id)

                    db.commit()

                    # Show success message with stock info if deducted
                    if stock_deducted:
                        QMessageBox.information(self, "Exito",
                            f"{self.doc_title} actualizado correctamente\n\nStock descontado:\n" + "\n".join(stock_deducted))
                    else:
                        QMessageBox.information(self, "Exito", f"{self.doc_title} actualizado correctamente")
                else:
                    # Create new document
                    if self.doc_type == "quote":
                        doc_type = DocumentType.QUOTE
                        code_prefix = "PRE"
                    elif self.doc_type == "delivery":
                        doc_type = DocumentType.DELIVERY_NOTE
                        code_prefix = "ALB"
                    else:
                        doc_type = DocumentType.INVOICE
                        code_prefix = "FAC"
                    doc_code = f"{code_prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

                    document = Document(
                        code=doc_code,
                        type=doc_type,
                        client_id=client_id,
                        issue_date=date.today(),
                        total=total,
                        status=DocumentStatus.DRAFT,
                        notes=self.notes_edit.toPlainText().strip() or None,
                        created_by=user_id
                    )

                    db.add(document)
                    db.flush()  # Get the ID

                    # Save line items
                    self._save_document_lines(db, document.id)

                    db.commit()
                    QMessageBox.information(self, "Exito", f"{self.doc_title} guardado correctamente\nCodigo: {doc_code}")

                self.accept()

        except Exception as e:
            logger.error(f"Error saving document: {e}")
            QMessageBox.critical(self, "Error", f"Error guardando {self.doc_title.lower()}: {str(e)}")

    def _save_document_lines(self, db, document_id):
        """Save document line items"""
        for row in range(self.items_table.rowCount()):
            product_name = self.items_table.item(row, 0).text() if self.items_table.item(row, 0) else ""
            description = self.items_table.item(row, 1).text() if self.items_table.item(row, 1) else ""

            qty_widget = self.items_table.cellWidget(row, 2)
            quantity = qty_widget.value() if qty_widget else 1

            price_item = self.items_table.item(row, 3)
            unit_price = float(price_item.text().replace('EUR', '').replace('€', '').strip()) if price_item else 0

            disc_widget = self.items_table.cellWidget(row, 4)
            discount = disc_widget.value() if disc_widget else 0

            total_item = self.items_table.item(row, 5)
            subtotal = float(total_item.text().replace('EUR', '').replace('€', '').strip()) if total_item else 0

            # Get product_id from items list if available
            product_id = None
            if row < len(self.items) and self.items[row].get('product_id'):
                product_id = self.items[row]['product_id']

            line = DocumentLine(
                document_id=document_id,
                product_id=product_id,
                description=description or product_name,
                quantity=quantity,
                unit_price=unit_price,
                discount_percent=discount,
                subtotal=subtotal,
                order_index=row
            )
            db.add(line)

# Continue with other classes...
class ClientManagementTab(QWidget):
    """Modern client management tab with Apple-inspired design"""

    def __init__(self):
        super().__init__()
        self.translatable_widgets = {}
        self._inventory_products = []
        self.setup_ui()
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self.refresh_data)

    def setup_ui(self):
        # Apply panel style
        self.setStyleSheet(UIStyles.get_panel_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header with title
        header_layout = QHBoxLayout()
        self.title_label = QLabel(translator.t("clients.title"))
        self.title_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 600;
            color: {UIStyles.COLORS['text_primary']};
            background: transparent;
        """)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(12)

        self.add_btn = QPushButton(translator.t("buttons.new_client"))
        self.add_btn.clicked.connect(self.add_client)
        self.add_btn.setStyleSheet(UIStyles.get_primary_button_style())
        toolbar_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton(translator.t("buttons.edit"))
        self.edit_btn.clicked.connect(self.edit_client)
        self.edit_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        toolbar_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton(translator.t("buttons.delete"))
        self.delete_btn.clicked.connect(self.delete_client)
        self.delete_btn.setStyleSheet(UIStyles.get_danger_button_style())
        toolbar_layout.addWidget(self.delete_btn)

        toolbar_layout.addStretch()

        self.refresh_btn = QPushButton(translator.t("buttons.refresh"))
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.refresh_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        toolbar_layout.addWidget(self.refresh_btn)

        layout.addLayout(toolbar_layout)

        # Search
        search_layout = QHBoxLayout()
        search_layout.setSpacing(12)

        self.search_label = QLabel(translator.t("buttons.search") + ":")
        self.search_label.setStyleSheet(UIStyles.get_label_style())
        search_layout.addWidget(self.search_label)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(translator.t("clients.search_placeholder"))
        self.search_edit.setStyleSheet(UIStyles.get_input_style())
        self.search_edit.textChanged.connect(self.filter_clients)
        search_layout.addWidget(self.search_edit)

        layout.addLayout(search_layout)

        # Table
        self.clients_table = QTableWidget()
        self.clients_table.setColumnCount(7)
        self.clients_table.setHorizontalHeaderLabels([
            translator.t("clients.code"), translator.t("clients.name"), translator.t("clients.email"),
            translator.t("clients.phone"), translator.t("clients.address"), translator.t("clients.tax_id"), translator.t("clients.active")
        ])
        self.clients_table.setStyleSheet(UIStyles.get_table_style())
        self.clients_table.setAlternatingRowColors(False)
        self.clients_table.setShowGrid(False)
        self.clients_table.verticalHeader().setVisible(False)
        self.clients_table.setSortingEnabled(True)

        header = self.clients_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.clients_table)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(UIStyles.get_status_label_style())
        layout.addWidget(self.status_label)
    
    def refresh_data(self):
        """Refresh clients data - supports local and remote modes"""
        self.client_ids = []
        app_mode = get_app_mode()

        try:
            if app_mode.is_remote:
                self._refresh_from_api(app_mode.api)
            else:
                self._refresh_from_local()
        except Exception as e:
            logger.error(f"Error refreshing clients: {e}")
            self.status_label.setText(f"Error: {str(e)}")

    def _refresh_from_api(self, api):
        """Refresh clients from remote API (with cache fallback)."""
        try:
            response = api.list_clients(limit=500, active_only=False)
            clients = response.get("items", [])
            from_cache = response.get("_from_cache", False)

            self.clients_table.setSortingEnabled(False)
            self.clients_table.setRowCount(0)
            self.client_ids = []

            for row, client in enumerate(clients):
                self.clients_table.insertRow(row)
                self.client_ids.append(client.get("id", ""))

                self.clients_table.setItem(row, 0, QTableWidgetItem(client.get("code", "")))
                self.clients_table.setItem(row, 1, QTableWidgetItem(client.get("name", "")))
                self.clients_table.setItem(row, 2, QTableWidgetItem(client.get("email", "") or ""))
                self.clients_table.setItem(row, 3, QTableWidgetItem(client.get("phone", "") or ""))
                self.clients_table.setItem(row, 4, QTableWidgetItem(client.get("address", "") or ""))
                self.clients_table.setItem(row, 5, QTableWidgetItem(client.get("tax_id", "") or ""))

                is_active = client.get("is_active", True)
                status_text = "Activo" if is_active else "Inactivo"
                self.clients_table.setItem(row, 6, QTableWidgetItem(status_text))

            self.clients_table.setSortingEnabled(True)
            source = "(cache - sin conexion)" if from_cache else "(servidor)"
            self.status_label.setText(f"Mostrando {len(clients)} clientes {source}")

        except Exception as e:
            logger.error(f"Error fetching clients from API: {e}")
            raise

    def _refresh_from_local(self):
        """Refresh clients from local SQLite database."""
        with SessionLocal() as db:
            clients = db.query(Client).order_by(Client.name).all()

            self.clients_table.setSortingEnabled(False)
            self.clients_table.setRowCount(0)
            self.client_ids = []

            for row, client in enumerate(clients):
                self.clients_table.insertRow(row)
                self.client_ids.append(client.id)

                self.clients_table.setItem(row, 0, QTableWidgetItem(client.code or ""))
                self.clients_table.setItem(row, 1, QTableWidgetItem(client.name or ""))
                self.clients_table.setItem(row, 2, QTableWidgetItem(client.email or ""))
                self.clients_table.setItem(row, 3, QTableWidgetItem(client.phone or ""))
                self.clients_table.setItem(row, 4, QTableWidgetItem(client.address or ""))
                self.clients_table.setItem(row, 5, QTableWidgetItem(client.tax_id or ""))

                status_text = "Activo" if client.is_active else "Inactivo"
                self.clients_table.setItem(row, 6, QTableWidgetItem(status_text))

            self.clients_table.setSortingEnabled(True)
            self.status_label.setText(f"Mostrando {len(clients)} clientes (local)")

    def filter_clients(self):
        """Filter clients based on search text"""
        search_text = self.search_edit.text().lower()

        for row in range(self.clients_table.rowCount()):
            visible = False
            for col in range(self.clients_table.columnCount()):
                item = self.clients_table.item(row, col)
                if item and search_text in item.text().lower():
                    visible = True
                    break
            self.clients_table.setRowHidden(row, not visible)

    def add_client(self):
        """Add new client"""
        dialog = ClientDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
            show_toast(self, "Cliente creado correctamente", "success")

    def edit_client(self):
        """Edit selected client"""
        current_row = self.clients_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "❌ Error", "Seleccione un cliente para editar")
            return

        if current_row >= len(self.client_ids):
            QMessageBox.warning(self, "❌ Error", "Error al obtener datos del cliente")
            return

        client_id = self.client_ids[current_row]
        dialog = ClientDialog(self, client_id=client_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
            show_toast(self, "Cliente actualizado correctamente", "success")

    def delete_client(self):
        """Delete selected client - supports local and remote modes"""
        current_row = self.clients_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Seleccione un cliente para eliminar")
            return

        if current_row >= len(self.client_ids):
            QMessageBox.warning(self, "Error", "Error al obtener datos del cliente")
            return

        client_name = self.clients_table.item(current_row, 1).text()
        client_id = self.client_ids[current_row]

        # Custom confirmation dialog
        dialog = ConfirmationDialog(
            self,
            title="Confirmar Eliminacion",
            message=f"¿Seguro de eliminar '{client_name}'?\n\nEsta accion no se puede deshacer.",
            confirm_text="Eliminar",
            is_danger=True
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            app_mode = get_app_mode()
            try:
                if app_mode.is_remote:
                    app_mode.api.delete_client(str(client_id))
                    self.refresh_data()
                    QMessageBox.information(self, "Exito", f"Cliente '{client_name}' eliminado")
                else:
                    with SessionLocal() as db:
                        # Check for associated documents
                        doc_count = db.query(Document).filter(Document.client_id == client_id).count()
                        if doc_count > 0:
                            confirm = QMessageBox.warning(
                                self, "Advertencia",
                                f"Este cliente tiene {doc_count} documento(s) asociado(s).\n"
                                "¿Desea eliminar el cliente y todos sus documentos?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.No
                            )
                            if confirm != QMessageBox.StandardButton.Yes:
                                return
                            db.query(Document).filter(Document.client_id == client_id).delete()

                        client = db.query(Client).filter(Client.id == client_id).first()
                        if client:
                            db.delete(client)
                            db.commit()
                            self.refresh_data()
                            QMessageBox.information(self, "Exito", f"Cliente '{client_name}' eliminado")
                        else:
                            QMessageBox.warning(self, "Error", "Cliente no encontrado")

            except Exception as e:
                logger.error(f"Error deleting client: {e}")
                QMessageBox.critical(self, "❌ Error", f"Error al eliminar cliente: {str(e)}")

    def retranslate_ui(self):
        """Update all translatable text"""
        # Update title
        if hasattr(self, 'title_label'):
            self.title_label.setText(translator.t("clients.title"))
        
        # Update buttons
        if hasattr(self, 'add_btn'):
            self.add_btn.setText(translator.t("buttons.new_client"))
        if hasattr(self, 'edit_btn'):
            self.edit_btn.setText(translator.t("buttons.edit"))
        if hasattr(self, 'delete_btn'):
            self.delete_btn.setText(translator.t("buttons.delete"))
        if hasattr(self, 'refresh_btn'):
            self.refresh_btn.setText(translator.t("buttons.refresh"))
        
        # Update search
        if hasattr(self, 'search_label'):
            self.search_label.setText(translator.t("buttons.search") + ":")
        if hasattr(self, 'search_edit'):
            self.search_edit.setPlaceholderText(translator.t("clients.search_placeholder"))
        
        # Update table headers
        if hasattr(self, 'clients_table'):
            self.clients_table.setHorizontalHeaderLabels([
                translator.t("clients.code"), translator.t("clients.name"), translator.t("clients.email"),
                translator.t("clients.phone"), translator.t("clients.address"), translator.t("clients.tax_id"), translator.t("clients.active")
            ])

class ProductManagementTab(QWidget):
    """Modern product management tab with Apple-inspired design"""

    def __init__(self):
        super().__init__()
        self.translatable_widgets = {}
        self.setup_ui()
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self.refresh_data)

    def setup_ui(self):
        self.setStyleSheet(UIStyles.get_panel_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        self.title_label = QLabel(translator.t("products.title"))
        self.title_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 600;
            color: {UIStyles.COLORS['text_primary']};
            background: transparent;
        """)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(12)

        self.add_btn = QPushButton(translator.t("buttons.new_product"))
        self.add_btn.clicked.connect(self.add_product)
        self.add_btn.setStyleSheet(UIStyles.get_primary_button_style())
        toolbar_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton(translator.t("buttons.edit"))
        self.edit_btn.clicked.connect(self.edit_product)
        self.edit_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        toolbar_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton(translator.t("buttons.delete"))
        self.delete_btn.clicked.connect(self.delete_product)
        self.delete_btn.setStyleSheet(UIStyles.get_danger_button_style())
        toolbar_layout.addWidget(self.delete_btn)

        toolbar_layout.addStretch()

        self.refresh_btn = QPushButton(translator.t("buttons.refresh"))
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.refresh_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        toolbar_layout.addWidget(self.refresh_btn)

        layout.addLayout(toolbar_layout)

        # Search
        search_layout = QHBoxLayout()
        search_layout.setSpacing(12)

        self.search_label = QLabel(translator.t("buttons.search") + ":")
        self.search_label.setStyleSheet(UIStyles.get_label_style())
        search_layout.addWidget(self.search_label)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(translator.t("products.search_placeholder"))
        self.search_edit.setStyleSheet(UIStyles.get_input_style())
        self.search_edit.textChanged.connect(self.filter_products)
        search_layout.addWidget(self.search_edit)

        layout.addLayout(search_layout)

        # Table
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(8)
        self.products_table.setHorizontalHeaderLabels([
            translator.t("products.code"), translator.t("products.name"), translator.t("products.description"),
            translator.t("products.cost_price"), translator.t("products.sale_price"), translator.t("products.stock"),
            translator.t("products.minimum_stock"), translator.t("products.active")
        ])
        self.products_table.setStyleSheet(UIStyles.get_table_style())
        self.products_table.setAlternatingRowColors(False)
        self.products_table.setShowGrid(False)
        self.products_table.verticalHeader().setVisible(False)
        self.products_table.setSortingEnabled(True)

        header = self.products_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.products_table)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(UIStyles.get_status_label_style())
        layout.addWidget(self.status_label)
    
    def refresh_data(self):
        """Refresh products data - supports local and remote modes"""
        self.product_ids = []
        app_mode = get_app_mode()

        try:
            if app_mode.is_remote:
                self._refresh_from_api(app_mode.api)
            else:
                self._refresh_from_local()
        except Exception as e:
            logger.error(f"Error refreshing products: {e}")
            self.status_label.setText(f"Error: {str(e)}")

    def _refresh_from_api(self, api):
        """Refresh products from remote API (with cache fallback)."""
        response = api.list_products(limit=500)
        products = response.get("items", [])
        from_cache = response.get("_from_cache", False)

        self.products_table.setSortingEnabled(False)
        self.products_table.setRowCount(0)
        self.product_ids = []

        for row, product in enumerate(products):
            self.products_table.insertRow(row)
            self.product_ids.append(product.get("id", ""))

            self.products_table.setItem(row, 0, QTableWidgetItem(product.get("code", "")))
            self.products_table.setItem(row, 1, QTableWidgetItem(product.get("name", "")))
            self.products_table.setItem(row, 2, QTableWidgetItem(product.get("description", "") or ""))
            self.products_table.setItem(row, 3, QTableWidgetItem(f"{product.get('purchase_price', 0):.2f} €"))
            self.products_table.setItem(row, 4, QTableWidgetItem(f"{product.get('sale_price', 0):.2f} €"))
            self.products_table.setItem(row, 5, QTableWidgetItem(str(product.get("current_stock", 0))))
            self.products_table.setItem(row, 6, QTableWidgetItem(str(product.get("minimum_stock", 0))))

            current_stock = product.get("current_stock", 0)
            minimum_stock = product.get("minimum_stock", 0)
            is_active = product.get("is_active", True)
            stock_status = "OK" if current_stock > minimum_stock else "BAJO"
            status_text = f"Activo ({stock_status})" if is_active else "Inactivo"
            self.products_table.setItem(row, 7, QTableWidgetItem(status_text))

        self.products_table.setSortingEnabled(True)
        source = "(cache - sin conexion)" if from_cache else "(servidor)"
        self.status_label.setText(f"Mostrando {len(products)} productos {source}")

    def _refresh_from_local(self):
        """Refresh products from local SQLite database."""
        with SessionLocal() as db:
            products = db.query(Product).order_by(Product.name).all()

            self.products_table.setSortingEnabled(False)
            self.products_table.setRowCount(0)
            self.product_ids = []

            for row, product in enumerate(products):
                self.products_table.insertRow(row)
                self.product_ids.append(product.id)

                self.products_table.setItem(row, 0, QTableWidgetItem(product.code or ""))
                self.products_table.setItem(row, 1, QTableWidgetItem(product.name or ""))
                self.products_table.setItem(row, 2, QTableWidgetItem(product.description or ""))
                self.products_table.setItem(row, 3, QTableWidgetItem(f"{product.purchase_price or 0:.2f} €"))
                self.products_table.setItem(row, 4, QTableWidgetItem(f"{product.sale_price or 0:.2f} €"))
                self.products_table.setItem(row, 5, QTableWidgetItem(str(product.current_stock or 0)))
                self.products_table.setItem(row, 6, QTableWidgetItem(str(product.minimum_stock or 0)))

                stock_status = "OK" if product.current_stock > product.minimum_stock else "BAJO"
                status_text = f"Activo ({stock_status})" if product.is_active else "Inactivo"
                self.products_table.setItem(row, 7, QTableWidgetItem(status_text))

            self.products_table.setSortingEnabled(True)
            self.status_label.setText(f"Mostrando {len(products)} productos (local)")

    def filter_products(self):
        """Filter products based on search text"""
        search_text = self.search_edit.text().lower()

        for row in range(self.products_table.rowCount()):
            visible = False
            for col in range(self.products_table.columnCount()):
                item = self.products_table.item(row, col)
                if item and search_text in item.text().lower():
                    visible = True
                    break
            self.products_table.setRowHidden(row, not visible)

    def add_product(self):
        """Add new product"""
        dialog = ProductDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
            show_toast(self, "Producto creado correctamente", "success")

    def edit_product(self):
        """Edit selected product"""
        current_row = self.products_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "❌ Error", "Seleccione un producto para editar")
            return

        if current_row >= len(self.product_ids):
            QMessageBox.warning(self, "❌ Error", "Error al obtener datos del producto")
            return

        product_id = self.product_ids[current_row]
        dialog = ProductDialog(self, product_id=product_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
            show_toast(self, "Producto actualizado correctamente", "success")

    def delete_product(self):
        """Delete selected product"""
        current_row = self.products_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "❌ Error", "Seleccione un producto para eliminar")
            return

        if current_row >= len(self.product_ids):
            QMessageBox.warning(self, "❌ Error", "Error al obtener datos del producto")
            return

        product_name = self.products_table.item(current_row, 1).text()
        product_id = self.product_ids[current_row]

        # Custom confirmation dialog
        dialog = ConfirmationDialog(
            self,
            title="🗑️ Confirmar Eliminación",
            message=f"¿Está seguro de eliminar el producto '{product_name}'?\n\n"
                    "Esta acción no se puede deshacer.",
            confirm_text="Eliminar",
            is_danger=True
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                with SessionLocal() as db:
                    product = db.query(Product).filter(Product.id == product_id).first()
                    if product:
                        db.delete(product)
                        db.commit()
                        self.refresh_data()
                        QMessageBox.information(self, "✅ Éxito", f"Producto '{product_name}' eliminado correctamente")
                    else:
                        QMessageBox.warning(self, "❌ Error", "Producto no encontrado")

            except Exception as e:
                logger.error(f"Error deleting product: {e}")
                QMessageBox.critical(self, "❌ Error", f"Error al eliminar producto: {str(e)}")

    def retranslate_ui(self):
        """Update all translatable text"""
        # Update title
        if hasattr(self, 'title_label'):
            self.title_label.setText(translator.t("products.title"))
        
        # Update buttons
        if hasattr(self, 'add_btn'):
            self.add_btn.setText(translator.t("buttons.new_product"))
        if hasattr(self, 'edit_btn'):
            self.edit_btn.setText(translator.t("buttons.edit"))
        if hasattr(self, 'delete_btn'):
            self.delete_btn.setText(translator.t("buttons.delete"))
        if hasattr(self, 'refresh_btn'):
            self.refresh_btn.setText(translator.t("buttons.refresh"))
        
        # Update search
        if hasattr(self, 'search_label'):
            self.search_label.setText(translator.t("buttons.search") + ":")
        if hasattr(self, 'search_edit'):
            self.search_edit.setPlaceholderText(translator.t("products.search_placeholder"))
        
        # Update table headers
        if hasattr(self, 'products_table'):
            self.products_table.setHorizontalHeaderLabels([
                translator.t("products.code"), translator.t("products.name"), translator.t("products.description"),
                translator.t("products.cost_price"), translator.t("products.sale_price"), translator.t("products.stock"),
                translator.t("products.minimum_stock"), translator.t("products.active")
            ])

class DocumentManagementTab(QWidget):
    """Modern document management tab with Apple-inspired design"""

    def __init__(self):
        super().__init__()
        self.translatable_widgets = {}
        self.setup_ui()
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self.refresh_data)

    def setup_ui(self):
        self.setStyleSheet(UIStyles.get_panel_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        self.title_label = QLabel(translator.t("documents.title"))
        self.title_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 600;
            color: {UIStyles.COLORS['text_primary']};
            background: transparent;
        """)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(12)

        self.new_invoice_btn = QPushButton(translator.t("buttons.new_invoice"))
        self.new_invoice_btn.clicked.connect(lambda: self.create_document("invoice"))
        self.new_invoice_btn.setStyleSheet(UIStyles.get_primary_button_style())
        toolbar_layout.addWidget(self.new_invoice_btn)

        self.new_quote_btn = QPushButton(translator.t("buttons.new_quote"))
        self.new_quote_btn.clicked.connect(lambda: self.create_document("quote"))
        self.new_quote_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        toolbar_layout.addWidget(self.new_quote_btn)

        self.new_delivery_btn = QPushButton(translator.t("buttons.new_delivery_note"))
        self.new_delivery_btn.clicked.connect(lambda: self.create_document("delivery"))
        self.new_delivery_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        toolbar_layout.addWidget(self.new_delivery_btn)

        toolbar_layout.addStretch()

        self.refresh_btn = QPushButton(translator.t("buttons.refresh"))
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.refresh_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        toolbar_layout.addWidget(self.refresh_btn)

        layout.addLayout(toolbar_layout)

        # Filter
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(12)

        self.filter_label = QLabel(translator.t("documents.filter_by_type") + ":")
        self.filter_label.setStyleSheet(UIStyles.get_label_style())
        filter_layout.addWidget(self.filter_label)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            translator.t("documents.all_types"),
            translator.t("documents.quotes"),
            translator.t("documents.invoices"),
            translator.t("documents.delivery_notes")
        ])
        self.filter_combo.setStyleSheet(UIStyles.get_input_style())
        self.filter_combo.currentTextChanged.connect(self.refresh_data)
        filter_layout.addWidget(self.filter_combo)

        # Status filter
        self.status_filter_label = QLabel("Estado:")
        self.status_filter_label.setStyleSheet(UIStyles.get_label_style())
        filter_layout.addWidget(self.status_filter_label)

        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(["Todos los estados"] + STATUS_OPTIONS_ES)
        self.status_filter_combo.setStyleSheet(UIStyles.get_input_style())
        self.status_filter_combo.currentTextChanged.connect(self.refresh_data)
        filter_layout.addWidget(self.status_filter_combo)

        # Sort by filter
        self.sort_label = QLabel("Ordenar por:")
        self.sort_label.setStyleSheet(UIStyles.get_label_style())
        filter_layout.addWidget(self.sort_label)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Fecha (más reciente)",
            "Fecha (más antiguo)",
            "Código (A-Z)",
            "Código (Z-A)",
            "Cliente (A-Z)",
            "Cliente (Z-A)",
            "Total (mayor)",
            "Total (menor)"
        ])
        self.sort_combo.setStyleSheet(UIStyles.get_input_style())
        self.sort_combo.currentTextChanged.connect(self.refresh_data)
        filter_layout.addWidget(self.sort_combo)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Documents table
        self.docs_table = QTableWidget()
        self.docs_table.setColumnCount(8)
        self.docs_table.setHorizontalHeaderLabels([
            translator.t("documents.code"), translator.t("documents.type"), translator.t("documents.client"),
            translator.t("documents.date"), translator.t("documents.status"), translator.t("documents.total"),
            translator.t("documents.due_date"), translator.t("documents.actions")
        ])
        self.docs_table.setStyleSheet(UIStyles.get_table_style())
        self.docs_table.setAlternatingRowColors(False)
        self.docs_table.setShowGrid(False)
        self.docs_table.verticalHeader().setVisible(False)
        self.docs_table.setSortingEnabled(True)

        header = self.docs_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.docs_table.setColumnWidth(7, 140)  # Fixed width for actions column

        # Enable click/double-click on table
        self.docs_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.docs_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.docs_table.cellClicked.connect(self.on_table_click)
        self.docs_table.cellDoubleClicked.connect(self.on_table_double_click)

        layout.addWidget(self.docs_table)

        # Status label
        self.status_label = QLabel("Cargando documentos...")
        self.status_label.setStyleSheet(UIStyles.get_status_label_style())
        layout.addWidget(self.status_label)
    
    def refresh_data(self):
        """Refresh documents data - supports local and remote modes"""
        app_mode = get_app_mode()
        try:
            if app_mode.is_remote:
                self._refresh_from_api(app_mode.api)
            else:
                self._refresh_from_local()
        except Exception as e:
            logger.error(f"Error refreshing documents: {e}")
            self.status_label.setText(f"Error: {str(e)}")

    def _get_doc_type_filter(self):
        """Get document type filter for API."""
        filter_type = self.filter_combo.currentText()
        type_map = {
            "Presupuestos": "quote",
            "Facturas": "invoice",
            "Albaranes": "delivery_note"
        }
        return type_map.get(filter_type)

    def _get_status_filter(self):
        """Get status filter for API."""
        if hasattr(self, 'status_filter_combo'):
            status_filter = self.status_filter_combo.currentText()
            status_map = {
                "Borrador": "draft",
                "No Enviado": "not_sent",
                "Enviado": "sent",
                "Aceptado": "accepted",
                "Rechazado": "rejected",
                "Pagado": "paid",
                "Pago Parcial": "partially_paid",
                "Cancelado": "cancelled",
            }
            return status_map.get(status_filter)
        return None

    def _refresh_from_api(self, api):
        """Refresh documents from remote API (with cache fallback)."""
        try:
            doc_type = self._get_doc_type_filter()
            doc_status = self._get_status_filter()

            response = api.list_documents(limit=100, doc_type=doc_type, doc_status=doc_status)
            documents = response.get("items", [])
            from_cache = response.get("_from_cache", False)

            self.docs_table.setSortingEnabled(False)
            self.docs_table.setRowCount(0)
            self._document_ids = []

            for row, doc in enumerate(documents):
                self._add_document_row(row, doc, is_remote=True)

            self.docs_table.setSortingEnabled(True)
            filter_type = self.filter_combo.currentText()
            source = "(cache - sin conexion)" if from_cache else "(servidor)"
            self.status_label.setText(f"Mostrando {len(documents)} documentos {source} - Filtro: {filter_type}")

        except Exception as e:
            logger.error(f"Error fetching documents from API: {e}")
            raise

    def _refresh_from_local(self):
        """Refresh documents from local SQLite database."""
        with SessionLocal() as db:
            # Get type filter
            filter_type = self.filter_combo.currentText()

            # Build query with eager loading for client relationship
            query = db.query(Document).options(joinedload(Document.client))
            if filter_type != "Todos":
                if filter_type == "Presupuestos":
                    query = query.filter(Document.type == DocumentType.QUOTE)
                elif filter_type == "Facturas":
                    query = query.filter(Document.type == DocumentType.INVOICE)
                elif filter_type == "Albaranes":
                    query = query.filter(Document.type == DocumentType.DELIVERY_NOTE)

            # Get status filter
            if hasattr(self, 'status_filter_combo'):
                status_filter = self.status_filter_combo.currentText()
                status_map = {
                    "Borrador": DocumentStatus.DRAFT,
                    "No Enviado": DocumentStatus.NOT_SENT,
                    "Enviado": DocumentStatus.SENT,
                    "Aceptado": DocumentStatus.ACCEPTED,
                    "Rechazado": DocumentStatus.REJECTED,
                    "Pagado": DocumentStatus.PAID,
                    "Pago Parcial": DocumentStatus.PARTIALLY_PAID,
                    "Cancelado": DocumentStatus.CANCELLED,
                }
                if status_filter in status_map:
                    query = query.filter(Document.status == status_map[status_filter])

            # Apply sort order
            sort_option = self.sort_combo.currentText() if hasattr(self, 'sort_combo') else "Fecha (más reciente)"

            if sort_option == "Fecha (más reciente)":
                query = query.order_by(Document.issue_date.desc())
            elif sort_option == "Fecha (más antiguo)":
                query = query.order_by(Document.issue_date.asc())
            elif sort_option == "Código (A-Z)":
                query = query.order_by(Document.code.asc())
            elif sort_option == "Código (Z-A)":
                query = query.order_by(Document.code.desc())
            elif sort_option == "Cliente (A-Z)":
                query = query.join(Client).order_by(Client.name.asc())
            elif sort_option == "Cliente (Z-A)":
                query = query.join(Client).order_by(Client.name.desc())
            elif sort_option == "Total (mayor)":
                query = query.order_by(Document.total.desc())
            elif sort_option == "Total (menor)":
                query = query.order_by(Document.total.asc())
            else:
                query = query.order_by(Document.updated_at.desc())

            documents = query.limit(100).all()

            self.docs_table.setSortingEnabled(False)
            self.docs_table.setRowCount(0)
            self._document_ids = []

            for row, doc in enumerate(documents):
                self._add_document_row_local(row, doc)

            self.docs_table.setSortingEnabled(True)
            self.status_label.setText(f"Mostrando {len(documents)} documentos (local) - Filtro: {filter_type}")

    def _add_document_row(self, row, doc, is_remote=False):
        """Add a document row to the table (for API data)."""
        self.docs_table.insertRow(row)
        doc_id = doc.get("id", "")
        self._document_ids.append(str(doc_id))

        # Document code - make it look clickable
        code_item = QTableWidgetItem(doc.get("code", ""))
        code_item.setData(Qt.ItemDataRole.UserRole, str(doc_id))
        code_font = QFont()
        code_font.setUnderline(True)
        code_font.setBold(True)
        code_item.setFont(code_font)
        code_item.setForeground(QColor("#007AFF"))
        self.docs_table.setItem(row, 0, code_item)

        # Document type
        doc_type = doc.get("type", "quote")
        type_map = {"quote": "Presupuesto", "invoice": "Factura", "delivery_note": "Albarán"}
        type_colors = {"quote": "#9b59b6", "invoice": "#e67e22", "delivery_note": "#3498db"}
        type_item = QTableWidgetItem(type_map.get(doc_type, doc_type))
        type_font = QFont()
        type_font.setBold(True)
        type_item.setFont(type_font)
        type_item.setForeground(QColor(type_colors.get(doc_type, "#6E6E73")))
        self.docs_table.setItem(row, 1, type_item)

        # Client name
        client_name = doc.get("client_name", "N/A") or "N/A"
        self.docs_table.setItem(row, 2, QTableWidgetItem(client_name))

        # Date
        date_str = doc.get("issue_date", "")
        if date_str:
            try:
                date_text = datetime.fromisoformat(date_str.replace("Z", "+00:00")).strftime('%d/%m/%Y')
            except:
                date_text = date_str[:10] if len(date_str) >= 10 else date_str
        else:
            date_text = ""
        self.docs_table.setItem(row, 3, QTableWidgetItem(date_text))

        # Status
        status_value = doc.get("status", "draft")
        status_text = get_status_label(status_value)
        status_colors = {
            "draft": "#6E6E73", "not_sent": "#FF9500", "sent": "#007AFF",
            "accepted": "#34C759", "rejected": "#FF3B30", "paid": "#5856D6",
            "partially_paid": "#FF9500", "cancelled": "#8E8E93"
        }
        status_item = QTableWidgetItem(status_text)
        status_item.setForeground(QColor(status_colors.get(status_value, "#6E6E73")))
        status_font = QFont()
        status_font.setBold(True)
        status_item.setFont(status_font)
        self.docs_table.setItem(row, 4, status_item)

        # Total
        total = doc.get("total", 0)
        self.docs_table.setItem(row, 5, QTableWidgetItem(f"{total:.2f} €"))

        # Due date
        due_str = doc.get("due_date", "")
        if due_str:
            try:
                due_text = datetime.fromisoformat(due_str.replace("Z", "+00:00")).strftime('%d/%m/%Y')
            except:
                due_text = due_str[:10] if len(due_str) >= 10 else due_str
        else:
            due_text = ""
        self.docs_table.setItem(row, 6, QTableWidgetItem(due_text))

        # Actions - placeholder for now (PDF/delete need special handling in remote mode)
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(4, 4, 4, 4)
        actions_layout.setSpacing(4)

        pdf_btn = QPushButton("PDF")
        pdf_btn.setToolTip("Generar PDF")
        pdf_btn.setMinimumWidth(40)
        pdf_btn.setMaximumHeight(26)
        pdf_btn.clicked.connect(lambda checked, did=doc_id: self.generate_pdf_by_id(did))
        actions_layout.addWidget(pdf_btn)

        del_btn = QPushButton("X")
        del_btn.setToolTip("Eliminar")
        del_btn.setMinimumWidth(30)
        del_btn.setMaximumHeight(26)
        del_btn.setStyleSheet("color: red; font-weight: bold;")
        del_btn.clicked.connect(lambda checked, did=doc_id: self.delete_document_by_id(did))
        actions_layout.addWidget(del_btn)

        self.docs_table.setCellWidget(row, 7, actions_widget)

    def _add_document_row_local(self, row, doc):
        """Add a document row to the table (for local ORM objects)."""
        self.docs_table.insertRow(row)
        self._document_ids.append(str(doc.id))

        # Document code
        code_item = QTableWidgetItem(doc.code or "")
        code_item.setData(Qt.ItemDataRole.UserRole, str(doc.id))
        code_font = QFont()
        code_font.setUnderline(True)
        code_font.setBold(True)
        code_item.setFont(code_font)
        code_item.setForeground(QColor("#007AFF"))
        self.docs_table.setItem(row, 0, code_item)

        # Document type
        type_text = ""
        if doc.type == DocumentType.QUOTE:
            type_text = "Presupuesto"
        elif doc.type == DocumentType.INVOICE:
            type_text = "Factura"
        elif doc.type == DocumentType.DELIVERY_NOTE:
            type_text = "Albarán"

        type_item = QTableWidgetItem(type_text)
        type_font = QFont()
        type_font.setBold(True)
        type_item.setFont(type_font)

        if doc.type == DocumentType.QUOTE:
            type_item.setForeground(QColor("#9b59b6"))
        elif doc.type == DocumentType.INVOICE:
            type_item.setForeground(QColor("#e67e22"))
        elif doc.type == DocumentType.DELIVERY_NOTE:
            type_item.setForeground(QColor("#3498db"))

        self.docs_table.setItem(row, 1, type_item)

        # Client name
        try:
            client_name = doc.client.name if doc.client else "N/A"
        except:
            client_name = "N/A"
        self.docs_table.setItem(row, 2, QTableWidgetItem(client_name))

        # Date
        date_text = doc.issue_date.strftime('%d/%m/%Y') if doc.issue_date else ""
        self.docs_table.setItem(row, 3, QTableWidgetItem(date_text))

        # Status
        status_text = get_status_label(doc.status)
        status_colors = {
            DocumentStatus.DRAFT: "#6E6E73",
            DocumentStatus.NOT_SENT: "#FF9500",
            DocumentStatus.SENT: "#007AFF",
            DocumentStatus.ACCEPTED: "#34C759",
            DocumentStatus.REJECTED: "#FF3B30",
            DocumentStatus.PAID: "#5856D6",
            DocumentStatus.PARTIALLY_PAID: "#FF9500",
            DocumentStatus.CANCELLED: "#8E8E93",
        }
        status_color = status_colors.get(doc.status, "#6E6E73")

        status_item = QTableWidgetItem(status_text)
        status_item.setForeground(QColor(status_color))
        status_font = QFont()
        status_font.setBold(True)
        status_item.setFont(status_font)
        self.docs_table.setItem(row, 4, status_item)

        # Total
        self.docs_table.setItem(row, 5, QTableWidgetItem(f"{doc.total or 0:.2f} €"))

        # Due date
        due_text = doc.due_date.strftime('%d/%m/%Y') if doc.due_date else ""
        self.docs_table.setItem(row, 6, QTableWidgetItem(due_text))

        # Actions
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(4, 4, 4, 4)
        actions_layout.setSpacing(4)

        pdf_btn = QPushButton("PDF")
        pdf_btn.setToolTip("Generar PDF")
        pdf_btn.setMinimumWidth(40)
        pdf_btn.setMaximumHeight(26)
        pdf_btn.clicked.connect(lambda checked, d=doc: self.generate_pdf(d))
        actions_layout.addWidget(pdf_btn)

        del_btn = QPushButton("X")
        del_btn.setToolTip("Eliminar")
        del_btn.setMinimumWidth(30)
        del_btn.setMaximumHeight(26)
        del_btn.setStyleSheet("color: red; font-weight: bold;")
        del_btn.clicked.connect(lambda checked, d=doc: self.delete_document(d))
        actions_layout.addWidget(del_btn)

        self.docs_table.setCellWidget(row, 7, actions_widget)

    def generate_pdf_by_id(self, doc_id):
        """Generate PDF for document by ID (used in remote mode)."""
        app_mode = get_app_mode()
        try:
            if app_mode.is_remote:
                # In remote mode, get PDF from API
                pdf_bytes = app_mode.api.get_document_pdf(str(doc_id))
                
                # Save to file
                import os
                from datetime import datetime
                
                # Get document info for filename
                response = app_mode.api.get_document(str(doc_id))
                code = response.get("code", f"document_{doc_id}")
                safe_code = code.replace("/", "-").replace("\\", "-")
                
                # Create downloads directory if needed
                downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads", "Dragofactu")
                os.makedirs(downloads_dir, exist_ok=True)
                
                # Save PDF
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{safe_code}_{timestamp}.pdf"
                filepath = os.path.join(downloads_dir, filename)
                
                with open(filepath, "wb") as f:
                    f.write(pdf_bytes)
                
                QMessageBox.information(
                    self, "PDF Generado",
                    f"PDF guardado en:\n{filepath}"
                )
                
                # Optionally open the file
                import subprocess
                import platform
                try:
                    if platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", filepath])
                    elif platform.system() == "Windows":
                        os.startfile(filepath)
                    else:  # Linux
                        subprocess.run(["xdg-open", filepath])
                except:
                    pass  # Ignore if can't open
            else:
                with SessionLocal() as db:
                    doc = db.query(Document).filter(Document.id == uuid.UUID(doc_id)).first()
                    if doc:
                        self.generate_pdf(doc)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generando PDF: {str(e)}")

    def delete_document_by_id(self, doc_id):
        """Delete document by ID (supports remote mode)."""
        app_mode = get_app_mode()
        reply = QMessageBox.question(
            self, "Confirmar", "¿Eliminar este documento?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            if app_mode.is_remote:
                app_mode.api.delete_document(str(doc_id))
                self.refresh_data()
                QMessageBox.information(self, "Exito", "Documento eliminado")
            else:
                with SessionLocal() as db:
                    doc = db.query(Document).filter(Document.id == uuid.UUID(doc_id)).first()
                    if doc:
                        self.delete_document(doc)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error eliminando documento: {str(e)}")
    
    def create_document(self, doc_type):
        """Create new document"""
        dialog = DocumentDialog(self, doc_type)
        if dialog.exec():
            self.refresh_data()

    def on_table_click(self, row, column):
        """Handle click on table - if clicked on code column (0), open editor"""
        if column == 0:  # Code column clicked
            self._open_document_editor(row)

    def on_table_double_click(self, row, column):
        """Handle double-click on table row - opens edit dialog"""
        self._open_document_editor(row)

    def _open_document_editor(self, row):
        """Open the full document editor for the given row"""
        if row < 0 or row >= len(self._document_ids):
            return
        raw_id = self._document_ids[row]
        try:
            doc_id = uuid.UUID(raw_id) if isinstance(raw_id, str) else raw_id
            with SessionLocal() as db:
                doc = db.query(Document).filter(Document.id == doc_id).first()
                if doc:
                    # Determine document type
                    doc_type = "quote"
                    if doc.type == DocumentType.INVOICE:
                        doc_type = "invoice"
                    elif doc.type == DocumentType.DELIVERY_NOTE:
                        doc_type = "delivery"

                    # Open full editor dialog
                    dialog = DocumentDialog(self, doc_type, document_id=str(doc.id))
                    if dialog.exec():
                        self.refresh_data()
                        self._sync_dashboard()
                        self._sync_inventory()
        except Exception as e:
            logger.error(f"Error opening document editor: {e}")
            QMessageBox.critical(self, "Error", f"Error al abrir documento: {str(e)}")

    def view_document(self, document):
        """View document details - supports local and remote"""
        app_mode = get_app_mode()
        try:
            # Get document ID as string for API, or UUID for local
            doc_id_str = str(document.id) if hasattr(document, 'id') else str(document.get('id', ''))

            if app_mode.is_remote:
                # Fetch from API
                doc_data = app_mode.api.get_document(doc_id_str)
                if not doc_data:
                    QMessageBox.warning(self, "Error", "Documento no encontrado")
                    return

                # Extract data from API response
                doc_type_value = doc_data.get('type', 'quote')
                doc_type = "Presupuesto" if doc_type_value == 'quote' else "Factura" if doc_type_value == 'invoice' else "Albarán"
                client_name = doc_data.get('client_name', 'N/A')
                code = doc_data.get('code', 'N/A')
                issue_date = doc_data.get('issue_date', 'N/A')
                due_date = doc_data.get('due_date', 'N/A')
                status_text = get_status_label(doc_data.get('status', 'draft'))
                subtotal = doc_data.get('subtotal', 0) or 0
                tax_amount = doc_data.get('tax_amount', 0) or 0
                total = doc_data.get('total', 0) or 0
                notes = doc_data.get('notes', '')
            else:
                # Fetch from local database
                doc_id = uuid.UUID(doc_id_str) if not isinstance(document.id, uuid.UUID) else document.id
                with SessionLocal() as db:
                    doc = db.query(Document).options(joinedload(Document.client)).filter(Document.id == doc_id).first()
                    if not doc:
                        QMessageBox.warning(self, "Error", "Documento no encontrado")
                        return

                    doc_type = "Presupuesto" if doc.type == DocumentType.QUOTE else "Factura" if doc.type == DocumentType.INVOICE else "Albarán"
                    client_name = doc.client.name if doc.client else "N/A"
                    code = doc.code or ""
                    issue_date = doc.issue_date.strftime('%d/%m/%Y') if doc.issue_date else "N/A"
                    due_date = doc.due_date.strftime('%d/%m/%Y') if doc.due_date else "N/A"
                    status_text = doc.status.value if hasattr(doc.status, 'value') else str(doc.status)
                    subtotal = doc.subtotal or 0
                    tax_amount = doc.tax_amount or 0
                    total = doc.total or 0
                    notes = doc.notes or ''

            # Create view dialog
            view_dialog = QDialog(self)
            view_dialog.setWindowTitle(f"📄 {doc_type} - {code}")
            view_dialog.setModal(True)
            view_dialog.resize(600, 500)

            layout = QVBoxLayout(view_dialog)

            # Header
            header = QLabel(f"📄 {doc_type}: {code}")
            header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            layout.addWidget(header)

            # Document details
            details_group = QGroupBox("📋 Detalles del Documento")
            details_layout = QFormLayout(details_group)
            details_layout.addRow("Código:", QLabel(code))
            details_layout.addRow("Tipo:", QLabel(doc_type))
            details_layout.addRow("Estado:", QLabel(status_text))
            details_layout.addRow("Cliente:", QLabel(client_name))
            details_layout.addRow("Fecha Emisión:", QLabel(str(issue_date)))
            details_layout.addRow("Fecha Vencimiento:", QLabel(str(due_date)))
            layout.addWidget(details_group)

            # Financial details
            financial_group = QGroupBox("💰 Detalles Financieros")
            financial_layout = QFormLayout(financial_group)
            financial_layout.addRow("Subtotal:", QLabel(f"{subtotal:.2f} €"))
            financial_layout.addRow("IVA:", QLabel(f"{tax_amount:.2f} €"))
            financial_layout.addRow("Total:", QLabel(f"{total:.2f} €"))
            layout.addWidget(financial_group)

            # Notes
            if notes:
                notes_group = QGroupBox("📝 Notas")
                notes_layout = QVBoxLayout(notes_group)
                notes_text = QTextEdit()
                notes_text.setPlainText(notes)
                notes_text.setReadOnly(True)
                notes_text.setMaximumHeight(100)
                notes_layout.addWidget(notes_text)
                layout.addWidget(notes_group)

            # Buttons layout
            buttons_layout = QHBoxLayout()

            # PDF button
            pdf_btn = QPushButton("Exportar PDF")
            pdf_btn.setStyleSheet(UIStyles.get_primary_button_style())
            pdf_btn.clicked.connect(lambda: (view_dialog.accept(), self.generate_pdf_by_id(doc_id_str)))
            buttons_layout.addWidget(pdf_btn)

            # Edit button
            edit_btn = QPushButton("Editar")
            edit_btn.setStyleSheet(UIStyles.get_secondary_button_style())
            edit_btn.clicked.connect(lambda: (view_dialog.accept(), self.edit_document_by_id(doc_id_str)))
            buttons_layout.addWidget(edit_btn)

            # Close button
            close_btn = QPushButton("Cerrar")
            close_btn.setStyleSheet(UIStyles.get_secondary_button_style())
            close_btn.clicked.connect(view_dialog.accept)
            buttons_layout.addWidget(close_btn)

            layout.addLayout(buttons_layout)

            view_dialog.exec()

        except Exception as e:
            logger.error(f"Error viewing document: {e}")
            QMessageBox.critical(self, "Error", f"Error al ver documento: {str(e)}")

    def edit_document_by_id(self, document_id: str):
        """Edit document by ID - supports local and remote"""
        app_mode = get_app_mode()
        try:
            if app_mode.is_remote:
                # Fetch document type from API
                doc_data = app_mode.api.get_document(document_id)
                if not doc_data:
                    QMessageBox.warning(self, "Error", "Documento no encontrado")
                    return
                doc_type_value = doc_data.get('type', 'quote')
                doc_type = doc_type_value  # quote, invoice, delivery_note
                if doc_type == 'delivery_note':
                    doc_type = 'delivery'
            else:
                # Fetch from local database
                doc_id = uuid.UUID(document_id)
                with SessionLocal() as db:
                    doc = db.query(Document).filter(Document.id == doc_id).first()
                    if not doc:
                        QMessageBox.warning(self, "Error", "Documento no encontrado")
                        return

                    doc_type = "quote"
                    if doc.type == DocumentType.INVOICE:
                        doc_type = "invoice"
                    elif doc.type == DocumentType.DELIVERY_NOTE:
                        doc_type = "delivery"

            # Open full editor dialog
            dialog = DocumentDialog(self, doc_type, document_id=document_id)
            if dialog.exec():
                self.refresh_data()
                self._sync_dashboard()
                self._sync_inventory()

        except Exception as e:
            logger.error(f"Error editing document: {e}")
            QMessageBox.critical(self, "Error", f"Error al editar documento: {str(e)}")

    def edit_document(self, document):
        """Edit document - wrapper for edit_document_by_id"""
        doc_id_str = str(document.id) if hasattr(document, 'id') else str(document.get('id', ''))
        self.edit_document_by_id(doc_id_str)

    def delete_document(self, document):
        """Delete document"""
        reply = QMessageBox.question(
            self, "🗑️ Confirmar Eliminación",
            f"¿Está seguro de eliminar el documento '{document.code}'?\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                with SessionLocal() as db:
                    doc = db.query(Document).filter(Document.id == document.id).first()
                    if doc:
                        doc_code = doc.code
                        db.delete(doc)
                        db.commit()
                        self.refresh_data()
                        # Sync with Dashboard
                        self._sync_dashboard()
                        QMessageBox.information(self, "Exito", f"Documento '{doc_code}' eliminado correctamente")
                    else:
                        QMessageBox.warning(self, "Error", "Documento no encontrado")

            except Exception as e:
                logger.error(f"Error deleting document: {e}")
                QMessageBox.critical(self, "Error", f"Error al eliminar documento: {str(e)}")

    def generate_pdf(self, document):
        """Generate PDF for document"""
        try:
            with SessionLocal() as db:
                # Reload document with all relationships
                doc = db.query(Document).options(
                    joinedload(Document.client),
                    joinedload(Document.lines)
                ).filter(Document.id == document.id).first()

                if not doc:
                    QMessageBox.warning(self, "Error", "Documento no encontrado")
                    return

                # Determine default filename
                doc_type_prefix = {
                    DocumentType.INVOICE: 'Factura',
                    DocumentType.QUOTE: 'Presupuesto',
                    DocumentType.DELIVERY_NOTE: 'Albaran',
                }.get(doc.type, 'Documento')

                default_filename = f"{doc_type_prefix}_{doc.code}.pdf"

                # Show save dialog
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Guardar PDF",
                    default_filename,
                    "Archivos PDF (*.pdf)"
                )

                if not file_path:
                    return  # User cancelled

                # Ensure .pdf extension
                if not file_path.lower().endswith('.pdf'):
                    file_path += '.pdf'

                # Get document lines
                lines = list(doc.lines) if doc.lines else []

                # Generate PDF
                generator = InvoicePDFGenerator()
                generator.generate(doc, lines, doc.client, file_path)

                # Show success message
                QMessageBox.information(
                    self,
                    "PDF Generado",
                    f"El documento se ha guardado correctamente:\n\n{file_path}"
                )

                logger.info(f"PDF generated successfully: {file_path}")

        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al generar el PDF:\n\n{str(e)}"
            )

    def retranslate_ui(self):
        """Update all translatable text"""
        # Update title
        if hasattr(self, 'title_label'):
            self.title_label.setText(translator.t("documents.title"))
        
        # Update buttons
        if hasattr(self, 'new_invoice_btn'):
            self.new_invoice_btn.setText(translator.t("buttons.new_invoice"))
        if hasattr(self, 'new_quote_btn'):
            self.new_quote_btn.setText(translator.t("buttons.new_quote"))
        if hasattr(self, 'new_delivery_btn'):
            self.new_delivery_btn.setText(translator.t("buttons.new_delivery_note"))
        if hasattr(self, 'refresh_btn'):
            self.refresh_btn.setText(translator.t("buttons.refresh"))
        
        # Update filter
        if hasattr(self, 'filter_label'):
            self.filter_label.setText(translator.t("documents.filter_by_type") + ":")
        if hasattr(self, 'filter_combo'):
            current_text = self.filter_combo.currentText()
            self.filter_combo.clear()
            self.filter_combo.addItems([
                translator.t("documents.all_types"),
                translator.t("documents.quotes"),
                translator.t("documents.invoices"),
                translator.t("documents.delivery_notes")
            ])
            # Try to restore previous selection
            index = self.filter_combo.findText(current_text)
            if index >= 0:
                self.filter_combo.setCurrentIndex(index)
        
        # Update table headers
        if hasattr(self, 'docs_table'):
            self.docs_table.setHorizontalHeaderLabels([
                translator.t("documents.code"), translator.t("documents.type"), translator.t("documents.client"),
                translator.t("documents.date"), translator.t("documents.status"), translator.t("documents.total"),
                translator.t("documents.due_date"), translator.t("documents.actions")
            ])

    def _sync_dashboard(self):
        """Sync changes with the Dashboard panel"""
        try:
            # Find the main window and refresh dashboard
            parent = self.parent()
            while parent is not None:
                if hasattr(parent, 'dashboard') and parent.dashboard:
                    parent.dashboard.refresh_data()
                    break
                parent = parent.parent()
        except Exception as e:
            logger.warning(f"Could not sync with dashboard: {e}")

    def _sync_inventory(self):
        """Sync changes with the Inventory panel"""
        try:
            parent = self.parent()
            while parent is not None:
                if hasattr(parent, 'inventory_tab') and parent.inventory_tab:
                    parent.inventory_tab.refresh_data()
                    break
                parent = parent.parent()
        except Exception as e:
            logger.warning(f"Could not sync with inventory: {e}")


class InventoryManagementTab(QWidget):
    """Modern inventory management tab with Apple-inspired design"""

    def __init__(self):
        super().__init__()
        self.translatable_widgets = {}
        self.setup_ui()
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self.refresh_data)

    def setup_ui(self):
        self.setStyleSheet(UIStyles.get_panel_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        self.title_label = QLabel(translator.t("inventory.title"))
        self.title_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 600;
            color: {UIStyles.COLORS['text_primary']};
            background: transparent;
        """)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(12)

        self.add_btn = QPushButton(translator.t("buttons.new_product"))
        self.add_btn.clicked.connect(self.add_product)
        self.add_btn.setStyleSheet(UIStyles.get_primary_button_style())
        toolbar_layout.addWidget(self.add_btn)

        self.adjust_stock_btn = QPushButton(translator.t("buttons.adjust_stock"))
        self.adjust_stock_btn.clicked.connect(self.adjust_stock)
        self.adjust_stock_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        toolbar_layout.addWidget(self.adjust_stock_btn)

        self.generate_report_btn = QPushButton(translator.t("buttons.report"))
        self.generate_report_btn.clicked.connect(self.generate_report)
        self.generate_report_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        toolbar_layout.addWidget(self.generate_report_btn)

        toolbar_layout.addStretch()

        self.refresh_btn = QPushButton(translator.t("buttons.refresh"))
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.refresh_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        toolbar_layout.addWidget(self.refresh_btn)

        layout.addLayout(toolbar_layout)

        # Search and filter
        search_layout = QHBoxLayout()
        search_layout.setSpacing(12)

        self.search_label = QLabel(translator.t("buttons.search") + ":")
        self.search_label.setStyleSheet(UIStyles.get_label_style())
        search_layout.addWidget(self.search_label)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(translator.t("inventory.search_placeholder"))
        self.search_edit.setStyleSheet(UIStyles.get_input_style())
        self.search_edit.textChanged.connect(self.filter_products)
        search_layout.addWidget(self.search_edit)

        self.filter_label = QLabel(translator.t("inventory.filter") + ":")
        self.filter_label.setStyleSheet(UIStyles.get_label_style())
        search_layout.addWidget(self.filter_label)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            translator.t("inventory.all_items"),
            translator.t("inventory.in_stock"),
            translator.t("inventory.low_stock"),
            translator.t("inventory.out_of_stock"),
            translator.t("inventory.active_only"),
            translator.t("inventory.inactive_only")
        ])
        self.filter_combo.setStyleSheet(UIStyles.get_input_style())
        self.filter_combo.currentTextChanged.connect(self.filter_products)
        search_layout.addWidget(self.filter_combo)

        layout.addLayout(search_layout)

        # Statistics cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self.total_products_label = QLabel(translator.t("inventory.total_products") + ": 0")
        self.total_products_label.setStyleSheet(f"""
            background-color: {UIStyles.COLORS['bg_card']};
            border: 1px solid {UIStyles.COLORS['border_light']};
            border-radius: 8px;
            padding: 12px 20px;
            font-weight: 500;
            color: {UIStyles.COLORS['text_primary']};
        """)
        stats_layout.addWidget(self.total_products_label)

        self.low_stock_label = QLabel(translator.t("inventory.low_stock") + ": 0")
        self.low_stock_label.setStyleSheet(f"""
            background-color: {UIStyles.COLORS['bg_card']};
            border: 1px solid {UIStyles.COLORS['warning']};
            border-radius: 8px;
            padding: 12px 20px;
            font-weight: 500;
            color: {UIStyles.COLORS['warning']};
        """)
        stats_layout.addWidget(self.low_stock_label)

        self.total_value_label = QLabel(translator.t("inventory.total_value") + ": 0.00 €")
        self.total_value_label.setStyleSheet(f"""
            background-color: {UIStyles.COLORS['bg_card']};
            border: 1px solid {UIStyles.COLORS['success']};
            border-radius: 8px;
            padding: 12px 20px;
            font-weight: 500;
            color: {UIStyles.COLORS['success']};
        """)
        stats_layout.addWidget(self.total_value_label)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Table
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(9)
        self.inventory_table.setHorizontalHeaderLabels([
            translator.t("inventory.code"), translator.t("inventory.product"), translator.t("inventory.description"),
            translator.t("inventory.current_stock"), translator.t("inventory.minimum_stock"), translator.t("inventory.status"),
            translator.t("inventory.total_value"), translator.t("inventory.actions"), translator.t("inventory.last_movement")
        ])
        self.inventory_table.setStyleSheet(UIStyles.get_table_style())
        self.inventory_table.setAlternatingRowColors(False)
        self.inventory_table.setShowGrid(False)
        self.inventory_table.verticalHeader().setVisible(False)
        self.inventory_table.setSortingEnabled(True)

        header = self.inventory_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.inventory_table)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(UIStyles.get_status_label_style())
        layout.addWidget(self.status_label)
    
    def refresh_data(self):
        """Refresh inventory data - supports local and remote modes"""
        app_mode = get_app_mode()
        try:
            if app_mode.is_remote:
                self._refresh_from_api(app_mode.api)
            else:
                self._refresh_from_local()
        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")

    def _refresh_from_api(self, api):
        """Refresh inventory data from remote API (with cache fallback)."""
        response = api.list_products(limit=500)
        products = response.get("items", [])
        from_cache = response.get("_from_cache", False)
        self._inventory_products = products

        self.inventory_table.setSortingEnabled(False)
        self.inventory_table.setRowCount(0)
        low_stock_count = 0
        total_value = 0.0

        for row, product in enumerate(products):
            self.inventory_table.insertRow(row)

            self.inventory_table.setItem(row, 0, QTableWidgetItem(product.get("code", "")))
            self.inventory_table.setItem(row, 1, QTableWidgetItem(product.get("name", "")))
            self.inventory_table.setItem(row, 2, QTableWidgetItem(product.get("description", "") or ""))
            self.inventory_table.setItem(row, 3, QTableWidgetItem(str(product.get("current_stock", 0))))
            self.inventory_table.setItem(row, 4, QTableWidgetItem(str(product.get("minimum_stock", 0))))

            current_stock = product.get("current_stock", 0) or 0
            minimum_stock = product.get("minimum_stock", 0) or 0
            stock_status = "OK"
            stock_color = "green"
            if current_stock <= 0:
                stock_status = "SIN STOCK"
                stock_color = "red"
            elif current_stock <= minimum_stock:
                stock_status = "BAJO"
                stock_color = "orange"
                low_stock_count += 1

            status_item = QTableWidgetItem(stock_status)
            from PySide6.QtGui import QColor, QFont
            status_item.setForeground(QColor(stock_color))
            font = QFont()
            font.setBold(True)
            status_item.setFont(font)
            self.inventory_table.setItem(row, 5, status_item)

            total_product_value = float(current_stock) * float(product.get("sale_price", 0) or 0)
            total_value += total_product_value
            value_item = QTableWidgetItem(f"{total_product_value:.2f} €")
            self.inventory_table.setItem(row, 6, value_item)

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)

            adjust_btn = QPushButton("📊")
            adjust_btn.setToolTip("Ajustar Stock")
            adjust_btn.setMaximumSize(30, 25)
            adjust_btn.clicked.connect(lambda checked, p=product: self.adjust_product_stock(p))
            actions_layout.addWidget(adjust_btn)

            edit_btn = QPushButton("✏️")
            edit_btn.setToolTip("Editar Producto")
            edit_btn.setMaximumSize(30, 25)
            edit_btn.clicked.connect(lambda checked, p=product: self.edit_product(p))
            actions_layout.addWidget(edit_btn)

            self.inventory_table.setCellWidget(row, 7, actions_widget)

            last_movement = "N/A"
            self.inventory_table.setItem(row, 8, QTableWidgetItem(last_movement))

        self.inventory_table.setSortingEnabled(True)
        self.total_products_label.setText(f"Total: {len(products)}")
        self.low_stock_label.setText(f"Stock Bajo: {low_stock_count}")
        self.total_value_label.setText(f"Valor Total: {total_value:.2f} €")

        source = "(cache - sin conexion)" if from_cache else "(servidor)"
        self.status_label.setText(f"📊 Mostrando {len(products)} productos - {low_stock_count} con stock bajo {source}")

    def _refresh_from_local(self):
        """Refresh inventory data from local SQLite database."""
        with SessionLocal() as db:
            products = db.query(Product).all()
            self._inventory_products = products

            self.inventory_table.setSortingEnabled(False)
            self.inventory_table.setRowCount(0)
            low_stock_count = 0
            total_value = 0.0

            for row, product in enumerate(products):
                self.inventory_table.insertRow(row)

                self.inventory_table.setItem(row, 0, QTableWidgetItem(product.code or ""))
                self.inventory_table.setItem(row, 1, QTableWidgetItem(product.name or ""))
                self.inventory_table.setItem(row, 2, QTableWidgetItem(product.description or ""))
                self.inventory_table.setItem(row, 3, QTableWidgetItem(str(product.current_stock or 0)))
                self.inventory_table.setItem(row, 4, QTableWidgetItem(str(product.minimum_stock or 0)))

                # Stock status
                stock_status = "OK"
                stock_color = "green"
                if product.current_stock <= 0:
                    stock_status = "SIN STOCK"
                    stock_color = "red"
                elif product.current_stock <= product.minimum_stock:
                    stock_status = "BAJO"
                    stock_color = "orange"
                    low_stock_count += 1

                status_item = QTableWidgetItem(stock_status)
                from PySide6.QtGui import QColor, QFont
                status_item.setForeground(QColor(stock_color))
                font = QFont()
                font.setBold(True)
                status_item.setFont(font)
                self.inventory_table.setItem(row, 5, status_item)

                # Total value - convert to float to avoid Decimal type issues
                total_product_value = float(product.current_stock or 0) * float(product.sale_price or 0)
                total_value += total_product_value
                value_item = QTableWidgetItem(f"{total_product_value:.2f} €")
                self.inventory_table.setItem(row, 6, value_item)

                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(2, 2, 2, 2)

                adjust_btn = QPushButton("📊")
                adjust_btn.setToolTip("Ajustar Stock")
                adjust_btn.setMaximumSize(30, 25)
                adjust_btn.clicked.connect(lambda checked, p=product: self.adjust_product_stock(p))
                actions_layout.addWidget(adjust_btn)

                edit_btn = QPushButton("✏️")
                edit_btn.setToolTip("Editar Producto")
                edit_btn.setMaximumSize(30, 25)
                edit_btn.clicked.connect(lambda checked, p=product: self.edit_product(p))
                actions_layout.addWidget(edit_btn)

                self.inventory_table.setCellWidget(row, 7, actions_widget)

                # Last movement
                last_movement = "N/A"
                if hasattr(product, 'updated_at') and product.updated_at:
                    last_movement = product.updated_at.strftime('%Y-%m-%d %H:%M')
                self.inventory_table.setItem(row, 8, QTableWidgetItem(last_movement))

            self.inventory_table.setSortingEnabled(True)

            # Update statistics
            self.total_products_label.setText(f"Total: {len(products)}")
            self.low_stock_label.setText(f"Stock Bajo: {low_stock_count}")
            self.total_value_label.setText(f"Valor Total: {total_value:.2f} €")

            self.status_label.setText(f"Mostrando {len(products)} productos - {low_stock_count} con stock bajo")
    
    def filter_products(self):
        """Filter products based on search and filter criteria"""
        search_text = self.search_edit.text().lower()
        filter_type = self.filter_combo.currentText()
        
        for row in range(self.inventory_table.rowCount()):
            visible = True
            
            # Apply text search
            if search_text:
                found = False
                for col in range(self.inventory_table.columnCount()):
                    item = self.inventory_table.item(row, col)
                    if item and search_text in item.text().lower():
                        found = True
                        break
                if not found:
                    visible = False
            
            # Apply filter criteria
            if visible:
                stock_item = self.inventory_table.item(row, 3)
                min_stock_item = self.inventory_table.item(row, 4)
                status_item = self.inventory_table.item(row, 5)
                
                if stock_item and min_stock_item and status_item:
                    stock = int(stock_item.text() or 0)
                    min_stock = int(min_stock_item.text() or 0)
                    status = status_item.text()
                    
                    if filter_type == "Con Stock" and stock <= 0:
                        visible = False
                    elif filter_type == "Stock Bajo" and stock > min_stock:
                        visible = False
                    elif filter_type == "Sin Stock" and stock > 0:
                        visible = False
                    elif filter_type == "Activos" and "Activo" not in status:
                        visible = False
                    elif filter_type == "Inactivos" and "Activo" in status:
                        visible = False
            
            self.inventory_table.setRowHidden(row, not visible)
    
    def add_product(self):
        """Add new product to inventory"""
        dialog = ProductDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
    
    def adjust_stock(self):
        """General stock adjustment dialog - improved UX"""
        current_row = self.inventory_table.currentRow()
        app_mode = get_app_mode()

        # If no row selected, show product picker dialog
        if current_row < 0:
            if app_mode.is_remote:
                self.show_product_picker_for_adjustment_remote()
            else:
                self.show_product_picker_for_adjustment()
            return

        # If row selected, adjust that product directly
        if current_row >= len(self._inventory_products):
            QMessageBox.warning(self, "Error", "Producto no encontrado")
            return
        self.adjust_product_stock(self._inventory_products[current_row])

    def show_product_picker_for_adjustment(self):
        """Show a dialog to pick a product for stock adjustment"""
        try:
            with SessionLocal() as db:
                products = db.query(Product).filter(Product.is_active == True).order_by(Product.name).all()

                if not products:
                    QMessageBox.information(self, "Info", "No hay productos activos en el inventario")
                    return

                # Create custom product selection dialog
                picker_dialog = QDialog(self)
                picker_dialog.setWindowTitle("Seleccionar Producto")
                picker_dialog.setModal(True)
                picker_dialog.resize(500, 400)
                picker_dialog.setStyleSheet(UIStyles.get_dialog_style() + UIStyles.get_input_style())

                layout = QVBoxLayout(picker_dialog)
                layout.setSpacing(16)
                layout.setContentsMargins(24, 24, 24, 24)

                # Label
                label = QLabel("Seleccione el producto para ajustar stock:")
                label.setStyleSheet(UIStyles.get_label_style())
                layout.addWidget(label)

                # Product list
                product_list = QListWidget()
                product_list.setStyleSheet(f"""
                    QListWidget {{
                        background-color: {UIStyles.COLORS['bg_card']};
                        border: 1px solid {UIStyles.COLORS['border']};
                        border-radius: 8px;
                        padding: 8px;
                    }}
                    QListWidget::item {{
                        padding: 10px;
                        border-bottom: 1px solid {UIStyles.COLORS['border_light']};
                    }}
                    QListWidget::item:selected {{
                        background-color: {UIStyles.COLORS['accent']};
                        color: white;
                    }}
                    QListWidget::item:hover {{
                        background-color: {UIStyles.COLORS['bg_hover']};
                    }}
                """)

                # Store product data for later access
                product_data = {}
                for p in products:
                    item_text = f"{p.code} - {p.name} (Stock: {p.current_stock or 0})"
                    product_list.addItem(item_text)
                    product_data[item_text] = p.code

                layout.addWidget(product_list)

                # Buttons
                button_layout = QHBoxLayout()
                button_layout.addStretch()

                cancel_btn = QPushButton("Cancelar")
                cancel_btn.setStyleSheet(UIStyles.get_secondary_button_style())
                cancel_btn.clicked.connect(picker_dialog.reject)
                button_layout.addWidget(cancel_btn)

                select_btn = QPushButton("Seleccionar")
                select_btn.setStyleSheet(UIStyles.get_primary_button_style())

                def on_select():
                    current_item = product_list.currentItem()
                    if current_item:
                        product_code = product_data.get(current_item.text())
                        if product_code:
                            picker_dialog.accept()
                            # Get fresh product from DB
                            with SessionLocal() as db2:
                                product = db2.query(Product).filter(Product.code == product_code).first()
                                if product:
                                    self.adjust_product_stock(product)
                    else:
                        QMessageBox.warning(picker_dialog, "Aviso", "Seleccione un producto primero")

                select_btn.clicked.connect(on_select)
                product_list.itemDoubleClicked.connect(lambda: on_select())
                button_layout.addWidget(select_btn)

                layout.addLayout(button_layout)
                picker_dialog.exec()

        except Exception as e:
            logger.error(f"Error showing product picker: {e}")
            QMessageBox.critical(self, "Error", f"Error al mostrar selector de productos: {str(e)}")

    def show_product_picker_for_adjustment_remote(self):
        """Show a dialog to pick a product for stock adjustment (remote)."""
        try:
            app_mode = get_app_mode()
            response = app_mode.api.list_products(limit=500)
            products = response.get("items", [])

            if not products:
                QMessageBox.information(self, "Info", "No hay productos activos en el inventario")
                return

            picker_dialog = QDialog(self)
            picker_dialog.setWindowTitle("Seleccionar Producto")
            picker_dialog.setModal(True)
            picker_dialog.resize(500, 400)
            picker_dialog.setStyleSheet(UIStyles.get_dialog_style() + UIStyles.get_input_style())

            layout = QVBoxLayout(picker_dialog)
            layout.setSpacing(16)
            layout.setContentsMargins(24, 24, 24, 24)

            label = QLabel("Seleccione el producto para ajustar stock:")
            label.setStyleSheet(UIStyles.get_label_style())
            layout.addWidget(label)

            product_list = QListWidget()
            product_list.setStyleSheet(f"""
                QListWidget {{
                    background-color: {UIStyles.COLORS['bg_card']};
                    border: 1px solid {UIStyles.COLORS['border']};
                    border-radius: 8px;
                    padding: 8px;
                }}
                QListWidget::item {{
                    padding: 10px;
                    border-bottom: 1px solid {UIStyles.COLORS['border_light']};
                }}
                QListWidget::item:selected {{
                    background-color: {UIStyles.COLORS['accent']};
                    color: white;
                }}
                QListWidget::item:hover {{
                    background-color: {UIStyles.COLORS['bg_hover']};
                }}
            """)

            product_data = {}
            for p in products:
                item_text = f"{p.get('code', '')} - {p.get('name', '')} (Stock: {p.get('current_stock', 0)})"
                product_list.addItem(item_text)
                product_data[item_text] = p

            layout.addWidget(product_list)

            button_layout = QHBoxLayout()
            button_layout.addStretch()

            cancel_btn = QPushButton("Cancelar")
            cancel_btn.setStyleSheet(UIStyles.get_secondary_button_style())
            cancel_btn.clicked.connect(picker_dialog.reject)
            button_layout.addWidget(cancel_btn)

            select_btn = QPushButton("Seleccionar")
            select_btn.setStyleSheet(UIStyles.get_primary_button_style())

            def on_select():
                current_item = product_list.currentItem()
                if current_item:
                    product = product_data.get(current_item.text())
                    if product:
                        picker_dialog.accept()
                        self.adjust_product_stock(product)
                else:
                    QMessageBox.warning(picker_dialog, "Aviso", "Seleccione un producto primero")

            select_btn.clicked.connect(on_select)
            product_list.itemDoubleClicked.connect(lambda: on_select())
            button_layout.addWidget(select_btn)

            layout.addLayout(button_layout)
            picker_dialog.exec()

        except Exception as e:
            logger.error(f"Error showing product picker (remote): {e}")
            QMessageBox.critical(self, "Error", f"Error al mostrar selector de productos: {str(e)}")
    
    def adjust_product_stock(self, product):
        """Adjust stock for specific product - improved with custom dialog"""
        app_mode = get_app_mode()
        is_remote = app_mode.is_remote or isinstance(product, dict)

        # Store product info to avoid detached session issues
        if isinstance(product, dict):
            product_id = product.get("id")
            product_name = product.get("name", "")
            current_stock = product.get("current_stock", 0) or 0
        else:
            product_id = product.id
            product_name = product.name
            current_stock = product.current_stock or 0

        # Create custom adjustment dialog
        adjust_dialog = QDialog(self)
        adjust_dialog.setWindowTitle("Ajustar Stock")
        adjust_dialog.setModal(True)
        adjust_dialog.resize(400, 300)
        adjust_dialog.setStyleSheet(UIStyles.get_dialog_style() + UIStyles.get_input_style())

        layout = QVBoxLayout(adjust_dialog)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Product info
        info_label = QLabel(f"Producto: {product_name}")
        info_label.setStyleSheet(f"font-weight: 600; font-size: 15px; color: {UIStyles.COLORS['text_primary']};")
        layout.addWidget(info_label)

        stock_label = QLabel(f"Stock actual: {current_stock} unidades")
        stock_label.setStyleSheet(UIStyles.get_label_style())
        layout.addWidget(stock_label)

        # Instructions
        instructions = QLabel("Ajuste de cantidad:\n  + Positivo para entrada (añadir stock)\n  - Negativo para salida (retirar stock)")
        instructions.setStyleSheet(f"color: {UIStyles.COLORS['text_secondary']}; font-size: 12px;")
        layout.addWidget(instructions)

        # Quantity input
        quantity_layout = QHBoxLayout()
        quantity_label = QLabel("Cantidad:")
        quantity_label.setStyleSheet(UIStyles.get_label_style())
        quantity_layout.addWidget(quantity_label)

        quantity_spin = QSpinBox()
        quantity_spin.setRange(-9999, 9999)
        quantity_spin.setValue(0)
        quantity_spin.setMinimumWidth(120)
        quantity_layout.addWidget(quantity_spin)
        quantity_layout.addStretch()

        layout.addLayout(quantity_layout)
        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        cancel_btn.clicked.connect(adjust_dialog.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Aplicar Ajuste")
        save_btn.setStyleSheet(UIStyles.get_primary_button_style())

        def apply_adjustment():
            quantity = quantity_spin.value()
            if quantity == 0:
                QMessageBox.information(adjust_dialog, "Info", "No se realizaron cambios (cantidad = 0)")
                return

            try:
                if is_remote:
                    updated = app_mode.api.adjust_stock(str(product_id), quantity, "Ajuste manual")
                    old_stock = current_stock
                    new_stock = updated.get("current_stock", old_stock + quantity)

                    movement_type = "Entrada" if quantity > 0 else "Salida"
                    adjust_dialog.accept()
                    QMessageBox.information(
                        self, "Exito",
                        f"Stock ajustado correctamente\n\n"
                        f"Producto: {product_name}\n"
                        f"Stock anterior: {old_stock}\n"
                        f"Stock nuevo: {new_stock}\n"
                        f"Operacion: {movement_type} de {abs(quantity)} unidades"
                    )
                    logger.info(f"Stock adjusted (remote): {product_name} from {old_stock} to {new_stock} ({quantity:+d})")
                    self.refresh_data()
                else:
                    with SessionLocal() as db:
                        db_product = db.query(Product).filter(Product.id == product_id).first()
                        if not db_product:
                            QMessageBox.warning(adjust_dialog, "Error", "Producto no encontrado")
                            return

                        old_stock = db_product.current_stock or 0
                        new_stock = max(0, old_stock + quantity)

                        # Validate the operation
                        if quantity < 0 and abs(quantity) > old_stock:
                            reply = QMessageBox.question(
                                adjust_dialog,
                                "Confirmar Operacion",
                                f"La cantidad a retirar ({abs(quantity)}) es mayor que el stock actual ({old_stock}).\n"
                                f"El stock resultante sera 0.\n\n"
                                f"¿Desea continuar?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.No
                            )
                            if reply != QMessageBox.StandardButton.Yes:
                                return

                        db_product.current_stock = new_stock
                        db.commit()

                        movement_type = "Entrada" if quantity > 0 else "Salida"
                        adjust_dialog.accept()
                        QMessageBox.information(
                            self, "Exito",
                            f"Stock ajustado correctamente\n\n"
                            f"Producto: {product_name}\n"
                            f"Stock anterior: {old_stock}\n"
                            f"Stock nuevo: {new_stock}\n"
                            f"Operacion: {movement_type} de {abs(quantity)} unidades"
                        )
                        logger.info(f"Stock adjusted: {product_name} from {old_stock} to {new_stock} ({quantity:+d})")
                        self.refresh_data()

            except Exception as e:
                logger.error(f"Error adjusting stock: {e}")
                error_msg = str(e)
                if hasattr(e, 'detail') and e.detail:
                    error_msg = e.detail
                QMessageBox.critical(adjust_dialog, "Error", f"Error al ajustar stock: {error_msg}")

        save_btn.clicked.connect(apply_adjustment)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)
        adjust_dialog.exec()
    
    def edit_product(self, product):
        """Edit product details using ProductDialog"""
        if isinstance(product, dict):
            product_id = product.get("id")
            product_name = product.get("name", "")
        else:
            product_id = product.id
            product_name = product.name
        dialog = ProductDialog(self, product_id=product_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
            QMessageBox.information(self, "Exito", f"Producto '{product_name}' actualizado correctamente")
    
    def generate_report(self):
        """Generate inventory report"""
        try:
            app_mode = get_app_mode()
            if app_mode.is_remote:
                response = app_mode.api.list_products(limit=500)
                products = response.get("items", [])
            else:
                with SessionLocal() as db:
                    products = db.query(Product).all()

            report = "📊 INFORME DE INVENTARIO\n"
            report += "=" * 50 + "\n"
            report += f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

            if app_mode.is_remote:
                total_products = len(products)
                low_stock = sum(1 for p in products if (p.get("current_stock", 0) or 0) <= (p.get("minimum_stock", 0) or 0))
                out_of_stock = sum(1 for p in products if (p.get("current_stock", 0) or 0) <= 0)
                total_value = sum((p.get("current_stock", 0) or 0) * (p.get("sale_price", 0) or 0) for p in products)
            else:
                total_products = len(products)
                low_stock = sum(1 for p in products if p.current_stock <= p.minimum_stock)
                out_of_stock = sum(1 for p in products if p.current_stock <= 0)
                total_value = sum((p.current_stock or 0) * (p.sale_price or 0) for p in products)

            report += f"📦 Total Productos: {total_products}\n"
            report += f"⚠️ Stock Bajo: {low_stock}\n"
            report += f"❌ Sin Stock: {out_of_stock}\n"
            report += f"💰 Valor Total Inventario: {total_value:.2f} €\n\n"

            report += "DETALLE DE PRODUCTOS CON STOCK BAJO:\n"
            report += "-" * 40 + "\n"

            if app_mode.is_remote:
                for product in products:
                    current_stock = product.get("current_stock", 0) or 0
                    minimum_stock = product.get("minimum_stock", 0) or 0
                    if current_stock <= minimum_stock:
                        report += f"• {product.get('name', '')}: {current_stock} (mín: {minimum_stock})\n"
            else:
                for product in products:
                    if product.current_stock <= product.minimum_stock:
                        report += f"• {product.name}: {product.current_stock} (mín: {product.minimum_stock})\n"

            # Show report in dialog
            report_dialog = QDialog(self)
            report_dialog.setWindowTitle("📊 Informe de Inventario")
            report_dialog.setModal(True)
            report_dialog.resize(600, 500)

            layout = QVBoxLayout(report_dialog)

            report_text = QTextEdit()
            report_text.setPlainText(report)
            report_text.setReadOnly(True)
            layout.addWidget(report_text)

            close_btn = QPushButton("❌ Cerrar")
            close_btn.clicked.connect(report_dialog.accept)
            layout.addWidget(close_btn)

            report_dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error generando informe: {str(e)}")

    def retranslate_ui(self):
        """Update all translatable text"""
        # Update title
        if hasattr(self, 'title_label'):
            self.title_label.setText(translator.t("inventory.title"))
        
        # Update buttons
        if hasattr(self, 'add_btn'):
            self.add_btn.setText(translator.t("buttons.new_product"))
        if hasattr(self, 'adjust_stock_btn'):
            self.adjust_stock_btn.setText(translator.t("buttons.adjust_stock"))
        if hasattr(self, 'generate_report_btn'):
            self.generate_report_btn.setText(translator.t("buttons.report"))
        if hasattr(self, 'refresh_btn'):
            self.refresh_btn.setText(translator.t("buttons.refresh"))
        
        # Update search and filter
        if hasattr(self, 'search_label'):
            self.search_label.setText(translator.t("buttons.search") + ":")
        if hasattr(self, 'search_edit'):
            self.search_edit.setPlaceholderText(translator.t("inventory.search_placeholder"))
        if hasattr(self, 'filter_label'):
            self.filter_label.setText(translator.t("inventory.filter") + ":")
        
        if hasattr(self, 'filter_combo'):
            current_text = self.filter_combo.currentText()
            self.filter_combo.clear()
            self.filter_combo.addItems([
                translator.t("inventory.all_items"),
                translator.t("inventory.in_stock"),
                translator.t("inventory.low_stock"),
                translator.t("inventory.out_of_stock"),
                translator.t("inventory.active_only"),
                translator.t("inventory.inactive_only")
            ])
            # Try to restore previous selection
            index = self.filter_combo.findText(current_text)
            if index >= 0:
                self.filter_combo.setCurrentIndex(index)
        
        # Update table headers
        if hasattr(self, 'inventory_table'):
            self.inventory_table.setHorizontalHeaderLabels([
                translator.t("inventory.code"), translator.t("inventory.product"), translator.t("inventory.description"),
                translator.t("inventory.current_stock"), translator.t("inventory.minimum_stock"), translator.t("inventory.status"),
                translator.t("inventory.total_value"), translator.t("inventory.actions"), translator.t("inventory.last_movement")
            ])

class DiaryManagementTab(QWidget):
    """Modern diary management tab with Apple-inspired design"""

    def __init__(self):
        super().__init__()
        self.translatable_widgets = {}
        self.notes = []
        self.setup_ui()
        self.load_notes()
        # Display notes immediately after loading
        self.refresh_notes()

    def setup_ui(self):
        self.setStyleSheet(UIStyles.get_panel_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        self.title_label = QLabel(translator.t("diary.title"))
        self.title_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 600;
            color: {UIStyles.COLORS['text_primary']};
            background: transparent;
        """)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(12)

        self.add_entry_btn = QPushButton(translator.t("diary.new_entry"))
        self.add_entry_btn.clicked.connect(self.add_entry)
        self.add_entry_btn.setStyleSheet(UIStyles.get_primary_button_style())
        toolbar_layout.addWidget(self.add_entry_btn)

        self.view_calendar_btn = QPushButton(translator.t("diary.view_calendar"))
        self.view_calendar_btn.clicked.connect(self.view_calendar)
        self.view_calendar_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        toolbar_layout.addWidget(self.view_calendar_btn)

        self.new_reminder_btn = QPushButton("Nuevo Recordatorio")
        self.new_reminder_btn.clicked.connect(self.add_reminder)
        self.new_reminder_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        toolbar_layout.addWidget(self.new_reminder_btn)

        self.view_reminders_btn = QPushButton("Ver Recordatorios")
        self.view_reminders_btn.clicked.connect(self.view_reminders)
        self.view_reminders_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        toolbar_layout.addWidget(self.view_reminders_btn)

        toolbar_layout.addStretch()

        self.clear_all_btn = QPushButton(translator.t("diary.clear_all"))
        self.clear_all_btn.clicked.connect(self.clear_all)
        self.clear_all_btn.setStyleSheet(UIStyles.get_danger_button_style())
        toolbar_layout.addWidget(self.clear_all_btn)

        layout.addLayout(toolbar_layout)

        # Date selector
        date_layout = QHBoxLayout()
        date_layout.setSpacing(12)

        self.date_label = QLabel(translator.t("diary.date") + ":")
        self.date_label.setStyleSheet(UIStyles.get_label_style())
        date_layout.addWidget(self.date_label)

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setStyleSheet(UIStyles.get_input_style())
        self.date_edit.dateChanged.connect(self.filter_notes_by_date)
        date_layout.addWidget(self.date_edit)

        self.today_btn = QPushButton(translator.t("diary.today"))
        self.today_btn.clicked.connect(lambda: self.date_edit.setDate(QDate.currentDate()))
        self.today_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        date_layout.addWidget(self.today_btn)

        date_layout.addStretch()
        layout.addLayout(date_layout)

        # Notes container
        notes_frame = QFrame()
        notes_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {UIStyles.COLORS['bg_card']};
                border: 1px solid {UIStyles.COLORS['border_light']};
                border-radius: 12px;
            }}
        """)
        notes_frame_layout = QVBoxLayout(notes_frame)
        notes_frame_layout.setContentsMargins(20, 20, 20, 20)

        notes_title = QLabel("Notas del Diario")
        notes_title.setStyleSheet(UIStyles.get_section_title_style())
        notes_frame_layout.addWidget(notes_title)

        self.notes_list = QTextEdit()
        self.notes_list.setReadOnly(True)
        self.notes_list.setPlaceholderText("Las notas del diario aparecerán aquí...")
        self.notes_list.setStyleSheet(f"""
            QTextEdit {{
                border: none;
                background: transparent;
                color: {UIStyles.COLORS['text_primary']};
                font-size: 14px;
                line-height: 1.6;
            }}
        """)
        notes_frame_layout.addWidget(self.notes_list)

        layout.addWidget(notes_frame)

        # Statistics
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self.total_notes_label = QLabel("Total Notas: 0")
        self.total_notes_label.setStyleSheet(f"""
            background-color: {UIStyles.COLORS['bg_card']};
            border: 1px solid {UIStyles.COLORS['border_light']};
            border-radius: 8px;
            padding: 12px 20px;
            font-weight: 500;
            color: {UIStyles.COLORS['text_primary']};
        """)
        stats_layout.addWidget(self.total_notes_label)

        self.today_notes_label = QLabel("Notas Hoy: 0")
        self.today_notes_label.setStyleSheet(f"""
            background-color: {UIStyles.COLORS['bg_card']};
            border: 1px solid {UIStyles.COLORS['accent']};
            border-radius: 8px;
            padding: 12px 20px;
            font-weight: 500;
            color: {UIStyles.COLORS['accent']};
        """)
        stats_layout.addWidget(self.today_notes_label)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Status label
        self.status_label = QLabel("Haz clic en 'Nueva Nota' para añadir apuntes")
        self.status_label.setStyleSheet(UIStyles.get_status_label_style())
        layout.addWidget(self.status_label)
    
    def add_entry(self):
        """Add new diary entry"""
        dialog = DiaryEntryDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            note_data = dialog.get_note_data()
            if note_data:
                app_mode = get_app_mode()
                if app_mode.is_remote:
                    try:
                        if not note_data.get('content'):
                            QMessageBox.warning(self, "Error", "El contenido es obligatorio en modo remoto")
                            return
                        entry_date = f"{note_data['date']}T{note_data['time']}:00"
                        import json as _json
                        app_mode.api.create_diary_entry(
                            title=note_data['title'],
                            content=note_data['content'],
                            entry_date=entry_date,
                            tags=_json.dumps(note_data.get('tags', []))
                        )
                        self.refresh_notes()
                        self.status_label.setText(f"✅ Nota guardada: {note_data['title']}")
                    except Exception as e:
                        error_msg = str(e)
                        if hasattr(e, 'detail') and e.detail:
                            error_msg = e.detail
                        QMessageBox.critical(self, "Error", f"Error al guardar: {error_msg}")
                else:
                    self.notes.append(note_data)
                    self.save_notes()
                    self.refresh_notes()
                    self.status_label.setText(f"✅ Nota guardada: {note_data['title']}")
    
    def view_calendar(self):
        """View calendar with notes"""
        from PySide6.QtWidgets import QCalendarWidget

        # Create calendar dialog
        calendar_dialog = QDialog(self)
        calendar_dialog.setWindowTitle("📅 Calendario de Notas")
        calendar_dialog.setModal(True)
        calendar_dialog.resize(600, 500)

        layout = QVBoxLayout(calendar_dialog)

        # Calendar widget
        calendar = QCalendarWidget()
        calendar.setGridVisible(True)

        # Highlight dates with notes
        from PySide6.QtGui import QTextCharFormat, QColor
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor(0, 122, 255, 50))  # Light blue

        for note in self.notes:
            try:
                note_date = QDate.fromString(note['date'], 'yyyy-MM-dd')
                if note_date.isValid():
                    calendar.setDateTextFormat(note_date, highlight_format)
            except:
                pass

        # Connect date selection to jump to that date
        def on_date_selected(date):
            self.date_edit.setDate(date)
            calendar_dialog.accept()

        calendar.clicked.connect(on_date_selected)
        layout.addWidget(calendar)

        # Info label
        info_label = QLabel("Las fechas resaltadas tienen notas. Haga clic en una fecha para ver sus notas.")
        info_label.setStyleSheet(UIStyles.get_status_label_style())
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Close button
        close_btn = QPushButton("Cerrar")
        close_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        close_btn.clicked.connect(calendar_dialog.accept)
        layout.addWidget(close_btn)

        calendar_dialog.exec()

    def add_reminder(self):
        """Add a new reminder"""
        reminder_dialog = QDialog(self)
        reminder_dialog.setWindowTitle("Nuevo Recordatorio")
        reminder_dialog.setModal(True)
        reminder_dialog.resize(450, 350)
        reminder_dialog.setStyleSheet(UIStyles.get_dialog_style() + UIStyles.get_input_style())

        layout = QVBoxLayout(reminder_dialog)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        # Title
        title_edit = QLineEdit()
        title_edit.setPlaceholderText("Titulo del recordatorio...")
        form_layout.addRow("Titulo:", title_edit)

        # Description
        description_edit = QTextEdit()
        description_edit.setPlaceholderText("Descripcion (opcional)...")
        description_edit.setMaximumHeight(80)
        form_layout.addRow("Descripcion:", description_edit)

        # Due date
        due_date_edit = QDateEdit()
        due_date_edit.setDate(QDate.currentDate())
        due_date_edit.setCalendarPopup(True)
        form_layout.addRow("Fecha:", due_date_edit)

        # Priority
        priority_combo = QComboBox()
        priority_combo.addItems(["Normal", "Alta", "Baja"])
        form_layout.addRow("Prioridad:", priority_combo)

        layout.addLayout(form_layout)
        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        cancel_btn.clicked.connect(reminder_dialog.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Guardar")
        save_btn.setStyleSheet(UIStyles.get_primary_button_style())

        def save_reminder():
            title = title_edit.text().strip()
            if not title:
                QMessageBox.warning(reminder_dialog, "Error", "El titulo es obligatorio")
                return

            priority_map = {"Normal": "normal", "Alta": "high", "Baja": "low"}
            priority = priority_map.get(priority_combo.currentText(), "normal")

            try:
                app_mode = get_app_mode()
                qdate = due_date_edit.date()
                due_date = datetime(qdate.year(), qdate.month(), qdate.day()).isoformat()

                if app_mode.is_remote:
                    app_mode.api.create_reminder(
                        title=title,
                        description=description_edit.toPlainText().strip() or None,
                        due_date=due_date,
                        priority=priority
                    )
                else:
                    with SessionLocal() as db:
                        reminder = Reminder(
                            title=title,
                            description=description_edit.toPlainText().strip() or None,
                            due_date=datetime(qdate.year(), qdate.month(), qdate.day()),
                            priority=priority,
                            is_completed=False,
                        )
                        db.add(reminder)
                        db.commit()

                reminder_dialog.accept()
                show_toast(self, "Recordatorio guardado correctamente", "success")
                # Sync with dashboard
                self._sync_dashboard()
            except Exception as e:
                logger.error(f"Error saving reminder: {e}")
                error_msg = str(e)
                if hasattr(e, 'detail') and e.detail:
                    error_msg = e.detail
                QMessageBox.critical(reminder_dialog, "Error", f"Error al guardar: {error_msg}")

        save_btn.clicked.connect(save_reminder)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)
        reminder_dialog.exec()

    def _sync_dashboard(self):
        """Sync changes with the Dashboard panel"""
        try:
            parent = self.parent()
            while parent is not None:
                if hasattr(parent, 'dashboard') and parent.dashboard:
                    parent.dashboard.refresh_data()
                    break
                parent = parent.parent()
        except Exception as e:
            logger.warning(f"Could not sync with dashboard: {e}")

    def view_reminders(self):
        """View all reminders in a list dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Recordatorios")
        dialog.setModal(True)
        dialog.resize(600, 450)
        dialog.setStyleSheet(UIStyles.get_dialog_style())

        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("Lista de Recordatorios")
        title.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {UIStyles.COLORS['text_primary']};")
        layout.addWidget(title)

        # Table
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Titulo", "Fecha", "Prioridad", "Estado", "Acciones"])
        table.setStyleSheet(UIStyles.get_table_style())
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(4, 120)

        # Load reminders
        try:
            app_mode = get_app_mode()
            if app_mode.is_remote:
                response = app_mode.api.list_reminders(pending_only=False)
                reminders = response.get("items", [])

                for row, r in enumerate(reminders):
                    table.insertRow(row)
                    table.setItem(row, 0, QTableWidgetItem(r.get("title", "")))

                    date_str = "Sin fecha"
                    due_date = r.get("due_date")
                    if due_date:
                        try:
                            if isinstance(due_date, str):
                                due_date = due_date.replace("Z", "+00:00")
                                dt = datetime.fromisoformat(due_date)
                            else:
                                dt = due_date
                            date_str = dt.strftime('%d/%m/%Y')
                        except Exception:
                            pass
                    table.setItem(row, 1, QTableWidgetItem(date_str))

                    priority_map = {"high": "Alta", "normal": "Normal", "low": "Baja"}
                    table.setItem(row, 2, QTableWidgetItem(priority_map.get(r.get("priority"), "Normal")))

                    is_completed = r.get("is_completed", False)
                    status = "Completado" if is_completed else "Pendiente"
                    status_item = QTableWidgetItem(status)
                    if is_completed:
                        status_item.setForeground(QColor("#34C759"))
                    else:
                        status_item.setForeground(QColor("#FF9500"))
                    table.setItem(row, 3, status_item)

                    actions = QWidget()
                    actions_layout = QHBoxLayout(actions)
                    actions_layout.setContentsMargins(2, 2, 2, 2)

                    complete_btn = QPushButton("✓" if not is_completed else "↩")
                    complete_btn.setToolTip("Marcar completado" if not is_completed else "Desmarcar")
                    complete_btn.setFixedSize(28, 24)
                    rid = r.get("id")
                    complete_btn.clicked.connect(lambda _, rid=rid, done=is_completed: self._toggle_reminder(rid, dialog, table, done))
                    actions_layout.addWidget(complete_btn)

                    del_btn = QPushButton("🗑")
                    del_btn.setToolTip("Eliminar")
                    del_btn.setFixedSize(28, 24)
                    del_btn.clicked.connect(lambda _, rid=rid: self._delete_reminder(rid, dialog, table))
                    actions_layout.addWidget(del_btn)

                    table.setCellWidget(row, 4, actions)
            else:
                with SessionLocal() as db:
                    reminders = db.query(Reminder).order_by(
                        Reminder.is_completed.asc(),
                        Reminder.due_date.asc().nullslast()
                    ).all()

                    for row, r in enumerate(reminders):
                        table.insertRow(row)
                        table.setItem(row, 0, QTableWidgetItem(r.title))
                        date_str = r.due_date.strftime('%d/%m/%Y') if r.due_date else "Sin fecha"
                        table.setItem(row, 1, QTableWidgetItem(date_str))
                        priority_map = {"high": "Alta", "normal": "Normal", "low": "Baja"}
                        table.setItem(row, 2, QTableWidgetItem(priority_map.get(r.priority, "Normal")))
                        status = "Completado" if r.is_completed else "Pendiente"
                        status_item = QTableWidgetItem(status)
                        if r.is_completed:
                            status_item.setForeground(QColor("#34C759"))
                        else:
                            status_item.setForeground(QColor("#FF9500"))
                        table.setItem(row, 3, status_item)

                        # Action buttons
                        actions = QWidget()
                        actions_layout = QHBoxLayout(actions)
                        actions_layout.setContentsMargins(2, 2, 2, 2)

                        complete_btn = QPushButton("✓" if not r.is_completed else "↩")
                        complete_btn.setToolTip("Marcar completado" if not r.is_completed else "Desmarcar")
                        complete_btn.setFixedSize(28, 24)
                        rid = r.id
                        complete_btn.clicked.connect(lambda _, rid=rid: self._toggle_reminder(rid, dialog, table))
                        actions_layout.addWidget(complete_btn)

                        del_btn = QPushButton("🗑")
                        del_btn.setToolTip("Eliminar")
                        del_btn.setFixedSize(28, 24)
                        del_btn.clicked.connect(lambda _, rid=rid: self._delete_reminder(rid, dialog, table))
                        actions_layout.addWidget(del_btn)

                        table.setCellWidget(row, 4, actions)

        except Exception as e:
            logger.error(f"Error loading reminders: {e}")

        layout.addWidget(table)

        # Close button
        close_btn = QPushButton("Cerrar")
        close_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()
        self._sync_dashboard()

    def _toggle_reminder(self, reminder_id, dialog, table, is_completed=None):
        """Toggle reminder completed status"""
        try:
            app_mode = get_app_mode()
            if app_mode.is_remote:
                new_value = not bool(is_completed)
                app_mode.api.update_reminder(str(reminder_id), is_completed=new_value)
            else:
                with SessionLocal() as db:
                    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
                    if reminder:
                        reminder.is_completed = not reminder.is_completed
                        db.commit()
            dialog.accept()
            self.view_reminders()
        except Exception as e:
            logger.error(f"Error toggling reminder: {e}")

    def _delete_reminder(self, reminder_id, dialog, table):
        """Delete a reminder"""
        reply = QMessageBox.question(self, "Confirmar", "¿Eliminar este recordatorio?")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                app_mode = get_app_mode()
                if app_mode.is_remote:
                    app_mode.api.delete_reminder(str(reminder_id))
                else:
                    with SessionLocal() as db:
                        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
                        if reminder:
                            db.delete(reminder)
                            db.commit()
                dialog.accept()
                self.view_reminders()
            except Exception as e:
                logger.error(f"Error deleting reminder: {e}")

    def clear_all(self):
        """Clear all notes"""
        reply = QMessageBox.question(
            self, "❌ Confirmar Eliminación", 
            "¿Está seguro de eliminar TODAS las notas del diario?\n\nEsta acción no se puede deshacer."
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            app_mode = get_app_mode()
            if app_mode.is_remote:
                try:
                    for note in self.notes:
                        if note.get("id"):
                            app_mode.api.delete_diary_entry(str(note["id"]))
                    self.refresh_notes()
                    self.status_label.setText("🗑️ Todas las notas han sido eliminadas")
                except Exception as e:
                    error_msg = str(e)
                    if hasattr(e, 'detail') and e.detail:
                        error_msg = e.detail
                    QMessageBox.critical(self, "Error", f"Error al eliminar: {error_msg}")
            else:
                self.notes = []
                self.save_notes()
                self.refresh_notes()
                self.status_label.setText("🗑️ Todas las notas han sido eliminadas")
    
    def filter_notes_by_date(self):
        """Filter notes by selected date"""
        self.refresh_notes()
    
    def load_notes(self):
        """Load notes from file"""
        try:
            app_mode = get_app_mode()
            if app_mode.is_remote:
                self._load_notes_remote()
                return
            import json
            notes_file = os.path.join(os.path.dirname(__file__), 'diary_notes.json')
            if os.path.exists(notes_file):
                with open(notes_file, 'r', encoding='utf-8') as f:
                    self.notes = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Error loading diary notes: {e}")
            self.notes = []

    def _load_notes_remote(self):
        """Load notes from remote API."""
        try:
            app_mode = get_app_mode()
            response = app_mode.api.list_diary_entries(limit=500)
            items = response.get("items", [])
            notes = []
            for entry in items:
                entry_date = entry.get("entry_date")
                date_str = ""
                time_str = ""
                if entry_date:
                    try:
                        if isinstance(entry_date, str):
                            entry_date = entry_date.replace("Z", "+00:00")
                            dt = datetime.fromisoformat(entry_date)
                        else:
                            dt = entry_date
                        date_str = dt.strftime('%Y-%m-%d')
                        time_str = dt.strftime('%H:%M')
                    except Exception:
                        pass
                tags_raw = entry.get("tags") or "[]"
                tags = []
                try:
                    import json as _json
                    if isinstance(tags_raw, str):
                        tags = _json.loads(tags_raw)
                except Exception:
                    tags = []
                notes.append({
                    "id": entry.get("id"),
                    "title": entry.get("title", ""),
                    "content": entry.get("content", ""),
                    "date": date_str,
                    "time": time_str,
                    "tags": tags
                })
            self.notes = notes
        except Exception as e:
            logger.error(f"Error loading diary notes (remote): {e}")
            self.notes = []
    
    def save_notes(self):
        """Save notes to file"""
        try:
            app_mode = get_app_mode()
            if app_mode.is_remote:
                return
            import json
            notes_file = os.path.join(os.path.dirname(__file__), 'diary_notes.json')
            with open(notes_file, 'w', encoding='utf-8') as f:
                json.dump(self.notes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error guardando notas: {str(e)}")
    
    def refresh_notes(self):
        """Refresh notes display"""
        selected_date = self.date_edit.date().toString('yyyy-MM-dd')
        
        display_text = f"📅 Notas para {selected_date}:\n"
        display_text += "=" * 50 + "\n\n"
        
        # Reload notes from file to get latest data
        self.load_notes()
        
        filtered_notes = [
            note for note in self.notes 
            if note['date'] == selected_date
        ]
        
        if filtered_notes:
            for i, note in enumerate(filtered_notes, 1):
                display_text += f"{i}. 📌 {note['title']}\n"
                display_text += f"   🕐 {note['time']}\n"
                display_text += f"   📝 {note['content']}\n"
                if note.get('tags'):
                    display_text += f"   🏷️  {', '.join(note['tags'])}\n"
                display_text += "-" * 30 + "\n\n"
        else:
            display_text += "No hay notas para esta fecha.\n\n"
            display_text += "💡 Tip: Usa 'Nueva Nota' para añadir una entrada."
        
        self.notes_list.setPlainText(display_text)
        
        # Update statistics
        from datetime import datetime
        today = QDate.currentDate().toString('yyyy-MM-dd')
        today_notes = [note for note in self.notes if note['date'] == today]
        
        self.total_notes_label.setText(f"📊 {translator.t('diary.total_notes')}: {len(self.notes)}")
        self.today_notes_label.setText(f"📅 {translator.t('diary.today_notes')}: {len(today_notes)}")

    def retranslate_ui(self):
        """Update all translatable text"""
        # Update title
        if hasattr(self, 'title_label'):
            self.title_label.setText(translator.t("diary.title"))
        
        # Update buttons
        if hasattr(self, 'add_entry_btn'):
            self.add_entry_btn.setText(translator.t("diary.new_entry"))
        if hasattr(self, 'view_calendar_btn'):
            self.view_calendar_btn.setText(translator.t("diary.view_calendar"))
        if hasattr(self, 'clear_all_btn'):
            self.clear_all_btn.setText(translator.t("diary.clear_all"))
        if hasattr(self, 'today_btn'):
            self.today_btn.setText(translator.t("diary.today"))
        
        # Update date label
        if hasattr(self, 'date_label'):
            self.date_label.setText(translator.t("diary.date") + ":")
        
        # Update empty state text
        if hasattr(self, 'empty_state_label'):
            self.empty_state_label.setText(translator.t("diary.empty_state"))
        if hasattr(self, 'empty_state_hint'):
            self.empty_state_hint.setText(translator.t("diary.empty_state_hint"))
        
        # Update statistics
        if hasattr(self, 'total_notes_label'):
            self.total_notes_label.setText(f"📊 {translator.t('diary.total_notes')}: {len(self.notes)}")
        if hasattr(self, 'today_notes_label'):
            today_notes = [n for n in self.notes if n['date'] == QDate.currentDate().toString('yyyy-MM-dd')]
            self.today_notes_label.setText(f"📅 {translator.t('diary.today_notes')}: {len(today_notes)}")

class DiaryEntryDialog(QDialog):
    """Dialog for creating new diary entries"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📝 Nueva Nota del Diario")
        self.setModal(True)
        self.resize(600, 500)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("📌 Título de la nota")
        layout.addWidget(QLabel("Título:"))
        layout.addWidget(self.title_edit)
        
        # Content
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("📝 Escribe el contenido de tu nota aquí...")
        layout.addWidget(QLabel("Contenido:"))
        layout.addWidget(self.content_edit)
        
        # Tags
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("🏷️ Etiquetas (separadas por comas: trabajo, importante, etc.)")
        layout.addWidget(QLabel("Etiquetas:"))
        layout.addWidget(self.tags_edit)
        
        # Date and time
        datetime_layout = QHBoxLayout()
        
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        datetime_layout.addWidget(QLabel("📅 Fecha:"))
        datetime_layout.addWidget(self.date_edit)
        
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime.currentTime())
        datetime_layout.addWidget(QLabel("🕐 Hora:"))
        datetime_layout.addWidget(self.time_edit)
        
        layout.addLayout(datetime_layout)
        
        # Priority
        priority_layout = QHBoxLayout()
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["🟢 Normal", "🟡 Importante", "🔴 Urgente"])
        priority_layout.addWidget(QLabel("🎯 Prioridad:"))
        priority_layout.addWidget(self.priority_combo)
        priority_layout.addStretch()
        layout.addLayout(priority_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Guardar Nota")
        save_btn.clicked.connect(self.accept)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #229954; }
        """)
        buttons_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def get_note_data(self):
        """Get note data from form"""
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "❌ Error", "El título es obligatorio")
            return None
        
        return {
            'title': self.title_edit.text().strip(),
            'content': self.content_edit.toPlainText().strip(),
            'date': self.date_edit.date().toString('yyyy-MM-dd'),
            'time': self.time_edit.time().toString('HH:mm'),
            'priority': self.priority_combo.currentText(),
            'tags': [tag.strip() for tag in self.tags_edit.text().split(',') if tag.strip()]
        }

# Add missing import for QTimeEdit and QTime
from PySide6.QtWidgets import QTimeEdit
from PySide6.QtCore import QTime


class WorkersManagementTab(QWidget):
    """Workers management tab with Apple-inspired design - supports local and remote modes"""

    def __init__(self):
        super().__init__()
        self.translatable_widgets = {}
        self.worker_ids = []
        self.setup_ui()
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self.refresh_data)

    def setup_ui(self):
        self.setStyleSheet(UIStyles.get_panel_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        self.title_label = QLabel(translator.t("workers.title"))
        self.title_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 600;
            color: {UIStyles.COLORS['text_primary']};
            background: transparent;
        """)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(12)

        self.add_btn = QPushButton(translator.t("workers.new_worker"))
        self.add_btn.clicked.connect(self.add_worker)
        self.add_btn.setStyleSheet(UIStyles.get_primary_button_style())
        toolbar_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton(translator.t("buttons.edit"))
        self.edit_btn.clicked.connect(self.edit_worker)
        self.edit_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        toolbar_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton(translator.t("buttons.delete"))
        self.delete_btn.clicked.connect(self.delete_worker)
        self.delete_btn.setStyleSheet(UIStyles.get_danger_button_style())
        toolbar_layout.addWidget(self.delete_btn)

        toolbar_layout.addStretch()

        self.refresh_btn = QPushButton(translator.t("buttons.refresh"))
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.refresh_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        toolbar_layout.addWidget(self.refresh_btn)

        layout.addLayout(toolbar_layout)

        # Search
        search_layout = QHBoxLayout()
        search_layout.setSpacing(12)

        self.search_label = QLabel(translator.t("buttons.search") + ":")
        self.search_label.setStyleSheet(UIStyles.get_label_style())
        search_layout.addWidget(self.search_label)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(translator.t("workers.search_placeholder"))
        self.search_edit.setStyleSheet(UIStyles.get_input_style())
        self.search_edit.textChanged.connect(self.filter_workers)
        search_layout.addWidget(self.search_edit)

        # Department filter
        self.department_combo = QComboBox()
        self.department_combo.addItem(translator.t("workers.all_departments"))
        self.department_combo.setStyleSheet(UIStyles.get_input_style())
        self.department_combo.currentIndexChanged.connect(self.filter_workers)
        search_layout.addWidget(self.department_combo)

        layout.addLayout(search_layout)

        # Table
        self.workers_table = QTableWidget()
        self.workers_table.setColumnCount(8)
        self.workers_table.setHorizontalHeaderLabels([
            translator.t("workers.code"),
            translator.t("workers.first_name"),
            translator.t("workers.last_name"),
            translator.t("workers.position"),
            translator.t("workers.department"),
            translator.t("workers.email"),
            translator.t("workers.phone"),
            translator.t("workers.active")
        ])
        self.workers_table.setStyleSheet(UIStyles.get_table_style())
        self.workers_table.setAlternatingRowColors(False)
        self.workers_table.setShowGrid(False)
        self.workers_table.verticalHeader().setVisible(False)
        self.workers_table.setSortingEnabled(True)
        self.workers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.workers_table.doubleClicked.connect(self.edit_worker)

        header = self.workers_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.workers_table)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(UIStyles.get_status_label_style())
        layout.addWidget(self.status_label)

    def refresh_data(self):
        """Refresh workers data - supports local and remote modes"""
        self.worker_ids = []
        app_mode = get_app_mode()

        try:
            if app_mode.is_remote:
                self._refresh_from_api(app_mode.api)
            else:
                self._refresh_from_local()
        except Exception as e:
            logger.error(f"Error refreshing workers: {e}")
            self.status_label.setText(f"Error: {str(e)}")

    def _refresh_from_api(self, api):
        """Refresh workers from remote API (with cache fallback)."""
        try:
            response = api.list_workers(limit=500)
            workers = response.get("items", [])
            from_cache = response.get("_from_cache", False)

            self.workers_table.setSortingEnabled(False)
            self.workers_table.setRowCount(0)
            self.worker_ids = []

            # Collect departments for filter
            departments = set()

            for row, worker in enumerate(workers):
                self.workers_table.insertRow(row)
                self.worker_ids.append(worker.get("id", ""))

                self.workers_table.setItem(row, 0, QTableWidgetItem(worker.get("code", "")))
                self.workers_table.setItem(row, 1, QTableWidgetItem(worker.get("first_name", "")))
                self.workers_table.setItem(row, 2, QTableWidgetItem(worker.get("last_name", "")))
                self.workers_table.setItem(row, 3, QTableWidgetItem(worker.get("position", "") or ""))
                dept = worker.get("department", "") or ""
                self.workers_table.setItem(row, 4, QTableWidgetItem(dept))
                if dept:
                    departments.add(dept)
                self.workers_table.setItem(row, 5, QTableWidgetItem(worker.get("email", "") or ""))
                self.workers_table.setItem(row, 6, QTableWidgetItem(worker.get("phone", "") or ""))

                is_active = worker.get("is_active", True)
                status_text = "Activo" if is_active else "Inactivo"
                self.workers_table.setItem(row, 7, QTableWidgetItem(status_text))

            self.workers_table.setSortingEnabled(True)
            # Update department filter
            self._update_department_filter(departments)
            source = "(cache - sin conexion)" if from_cache else "(servidor)"
            self.status_label.setText(f"Mostrando {len(workers)} trabajadores {source}")

        except Exception as e:
            logger.error(f"Error fetching workers from API: {e}")
            raise

    def _refresh_from_local(self):
        """Refresh workers from local SQLite database."""
        with SessionLocal() as db:
            workers = db.query(Worker).order_by(Worker.last_name, Worker.first_name).all()

            self.workers_table.setSortingEnabled(False)
            self.workers_table.setRowCount(0)
            self.worker_ids = []

            # Collect departments for filter
            departments = set()

            for row, worker in enumerate(workers):
                self.workers_table.insertRow(row)
                self.worker_ids.append(worker.id)

                self.workers_table.setItem(row, 0, QTableWidgetItem(worker.code or ""))
                self.workers_table.setItem(row, 1, QTableWidgetItem(worker.first_name or ""))
                self.workers_table.setItem(row, 2, QTableWidgetItem(worker.last_name or ""))
                self.workers_table.setItem(row, 3, QTableWidgetItem(worker.position or ""))
                dept = worker.department or ""
                self.workers_table.setItem(row, 4, QTableWidgetItem(dept))
                if dept:
                    departments.add(dept)
                self.workers_table.setItem(row, 5, QTableWidgetItem(worker.email or ""))
                self.workers_table.setItem(row, 6, QTableWidgetItem(worker.phone or ""))

                status_text = "Activo" if worker.is_active else "Inactivo"
                self.workers_table.setItem(row, 7, QTableWidgetItem(status_text))

            self.workers_table.setSortingEnabled(True)
            # Update department filter
            self._update_department_filter(departments)
            self.status_label.setText(f"Mostrando {len(workers)} trabajadores (local)")

    def _update_department_filter(self, departments: set):
        """Update department filter combo box."""
        current_text = self.department_combo.currentText()
        self.department_combo.blockSignals(True)
        self.department_combo.clear()
        self.department_combo.addItem(translator.t("workers.all_departments"))
        for dept in sorted(departments):
            self.department_combo.addItem(dept)
        # Restore selection if possible
        idx = self.department_combo.findText(current_text)
        if idx >= 0:
            self.department_combo.setCurrentIndex(idx)
        self.department_combo.blockSignals(False)

    def filter_workers(self):
        """Filter workers based on search text and department."""
        search_text = self.search_edit.text().lower()
        selected_dept = self.department_combo.currentText()
        all_depts = translator.t("workers.all_departments")

        for row in range(self.workers_table.rowCount()):
            visible = True

            # Check search text
            if search_text:
                text_match = False
                for col in range(self.workers_table.columnCount()):
                    item = self.workers_table.item(row, col)
                    if item and search_text in item.text().lower():
                        text_match = True
                        break
                visible = text_match

            # Check department filter
            if visible and selected_dept != all_depts:
                dept_item = self.workers_table.item(row, 4)
                if dept_item and dept_item.text() != selected_dept:
                    visible = False

            self.workers_table.setRowHidden(row, not visible)

    def add_worker(self):
        """Add new worker."""
        dialog = WorkerDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
            show_toast(self, "Trabajador creado correctamente", "success")

    def edit_worker(self):
        """Edit selected worker."""
        current_row = self.workers_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Seleccione un trabajador para editar")
            return

        if current_row >= len(self.worker_ids):
            QMessageBox.warning(self, "Error", "Error al obtener datos del trabajador")
            return

        worker_id = self.worker_ids[current_row]
        dialog = WorkerDialog(self, worker_id=worker_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
            show_toast(self, "Trabajador actualizado correctamente", "success")

    def delete_worker(self):
        """Delete selected worker - supports local and remote modes."""
        current_row = self.workers_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Seleccione un trabajador para eliminar")
            return

        if current_row >= len(self.worker_ids):
            QMessageBox.warning(self, "Error", "Error al obtener datos del trabajador")
            return

        first_name = self.workers_table.item(current_row, 1).text()
        last_name = self.workers_table.item(current_row, 2).text()
        worker_name = f"{first_name} {last_name}"
        worker_id = self.worker_ids[current_row]

        dialog = ConfirmationDialog(
            self,
            title="Confirmar Eliminacion",
            message=f"¿Seguro de eliminar '{worker_name}'?\n\nEsta accion no se puede deshacer.",
            confirm_text="Eliminar",
            is_danger=True
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            app_mode = get_app_mode()
            try:
                if app_mode.is_remote:
                    app_mode.api.delete_worker(str(worker_id))
                    self.refresh_data()
                    QMessageBox.information(self, "Exito", f"Trabajador '{worker_name}' eliminado")
                else:
                    with SessionLocal() as db:
                        worker = db.query(Worker).filter(Worker.id == worker_id).first()
                        if worker:
                            worker.is_active = False
                            db.commit()
                            self.refresh_data()
                            QMessageBox.information(self, "Exito", f"Trabajador '{worker_name}' eliminado")
            except Exception as e:
                logger.error(f"Error deleting worker: {e}")
                error_msg = str(e)
                if hasattr(e, 'detail') and e.detail:
                    error_msg = e.detail
                QMessageBox.critical(self, "Error", f"Error al eliminar: {error_msg}")

    def retranslate_ui(self):
        """Update all translatable text."""
        if hasattr(self, 'title_label'):
            self.title_label.setText(translator.t("workers.title"))
        if hasattr(self, 'add_btn'):
            self.add_btn.setText(translator.t("workers.new_worker"))
        if hasattr(self, 'edit_btn'):
            self.edit_btn.setText(translator.t("buttons.edit"))
        if hasattr(self, 'delete_btn'):
            self.delete_btn.setText(translator.t("buttons.delete"))
        if hasattr(self, 'refresh_btn'):
            self.refresh_btn.setText(translator.t("buttons.refresh"))
        if hasattr(self, 'search_label'):
            self.search_label.setText(translator.t("buttons.search") + ":")


class WorkerDialog(QDialog):
    """Dialog for creating/editing workers - supports local and remote modes."""

    def __init__(self, parent=None, worker_id=None):
        super().__init__(parent)
        self.worker_id = worker_id
        self.is_edit_mode = worker_id is not None
        self.setWindowTitle("Editar Trabajador" if self.is_edit_mode else "Nuevo Trabajador")
        self.setModal(True)
        self.resize(550, 500)
        self.setStyleSheet(UIStyles.get_dialog_style())
        self.setup_ui()
        if self.is_edit_mode:
            self.load_worker_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        # Code
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("Ej: TRB-001")
        self.code_edit.setStyleSheet(UIStyles.get_input_style())
        form_layout.addRow("Codigo*:", self.code_edit)

        # First name
        self.first_name_edit = QLineEdit()
        self.first_name_edit.setPlaceholderText("Nombre")
        self.first_name_edit.setStyleSheet(UIStyles.get_input_style())
        form_layout.addRow("Nombre*:", self.first_name_edit)

        # Last name
        self.last_name_edit = QLineEdit()
        self.last_name_edit.setPlaceholderText("Apellido")
        self.last_name_edit.setStyleSheet(UIStyles.get_input_style())
        form_layout.addRow("Apellido*:", self.last_name_edit)

        # Position
        self.position_edit = QLineEdit()
        self.position_edit.setPlaceholderText("Ej: Desarrollador, Gerente...")
        self.position_edit.setStyleSheet(UIStyles.get_input_style())
        form_layout.addRow("Cargo:", self.position_edit)

        # Department
        self.department_edit = QLineEdit()
        self.department_edit.setPlaceholderText("Ej: IT, Ventas, RRHH...")
        self.department_edit.setStyleSheet(UIStyles.get_input_style())
        form_layout.addRow("Departamento:", self.department_edit)

        # Email
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("email@empresa.com")
        self.email_edit.setStyleSheet(UIStyles.get_input_style())
        form_layout.addRow("Email:", self.email_edit)

        # Phone
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("+34 612 345 678")
        self.phone_edit.setStyleSheet(UIStyles.get_input_style())
        form_layout.addRow("Telefono:", self.phone_edit)

        # Address
        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("Direccion completa")
        self.address_edit.setStyleSheet(UIStyles.get_input_style())
        form_layout.addRow("Direccion:", self.address_edit)

        # Hire date
        self.hire_date_edit = QDateEdit()
        self.hire_date_edit.setDate(QDate.currentDate())
        self.hire_date_edit.setCalendarPopup(True)
        self.hire_date_edit.setStyleSheet(UIStyles.get_input_style())
        form_layout.addRow("Fecha contratacion:", self.hire_date_edit)

        # Salary
        self.salary_edit = QLineEdit()
        self.salary_edit.setPlaceholderText("0.00")
        self.salary_edit.setStyleSheet(UIStyles.get_input_style())
        form_layout.addRow("Salario:", self.salary_edit)

        # Active
        self.active_check = QCheckBox("Activo")
        self.active_check.setChecked(True)
        form_layout.addRow("", self.active_check)

        layout.addLayout(form_layout)
        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Guardar")
        save_btn.setStyleSheet(UIStyles.get_primary_button_style())
        save_btn.clicked.connect(self.save_worker)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def load_worker_data(self):
        """Load worker data for editing."""
        app_mode = get_app_mode()
        try:
            if app_mode.is_remote:
                worker = app_mode.api.get_worker(str(self.worker_id))
                self.code_edit.setText(worker.get("code", ""))
                self.first_name_edit.setText(worker.get("first_name", ""))
                self.last_name_edit.setText(worker.get("last_name", ""))
                self.position_edit.setText(worker.get("position", "") or "")
                self.department_edit.setText(worker.get("department", "") or "")
                self.email_edit.setText(worker.get("email", "") or "")
                self.phone_edit.setText(worker.get("phone", "") or "")
                self.address_edit.setText(worker.get("address", "") or "")
                self.active_check.setChecked(worker.get("is_active", True))
                # Handle hire_date
                hire_date = worker.get("hire_date")
                if hire_date:
                    try:
                        if isinstance(hire_date, str):
                            dt = datetime.fromisoformat(hire_date.replace("Z", "+00:00"))
                            self.hire_date_edit.setDate(QDate(dt.year, dt.month, dt.day))
                    except Exception:
                        pass
                # Handle salary
                salary = worker.get("salary")
                if salary is not None:
                    self.salary_edit.setText(str(salary))
            else:
                with SessionLocal() as db:
                    worker = db.query(Worker).filter(Worker.id == self.worker_id).first()
                    if worker:
                        self.code_edit.setText(worker.code or "")
                        self.first_name_edit.setText(worker.first_name or "")
                        self.last_name_edit.setText(worker.last_name or "")
                        self.position_edit.setText(worker.position or "")
                        self.department_edit.setText(worker.department or "")
                        self.email_edit.setText(worker.email or "")
                        self.phone_edit.setText(worker.phone or "")
                        self.address_edit.setText(worker.address or "")
                        self.active_check.setChecked(worker.is_active)
                        if worker.hire_date:
                            self.hire_date_edit.setDate(QDate(
                                worker.hire_date.year,
                                worker.hire_date.month,
                                worker.hire_date.day
                            ))
                        if worker.salary is not None:
                            self.salary_edit.setText(str(worker.salary))
        except Exception as e:
            logger.error(f"Error loading worker data: {e}")
            QMessageBox.critical(self, "Error", f"Error al cargar datos: {str(e)}")

    def save_worker(self):
        """Save worker - supports local and remote modes."""
        # Validate required fields
        code = self.code_edit.text().strip()
        first_name = self.first_name_edit.text().strip()
        last_name = self.last_name_edit.text().strip()

        if not code:
            QMessageBox.warning(self, "Error", "El codigo es obligatorio")
            return
        if not first_name:
            QMessageBox.warning(self, "Error", "El nombre es obligatorio")
            return
        if not last_name:
            QMessageBox.warning(self, "Error", "El apellido es obligatorio")
            return

        # Parse salary
        salary = None
        salary_text = self.salary_edit.text().strip()
        if salary_text:
            try:
                salary = float(salary_text.replace(",", "."))
            except ValueError:
                QMessageBox.warning(self, "Error", "El salario debe ser un numero valido")
                return

        # Get hire date
        qdate = self.hire_date_edit.date()
        hire_date = datetime(qdate.year(), qdate.month(), qdate.day())

        app_mode = get_app_mode()
        try:
            if app_mode.is_remote:
                data = {
                    "code": code,
                    "first_name": first_name,
                    "last_name": last_name,
                    "position": self.position_edit.text().strip() or None,
                    "department": self.department_edit.text().strip() or None,
                    "email": self.email_edit.text().strip() or None,
                    "phone": self.phone_edit.text().strip() or None,
                    "address": self.address_edit.text().strip() or None,
                    "hire_date": hire_date.isoformat(),
                    "salary": salary,
                    "is_active": self.active_check.isChecked()
                }
                if self.is_edit_mode:
                    app_mode.api.update_worker(str(self.worker_id), **data)
                else:
                    app_mode.api.create_worker(**data)
            else:
                with SessionLocal() as db:
                    if self.is_edit_mode:
                        worker = db.query(Worker).filter(Worker.id == self.worker_id).first()
                        if worker:
                            worker.code = code
                            worker.first_name = first_name
                            worker.last_name = last_name
                            worker.full_name = f"{first_name} {last_name}"
                            worker.position = self.position_edit.text().strip() or None
                            worker.department = self.department_edit.text().strip() or None
                            worker.email = self.email_edit.text().strip() or None
                            worker.phone = self.phone_edit.text().strip() or None
                            worker.address = self.address_edit.text().strip() or None
                            worker.hire_date = hire_date
                            worker.salary = salary
                            worker.is_active = self.active_check.isChecked()
                    else:
                        worker = Worker(
                            code=code,
                            first_name=first_name,
                            last_name=last_name,
                            full_name=f"{first_name} {last_name}",
                            position=self.position_edit.text().strip() or None,
                            department=self.department_edit.text().strip() or None,
                            email=self.email_edit.text().strip() or None,
                            phone=self.phone_edit.text().strip() or None,
                            address=self.address_edit.text().strip() or None,
                            hire_date=hire_date,
                            salary=salary,
                            is_active=self.active_check.isChecked()
                        )
                        db.add(worker)
                    db.commit()
            self.accept()
        except Exception as e:
            logger.error(f"Error saving worker: {e}")
            error_msg = str(e)
            if hasattr(e, 'detail') and e.detail:
                error_msg = e.detail
            QMessageBox.critical(self, "Error", f"Error al guardar: {error_msg}")


class MainWindow(QMainWindow):
    """Modern Apple-inspired main window"""

    def __init__(self):
        super().__init__()
        self.current_user = None
        self._load_theme()
        self.setup_ui()

    def set_current_user(self, user):
        """Set current user"""
        self.current_user = user
        username = user.username
        full_name = user.full_name
        role = user.role.value if hasattr(user.role, 'value') else str(user.role)

        self.user_label.setText(f"{full_name} ({role})")
        self.statusBar().showMessage("Listo")

    def _load_theme(self):
        """Load saved theme preference."""
        try:
            theme_path = Path.home() / ".dragofactu" / "theme.json"
            if theme_path.exists():
                with open(theme_path) as f:
                    data = json.load(f)
                theme = data.get("theme", "Claro")
                UIStyles.set_dark_mode(theme == "Oscuro")
        except Exception:
            pass

    def _setup_shortcuts(self):
        """Setup additional keyboard shortcuts."""
        from PySide6.QtGui import QShortcut, QKeySequence

        # Ctrl+1..7 → switch tabs
        for i in range(min(7, self.tabs.count())):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{i+1}"), self)
            shortcut.activated.connect(lambda idx=i: self.tabs.setCurrentIndex(idx))

        # F5 → refresh current tab
        refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        refresh_shortcut.activated.connect(self._refresh_current_tab)

        # Ctrl+N → new element (context-dependent)
        new_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        new_shortcut.activated.connect(self._new_element_for_current_tab)

        # Ctrl+F → focus search bar in current tab
        search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        search_shortcut.activated.connect(self._focus_search)

        # Escape → close dialogs / clear search
        esc_shortcut = QShortcut(QKeySequence("Escape"), self)
        esc_shortcut.activated.connect(self._handle_escape)

    def _refresh_current_tab(self):
        """Refresh the data of the currently active tab."""
        tab = self.tabs.currentWidget()
        if hasattr(tab, 'refresh_data'):
            tab.refresh_data()
            show_toast(self, "Datos actualizados", "info", 1500)

    def _new_element_for_current_tab(self):
        """Trigger new element creation based on the active tab."""
        idx = self.tabs.currentIndex()
        tab = self.tabs.currentWidget()
        if idx == 1 and hasattr(tab, 'add_client'):  # Clients
            tab.add_client()
        elif idx == 2 and hasattr(tab, 'add_product'):  # Products
            tab.add_product()
        elif idx == 3:  # Documents
            self.new_invoice()
        elif idx == 5 and hasattr(tab, 'add_entry'):  # Diary
            tab.add_entry()
        elif idx == 6 and hasattr(tab, 'add_worker'):  # Workers
            tab.add_worker()

    def _focus_search(self):
        """Focus the search bar in the current tab."""
        tab = self.tabs.currentWidget()
        if hasattr(tab, 'search_input'):
            tab.search_input.setFocus()
            tab.search_input.selectAll()

    def _handle_escape(self):
        """Handle Escape key: clear search or deselect."""
        tab = self.tabs.currentWidget()
        if hasattr(tab, 'search_input') and tab.search_input.text():
            tab.search_input.clear()
            if hasattr(tab, 'refresh_data'):
                tab.refresh_data()

    def _apply_theme(self):
        """Re-apply the current theme stylesheet to the main window."""
        self.setStyleSheet(self._build_main_stylesheet())
        # Refresh tab panels
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if hasattr(w, 'setStyleSheet'):
                w.setStyleSheet(UIStyles.get_panel_style())

    def _build_main_stylesheet(self):
        """Build the main window stylesheet from current UIStyles colors."""
        return f"""
            QMainWindow {{
                background-color: {UIStyles.COLORS['bg_app']};
            }}
            QMenuBar {{
                background-color: {UIStyles.COLORS['bg_card']};
                border-bottom: 1px solid {UIStyles.COLORS['border_light']};
                padding: 4px 8px;
                font-size: 13px;
            }}
            QMenuBar::item {{
                background-color: transparent;
                padding: 6px 12px;
                border-radius: 4px;
                color: {UIStyles.COLORS['text_primary']};
            }}
            QMenuBar::item:selected {{
                background-color: {UIStyles.COLORS['bg_hover']};
            }}
            QMenu {{
                background-color: {UIStyles.COLORS['bg_card']};
                border: 1px solid {UIStyles.COLORS['border']};
                border-radius: 8px;
                padding: 4px 0;
            }}
            QMenu::item {{
                padding: 8px 24px;
                color: {UIStyles.COLORS['text_primary']};
            }}
            QMenu::item:selected {{
                background-color: {UIStyles.COLORS['accent']};
                color: {UIStyles.COLORS['text_inverse']};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {UIStyles.COLORS['border_light']};
                margin: 4px 8px;
            }}
            QStatusBar {{
                background-color: {UIStyles.COLORS['bg_card']};
                border-top: 1px solid {UIStyles.COLORS['border_light']};
                padding: 4px 12px;
                font-size: 12px;
                color: {UIStyles.COLORS['text_secondary']};
            }}
            QTabWidget::pane {{
                background-color: transparent;
                border: none;
            }}
            QTabBar {{
                background-color: transparent;
            }}
            QTabBar::tab {{
                background-color: transparent;
                border: none;
                padding: 12px 20px;
                margin-right: 4px;
                color: {UIStyles.COLORS['text_secondary']};
                font-weight: 500;
                font-size: 13px;
            }}
            QTabBar::tab:selected {{
                color: {UIStyles.COLORS['accent']};
                border-bottom: 2px solid {UIStyles.COLORS['accent']};
            }}
            QTabBar::tab:hover:!selected {{
                color: {UIStyles.COLORS['text_primary']};
            }}
        """

    def setup_ui(self):
        """Setup modern main window"""
        self.setWindowTitle("Dragofactu - Sistema de Gestión")
        self.setGeometry(100, 100, 1400, 900)

        # Apply main window style (theme-aware)
        self.setStyleSheet(self._build_main_stylesheet())

        # Create menu bar
        self.create_menu()

        # Create central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tab widget
        self.tabs = QTabWidget()

        # Dashboard tab
        self.dashboard = Dashboard()
        self.tabs.addTab(self.dashboard, translator.t("tabs.dashboard"))

        # Add functional tabs
        self.clients_tab = ClientManagementTab()
        self.tabs.addTab(self.clients_tab, translator.t("tabs.clients"))

        self.products_tab = ProductManagementTab()
        self.tabs.addTab(self.products_tab, translator.t("tabs.products"))

        self.documents_tab = DocumentManagementTab()
        self.tabs.addTab(self.documents_tab, translator.t("tabs.documents"))

        self.inventory_tab = InventoryManagementTab()
        self.tabs.addTab(self.inventory_tab, translator.t("tabs.inventory"))

        self.diary_tab = DiaryManagementTab()
        self.tabs.addTab(self.diary_tab, translator.t("tabs.diary"))

        self.workers_tab = WorkersManagementTab()
        self.tabs.addTab(self.workers_tab, translator.t("tabs.workers"))

        layout.addWidget(self.tabs)

        # Create status bar with user info and connectivity indicator
        status_bar = self.statusBar()

        # Connectivity indicator
        self.connectivity_label = QLabel("")
        self.connectivity_label.setStyleSheet(f"color: {UIStyles.COLORS['text_secondary']}; padding-right: 8px;")
        status_bar.addPermanentWidget(self.connectivity_label)

        # Pending operations indicator
        self.pending_ops_label = QLabel("")
        self.pending_ops_label.setStyleSheet(f"color: {UIStyles.COLORS['warning']}; padding-right: 8px;")
        self.pending_ops_label.setVisible(False)
        status_bar.addPermanentWidget(self.pending_ops_label)

        self.user_label = QLabel("")
        self.user_label.setStyleSheet(f"color: {UIStyles.COLORS['text_secondary']}; padding-right: 16px;")
        status_bar.addPermanentWidget(self.user_label)
        status_bar.showMessage(translator.t("status.ready"))

        # Setup connectivity monitoring
        self._setup_connectivity_monitor()

        # Setup keyboard shortcuts
        self._setup_shortcuts()

        # Connect tab changes to refresh data
        self.tabs.currentChanged.connect(self.on_tab_changed)
    
    def _setup_connectivity_monitor(self):
        """Setup connectivity monitoring for offline/online status."""
        app_mode = get_app_mode()
        if not app_mode.is_remote:
            self.connectivity_label.setText("Modo local")
            return

        try:
            from dragofactu.services.offline_cache import get_connectivity_monitor, get_operation_queue
            monitor = get_connectivity_monitor()
            monitor.add_listener(self._on_connectivity_changed)
            # Initial check
            if app_mode.api:
                monitor.check_now(app_mode.api)
            self._update_connectivity_ui()
            self._update_pending_ops_ui()
        except Exception as e:
            logger.warning(f"Error setting up connectivity monitor: {e}")

    def _on_connectivity_changed(self, is_online: bool):
        """Callback when connectivity status changes."""
        try:
            from PySide6.QtCore import QMetaObject, Qt as QtCore_Qt, Q_ARG
            # Use invokeMethod for thread safety (monitor may call from bg thread)
            QMetaObject.invokeMethod(self, "_update_connectivity_ui", QtCore_Qt.ConnectionType.QueuedConnection)
            if is_online:
                QMetaObject.invokeMethod(self, "_try_auto_sync", QtCore_Qt.ConnectionType.QueuedConnection)
        except Exception as e:
            logger.warning(f"Error handling connectivity change: {e}")

    def _update_connectivity_ui(self):
        """Update status bar connectivity indicator."""
        app_mode = get_app_mode()
        if not app_mode.is_remote:
            self.connectivity_label.setText("Modo local")
            self.connectivity_label.setStyleSheet(f"color: {UIStyles.COLORS['text_secondary']}; padding-right: 8px;")
            return

        try:
            from dragofactu.services.offline_cache import get_connectivity_monitor
            monitor = get_connectivity_monitor()
            if monitor.is_online:
                self.connectivity_label.setText("En linea")
                self.connectivity_label.setStyleSheet(f"color: {UIStyles.COLORS['success']}; font-weight: 500; padding-right: 8px;")
            else:
                self.connectivity_label.setText("Sin conexion (cache)")
                self.connectivity_label.setStyleSheet(f"color: {UIStyles.COLORS['warning']}; font-weight: 500; padding-right: 8px;")
        except Exception:
            pass

    def _update_pending_ops_ui(self):
        """Update pending operations indicator in status bar."""
        try:
            from dragofactu.services.offline_cache import get_operation_queue
            queue = get_operation_queue()
            count = queue.pending_count
            if count > 0:
                self.pending_ops_label.setText(f"Pendientes: {count}")
                self.pending_ops_label.setVisible(True)
            else:
                self.pending_ops_label.setVisible(False)
        except Exception:
            self.pending_ops_label.setVisible(False)

    def _try_auto_sync(self):
        """Auto-sync pending operations when back online."""
        self.sync_pending_operations(silent=True)

    def sync_pending_operations(self, silent=False):
        """Sync pending offline operations with the server."""
        app_mode = get_app_mode()
        if not app_mode.is_remote or not app_mode.api:
            if not silent:
                QMessageBox.information(self, "Sincronizar", "No hay servidor remoto configurado.")
            return

        try:
            from dragofactu.services.offline_cache import get_operation_queue, get_connectivity_monitor
            queue = get_operation_queue()

            if queue.pending_count == 0:
                if not silent:
                    QMessageBox.information(self, "Sincronizar", "No hay operaciones pendientes.")
                self._update_pending_ops_ui()
                return

            # Check connectivity first
            monitor = get_connectivity_monitor()
            if not monitor.check_now(app_mode.api):
                if not silent:
                    QMessageBox.warning(self, "Sin conexion",
                        "No se puede conectar al servidor. Las operaciones se sincronizaran cuando haya conexion.")
                return

            result = queue.sync(app_mode.api)
            self._update_pending_ops_ui()
            self._update_connectivity_ui()

            if not silent:
                msg = f"Sincronizadas: {result['synced']}"
                if result['failed'] > 0:
                    msg += f"\nFallidas: {result['failed']}"
                if result['remaining'] > 0:
                    msg += f"\nPendientes: {result['remaining']}"
                QMessageBox.information(self, "Sincronizacion", msg)

            # Refresh current tab after sync
            if result['synced'] > 0:
                self._refresh_all_panels()

        except Exception as e:
            if not silent:
                QMessageBox.critical(self, "Error", f"Error al sincronizar: {str(e)}")
            logger.error(f"Error syncing operations: {e}")

    def _clear_cache(self):
        """Clear offline cache."""
        try:
            from dragofactu.services.offline_cache import get_cache
            get_cache().clear()
            show_toast(self, "Cache limpiada correctamente", "info")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al limpiar cache: {str(e)}")

    def on_tab_changed(self, index):
        """Handle tab change to refresh data"""
        tab_widget = self.tabs.widget(index)

        # Always refresh dashboard when switching to it
        if index == 0:  # Dashboard tab
            if hasattr(self.dashboard, 'refresh_data'):
                self.dashboard.refresh_data()
        # Refresh the specific tab when it becomes active
        elif index == 1:  # Clients tab
            if hasattr(tab_widget, 'refresh_data'):
                tab_widget.refresh_data()
        elif index == 2:  # Products tab
            if hasattr(tab_widget, 'refresh_data'):
                tab_widget.refresh_data()

    def create_menu(self):
        """Create clean menu bar with translations"""
        menubar = self.menuBar()

        # File menu
        self.file_menu = menubar.addMenu(translator.t("menu.file"))

        self.new_quote_action = QAction(translator.t("menu.new_quote"), self)
        self.new_quote_action.setShortcut("Ctrl+Shift+P")
        self.new_quote_action.triggered.connect(self.new_quote)
        self.file_menu.addAction(self.new_quote_action)

        self.new_invoice_action = QAction(translator.t("menu.new_invoice"), self)
        self.new_invoice_action.setShortcut("Ctrl+Shift+F")
        self.new_invoice_action.triggered.connect(self.new_invoice)
        self.file_menu.addAction(self.new_invoice_action)

        self.file_menu.addSeparator()

        self.import_action = QAction(translator.t("menu.import") + "...", self)
        self.import_action.setShortcut("Ctrl+I")
        self.import_action.triggered.connect(self.import_external_file)
        self.file_menu.addAction(self.import_action)

        self.export_action = QAction(translator.t("menu.export") + "...", self)
        self.export_action.setShortcut("Ctrl+E")
        self.export_action.triggered.connect(self.export_data)
        self.file_menu.addAction(self.export_action)

        self.export_pdf_action = QAction("PDF...", self)
        self.export_pdf_action.setShortcut("Ctrl+P")
        self.export_pdf_action.triggered.connect(self.export_document_to_pdf)
        self.file_menu.addAction(self.export_pdf_action)

        self.file_menu.addSeparator()

        self.exit_action = QAction(translator.t("menu.exit"), self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)

        # Tools menu
        self.tools_menu = menubar.addMenu(translator.t("menu.tools"))

        self.sync_action = QAction(translator.t("menu.sync"), self)
        self.sync_action.setShortcut("Ctrl+Shift+S")
        self.sync_action.triggered.connect(lambda: self.sync_pending_operations(silent=False))
        self.tools_menu.addAction(self.sync_action)

        self.clear_cache_action = QAction(translator.t("menu.clear_cache"), self)
        self.clear_cache_action.triggered.connect(self._clear_cache)
        self.tools_menu.addAction(self.clear_cache_action)

        self.tools_menu.addSeparator()

        self.settings_action = QAction(translator.t("menu.settings") + "...", self)
        self.settings_action.setShortcut("Ctrl+,")
        self.settings_action.triggered.connect(self.show_settings)
        self.tools_menu.addAction(self.settings_action)

        # Language menu
        self.language_menu = menubar.addMenu(translator.t("menu.language"))

        for lang_code, lang_name in translator.get_available_languages().items():
            lang_action = QAction(lang_name, self)
            lang_action.triggered.connect(lambda checked, code=lang_code: self.change_language(code))
            self.language_menu.addAction(lang_action)
    
    def new_quote(self):
        """Create new quote"""
        dialog = DocumentDialog(self, "quote")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._refresh_all_panels()

    def new_invoice(self):
        """Create new invoice"""
        dialog = DocumentDialog(self, "invoice")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._refresh_all_panels()

    def _refresh_all_panels(self):
        """Refresh all panels after data changes"""
        if hasattr(self, 'dashboard') and self.dashboard:
            self.dashboard.refresh_data()
        if hasattr(self, 'documents_tab') and self.documents_tab:
            self.documents_tab.refresh_data()
        if hasattr(self, 'inventory_tab') and self.inventory_tab:
            self.inventory_tab.refresh_data()

    def export_document_to_pdf(self):
        """Export selected document to PDF - shows document selection dialog"""
        try:
            # Create document selection dialog
            pdf_dialog = QDialog(self)
            pdf_dialog.setWindowTitle("Exportar a PDF")
            pdf_dialog.setModal(True)
            pdf_dialog.resize(500, 400)

            layout = QVBoxLayout(pdf_dialog)

            # Header
            header_label = QLabel("Seleccione un documento para exportar a PDF")
            header_label.setStyleSheet(f"""
                font-size: 14px;
                font-weight: 500;
                color: {UIStyles.COLORS['text_primary']};
                margin-bottom: 12px;
            """)
            layout.addWidget(header_label)

            # Document list
            doc_list = QListWidget()
            doc_list.setStyleSheet(UIStyles.get_input_style())

            with SessionLocal() as db:
                documents = db.query(Document).options(
                    joinedload(Document.client)
                ).order_by(Document.updated_at.desc()).limit(50).all()

                for doc in documents:
                    doc_type_text = {
                        DocumentType.INVOICE: "Factura",
                        DocumentType.QUOTE: "Presupuesto",
                        DocumentType.DELIVERY_NOTE: "Albaran"
                    }.get(doc.type, "Documento")

                    client_name = doc.client.name if doc.client else "Sin cliente"
                    date_str = doc.issue_date.strftime('%d/%m/%Y') if doc.issue_date else ""

                    item_text = f"{doc_type_text} {doc.code} - {client_name} - {date_str} ({doc.total or 0:.2f} EUR)"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.ItemDataRole.UserRole, str(doc.id))
                    doc_list.addItem(item)

            layout.addWidget(doc_list)

            # Buttons
            button_layout = QHBoxLayout()

            export_btn = QPushButton("Exportar PDF")
            export_btn.setStyleSheet(UIStyles.get_primary_button_style())

            def do_export():
                current_item = doc_list.currentItem()
                if not current_item:
                    QMessageBox.warning(pdf_dialog, "Aviso", "Seleccione un documento")
                    return

                doc_id = current_item.data(Qt.ItemDataRole.UserRole)
                pdf_dialog.accept()

                # Generate PDF using documents tab method
                with SessionLocal() as db:
                    doc = db.query(Document).filter(Document.id == doc_id).first()
                    if doc:
                        self.documents_tab.generate_pdf(doc)

            export_btn.clicked.connect(do_export)
            button_layout.addWidget(export_btn)

            cancel_btn = QPushButton("Cancelar")
            cancel_btn.setStyleSheet(UIStyles.get_secondary_button_style())
            cancel_btn.clicked.connect(pdf_dialog.reject)
            button_layout.addWidget(cancel_btn)

            layout.addLayout(button_layout)

            # Double-click to export directly
            doc_list.itemDoubleClicked.connect(lambda: do_export())

            pdf_dialog.exec()

        except Exception as e:
            logger.error(f"Error exporting to PDF: {e}")
            QMessageBox.critical(self, "Error", f"Error al exportar a PDF: {str(e)}")

    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self)
        dialog.exec()

    def change_language(self, lang_code):
        """Change application language and update UI immediately"""
        try:
            lang_names = {'es': 'Español', 'en': 'English', 'de': 'Deutsch'}
            lang_name = lang_names.get(lang_code, lang_code)

            if translator.set_language(lang_code):
                # Update UI immediately
                self.retranslate_ui()

                # Show confirmation in new language
                QMessageBox.information(
                    self,
                    "OK",
                    translator.t("messages.language_changed", lang=lang_name)
                )
            else:
                QMessageBox.warning(self, "Error", f"Language {lang_code} not available")
        except Exception as e:
            logger.error(f"Error changing language: {e}")
            QMessageBox.warning(self, "Error", f"Could not change language: {str(e)}")

    def retranslate_ui(self):
        """Update all UI text to current language"""
        # Window title
        self.setWindowTitle(f"DRAGOFACTU - {translator.t('app.subtitle')}")

        # Update tab names
        self.tabs.setTabText(0, translator.t("tabs.dashboard"))
        self.tabs.setTabText(1, translator.t("tabs.clients"))
        self.tabs.setTabText(2, translator.t("tabs.products"))
        self.tabs.setTabText(3, translator.t("tabs.documents"))
        self.tabs.setTabText(4, translator.t("tabs.inventory"))
        self.tabs.setTabText(5, translator.t("tabs.diary"))

        # Update menus
        self.file_menu.setTitle(translator.t("menu.file"))
        self.tools_menu.setTitle(translator.t("menu.tools"))
        self.language_menu.setTitle(translator.t("menu.language"))

        # Update menu actions
        self.new_quote_action.setText(translator.t("menu.new_quote"))
        self.new_invoice_action.setText(translator.t("menu.new_invoice"))
        self.import_action.setText(translator.t("menu.import") + "...")
        self.export_action.setText(translator.t("menu.export") + "...")
        self.exit_action.setText(translator.t("menu.exit"))
        self.settings_action.setText(translator.t("menu.settings") + "...")

        # Update Dashboard
        if hasattr(self, 'dashboard') and hasattr(self.dashboard, 'retranslate_ui'):
            self.dashboard.retranslate_ui()

        # Update tab content
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if hasattr(tab, 'retranslate_ui'):
                tab.retranslate_ui()

        # Update status bar
        self.statusBar().showMessage(translator.t("status.ready"))

    def import_external_file(self):
        """"Import external files - Fixed QAction/slot mismatch"""
        try:
            from PySide6.QtWidgets import QFileDialog, QMessageBox
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Seleccionar Archivo", "", "Files (*.*)"
            )
            if file_path:
                QMessageBox.information(self, "✅ Importado", f"Archivo: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error: {str(e)}")
    
    def export_data(self):
        """Export application data to CSV/JSON"""
        from PySide6.QtWidgets import QFileDialog

        # Create export dialog
        export_dialog = QDialog(self)
        export_dialog.setWindowTitle("📤 Exportar Datos")
        export_dialog.setModal(True)
        export_dialog.resize(400, 300)

        layout = QVBoxLayout(export_dialog)

        # Export type selection
        type_group = QGroupBox("📋 Seleccione qué exportar")
        type_layout = QVBoxLayout(type_group)

        self.export_clients_check = QCheckBox("👥 Clientes")
        self.export_clients_check.setChecked(True)
        type_layout.addWidget(self.export_clients_check)

        self.export_products_check = QCheckBox("📦 Productos")
        self.export_products_check.setChecked(True)
        type_layout.addWidget(self.export_products_check)

        self.export_documents_check = QCheckBox("📄 Documentos")
        self.export_documents_check.setChecked(True)
        type_layout.addWidget(self.export_documents_check)

        layout.addWidget(type_group)

        # Format selection
        format_group = QGroupBox("📁 Formato de exportación")
        format_layout = QVBoxLayout(format_group)

        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["CSV (Hojas de cálculo)", "JSON (Datos estructurados)"])
        format_layout.addWidget(self.export_format_combo)

        layout.addWidget(format_group)

        # Buttons
        buttons_layout = QHBoxLayout()

        export_btn = QPushButton("📤 Exportar")
        export_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 10px; border-radius: 5px; font-weight: bold;")
        export_btn.clicked.connect(lambda: self.perform_export(export_dialog))
        buttons_layout.addWidget(export_btn)

        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.clicked.connect(export_dialog.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

        export_dialog.exec()

    def perform_export(self, dialog):
        """Perform the actual export"""
        import csv
        import json
        from PySide6.QtWidgets import QFileDialog

        export_clients = self.export_clients_check.isChecked()
        export_products = self.export_products_check.isChecked()
        export_documents = self.export_documents_check.isChecked()
        is_csv = "CSV" in self.export_format_combo.currentText()

        if not any([export_clients, export_products, export_documents]):
            QMessageBox.warning(self, "❌ Error", "Seleccione al menos un tipo de datos para exportar")
            return

        # Get export directory
        export_dir = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Exportación")
        if not export_dir:
            return

        try:
            exported_files = []

            with SessionLocal() as db:
                # Export Clients
                if export_clients:
                    clients = db.query(Client).all()
                    if clients:
                        if is_csv:
                            filepath = os.path.join(export_dir, "clientes.csv")
                            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                                writer = csv.writer(f)
                                writer.writerow(['Código', 'Nombre', 'Email', 'Teléfono', 'Dirección', 'Ciudad', 'C. Postal', 'CIF/NIF', 'Activo'])
                                for c in clients:
                                    writer.writerow([c.code, c.name, c.email or '', c.phone or '', c.address or '', c.city or '', c.postal_code or '', c.tax_id or '', 'Sí' if c.is_active else 'No'])
                        else:
                            filepath = os.path.join(export_dir, "clientes.json")
                            data = [{'codigo': c.code, 'nombre': c.name, 'email': c.email, 'telefono': c.phone, 'direccion': c.address, 'ciudad': c.city, 'codigo_postal': c.postal_code, 'cif_nif': c.tax_id, 'activo': c.is_active} for c in clients]
                            with open(filepath, 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                        exported_files.append(filepath)

                # Export Products
                if export_products:
                    products = db.query(Product).all()
                    if products:
                        if is_csv:
                            filepath = os.path.join(export_dir, "productos.csv")
                            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                                writer = csv.writer(f)
                                writer.writerow(['Código', 'Nombre', 'Descripción', 'Categoría', 'P. Coste', 'P. Venta', 'Stock', 'Stock Mín', 'Unidad', 'Activo'])
                                for p in products:
                                    writer.writerow([p.code, p.name, p.description or '', p.category or '', float(p.purchase_price or 0), float(p.sale_price or 0), p.current_stock or 0, p.minimum_stock or 0, p.stock_unit or '', 'Sí' if p.is_active else 'No'])
                        else:
                            filepath = os.path.join(export_dir, "productos.json")
                            data = [{'codigo': p.code, 'nombre': p.name, 'descripcion': p.description, 'categoria': p.category, 'precio_coste': float(p.purchase_price or 0), 'precio_venta': float(p.sale_price or 0), 'stock': p.current_stock, 'stock_minimo': p.minimum_stock, 'unidad': p.stock_unit, 'activo': p.is_active} for p in products]
                            with open(filepath, 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                        exported_files.append(filepath)

                # Export Documents
                if export_documents:
                    documents = db.query(Document).options(joinedload(Document.client)).all()
                    if documents:
                        if is_csv:
                            filepath = os.path.join(export_dir, "documentos.csv")
                            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                                writer = csv.writer(f)
                                writer.writerow(['Código', 'Tipo', 'Estado', 'Cliente', 'F. Emisión', 'F. Vencimiento', 'Subtotal', 'IVA', 'Total', 'Notas'])
                                for d in documents:
                                    doc_type = d.type.value if hasattr(d.type, 'value') else str(d.type)
                                    status = d.status.value if hasattr(d.status, 'value') else str(d.status)
                                    client_name = d.client.name if d.client else ''
                                    issue_date = d.issue_date.strftime('%Y-%m-%d') if d.issue_date else ''
                                    due_date = d.due_date.strftime('%Y-%m-%d') if d.due_date else ''
                                    writer.writerow([d.code, doc_type, status, client_name, issue_date, due_date, float(d.subtotal or 0), float(d.tax_amount or 0), float(d.total or 0), d.notes or ''])
                        else:
                            filepath = os.path.join(export_dir, "documentos.json")
                            data = []
                            for d in documents:
                                data.append({
                                    'codigo': d.code,
                                    'tipo': d.type.value if hasattr(d.type, 'value') else str(d.type),
                                    'estado': d.status.value if hasattr(d.status, 'value') else str(d.status),
                                    'cliente': d.client.name if d.client else None,
                                    'fecha_emision': d.issue_date.strftime('%Y-%m-%d') if d.issue_date else None,
                                    'fecha_vencimiento': d.due_date.strftime('%Y-%m-%d') if d.due_date else None,
                                    'subtotal': float(d.subtotal or 0),
                                    'iva': float(d.tax_amount or 0),
                                    'total': float(d.total or 0),
                                    'notas': d.notes
                                })
                            with open(filepath, 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                        exported_files.append(filepath)

            dialog.accept()

            if exported_files:
                file_list = '\n'.join([f"  - {os.path.basename(f)}" for f in exported_files])
                QMessageBox.information(
                    self, "✅ Exportación Completada",
                    f"Datos exportados correctamente a:\n{export_dir}\n\nArchivos creados:\n{file_list}"
                )
            else:
                QMessageBox.information(self, "ℹ️ Info", "No hay datos para exportar")

        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al exportar datos: {str(e)}")
    


class SettingsDialog(QDialog):
    """Functional Settings dialog with PDF configuration"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuracion - DRAGOFACTU")
        self.setModal(True)
        self.resize(600, 700)
        self.pdf_settings = get_pdf_settings()
        self.logo_path_temp = None
        self.setup_ui()
        self.load_pdf_settings()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Create tab widget
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #D2D2D7;
                border-radius: 8px;
                background: white;
            }
            QTabBar::tab {
                padding: 8px 16px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                background: #F5F5F7;
                border: 1px solid #D2D2D7;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 1px solid white;
            }
        """)

        # Tab 1: PDF Configuration
        pdf_tab = QWidget()
        pdf_layout = QVBoxLayout(pdf_tab)
        pdf_layout.setContentsMargins(16, 16, 16, 16)
        pdf_layout.setSpacing(12)

        # Company info section
        company_group = QGroupBox("Datos de la Empresa (PDF)")
        company_group.setStyleSheet(UIStyles.get_group_box_style())
        company_layout = QFormLayout(company_group)
        company_layout.setSpacing(10)

        self.pdf_company_name = QLineEdit()
        self.pdf_company_name.setPlaceholderText("Nombre de tu empresa")
        self.pdf_company_name.setStyleSheet(UIStyles.get_input_style())
        company_layout.addRow("Nombre:", self.pdf_company_name)

        self.pdf_company_address = QLineEdit()
        self.pdf_company_address.setPlaceholderText("Direccion completa")
        self.pdf_company_address.setStyleSheet(UIStyles.get_input_style())
        company_layout.addRow("Direccion:", self.pdf_company_address)

        self.pdf_company_phone = QLineEdit()
        self.pdf_company_phone.setPlaceholderText("+34 XXX XXX XXX")
        self.pdf_company_phone.setStyleSheet(UIStyles.get_input_style())
        company_layout.addRow("Telefono:", self.pdf_company_phone)

        self.pdf_company_email = QLineEdit()
        self.pdf_company_email.setPlaceholderText("email@tuempresa.com")
        self.pdf_company_email.setStyleSheet(UIStyles.get_input_style())
        company_layout.addRow("Email:", self.pdf_company_email)

        self.pdf_company_cif = QLineEdit()
        self.pdf_company_cif.setPlaceholderText("B12345678")
        self.pdf_company_cif.setStyleSheet(UIStyles.get_input_style())
        company_layout.addRow("CIF/NIF:", self.pdf_company_cif)

        pdf_layout.addWidget(company_group)

        # Logo section
        logo_group = QGroupBox("Logo de la Empresa")
        logo_group.setStyleSheet(UIStyles.get_group_box_style())
        logo_layout = QVBoxLayout(logo_group)
        logo_layout.setSpacing(10)

        # Logo preview
        self.logo_preview = QLabel()
        self.logo_preview.setFixedSize(150, 80)
        self.logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_preview.setStyleSheet("""
            QLabel {
                background-color: #F5F5F7;
                border: 2px dashed #D2D2D7;
                border-radius: 8px;
            }
        """)
        self.logo_preview.setText("Sin logo")

        logo_preview_container = QHBoxLayout()
        logo_preview_container.addStretch()
        logo_preview_container.addWidget(self.logo_preview)
        logo_preview_container.addStretch()
        logo_layout.addLayout(logo_preview_container)

        # Logo buttons
        logo_buttons = QHBoxLayout()
        logo_buttons.setSpacing(10)

        select_logo_btn = QPushButton("Seleccionar Logo")
        select_logo_btn.setStyleSheet(UIStyles.get_primary_button_style())
        select_logo_btn.clicked.connect(self.select_logo)
        logo_buttons.addWidget(select_logo_btn)

        remove_logo_btn = QPushButton("Eliminar Logo")
        remove_logo_btn.setStyleSheet(UIStyles.get_danger_button_style())
        remove_logo_btn.clicked.connect(self.remove_logo)
        logo_buttons.addWidget(remove_logo_btn)

        logo_buttons.addStretch()
        logo_layout.addLayout(logo_buttons)

        logo_hint = QLabel("Formatos: PNG, JPG. Recomendado: PNG con fondo transparente.")
        logo_hint.setStyleSheet("color: #6E6E73; font-size: 11px;")
        logo_layout.addWidget(logo_hint)

        pdf_layout.addWidget(logo_group)

        # Footer text section
        footer_group = QGroupBox("Texto del Pie de Factura")
        footer_group.setStyleSheet(UIStyles.get_group_box_style())
        footer_layout = QVBoxLayout(footer_group)
        footer_layout.setSpacing(10)

        footer_hint = QLabel("Este texto aparecera al final de todos los PDFs generados.")
        footer_hint.setStyleSheet("color: #6E6E73; font-size: 11px;")
        footer_layout.addWidget(footer_hint)

        self.pdf_footer_text = QTextEdit()
        self.pdf_footer_text.setMaximumHeight(100)
        self.pdf_footer_text.setPlaceholderText("Ej: Este documento es valido como factura segun la normativa fiscal vigente...")
        self.pdf_footer_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #D2D2D7;
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
                background: white;
            }
            QTextEdit:focus {
                border-color: #007AFF;
            }
        """)
        footer_layout.addWidget(self.pdf_footer_text)

        pdf_layout.addWidget(footer_group)
        pdf_layout.addStretch()

        tab_widget.addTab(pdf_tab, "Configuracion PDF")

        # Tab 2: UI Settings
        ui_tab = QWidget()
        ui_layout = QVBoxLayout(ui_tab)
        ui_layout.setContentsMargins(16, 16, 16, 16)
        ui_layout.setSpacing(12)

        ui_group = QGroupBox("Apariencia")
        ui_group.setStyleSheet(UIStyles.get_group_box_style())
        ui_form = QFormLayout(ui_group)
        ui_form.setSpacing(10)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Claro", "Oscuro"])
        # Load saved theme
        saved_theme = "Claro"
        try:
            theme_path = Path.home() / ".dragofactu" / "theme.json"
            if theme_path.exists():
                with open(theme_path) as f:
                    saved_theme = json.load(f).get("theme", "Claro")
        except Exception:
            pass
        self.theme_combo.setCurrentText(saved_theme)
        self.theme_combo.setStyleSheet(UIStyles.get_input_style())
        self.theme_combo.currentTextChanged.connect(self.preview_theme)
        ui_form.addRow("Tema:", self.theme_combo)

        self.language_combo = QComboBox()
        self.language_combo.addItems(["Espanol", "English", "Deutsch"])
        self.language_combo.setCurrentText("Espanol")
        self.language_combo.setStyleSheet(UIStyles.get_input_style())
        ui_form.addRow("Idioma:", self.language_combo)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(12)
        self.font_size_spin.setStyleSheet(UIStyles.get_input_style())
        ui_form.addRow("Tamano Fuente:", self.font_size_spin)

        ui_layout.addWidget(ui_group)

        # Business settings
        business_group = QGroupBox("Configuracion Negocio")
        business_group.setStyleSheet(UIStyles.get_group_box_style())
        business_form = QFormLayout(business_group)
        business_form.setSpacing(10)

        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["EUR - Euro", "USD - Dolar", "GBP - Libra"])
        self.currency_combo.setCurrentText("EUR - Euro")
        self.currency_combo.setStyleSheet(UIStyles.get_input_style())
        business_form.addRow("Moneda:", self.currency_combo)

        self.tax_rate_spin = QDoubleSpinBox()
        self.tax_rate_spin.setRange(0, 50)
        self.tax_rate_spin.setDecimals(2)
        self.tax_rate_spin.setValue(21)
        self.tax_rate_spin.setSuffix("%")
        self.tax_rate_spin.setStyleSheet(UIStyles.get_input_style())
        business_form.addRow("IVA Por Defecto:", self.tax_rate_spin)

        ui_layout.addWidget(business_group)
        ui_layout.addStretch()

        tab_widget.addTab(ui_tab, "Apariencia")

        # Tab 3: System Info
        info_tab = QWidget()
        info_layout = QVBoxLayout(info_tab)
        info_layout.setContentsMargins(16, 16, 16, 16)
        info_layout.setSpacing(12)

        # Database info
        db_group = QGroupBox("Base de Datos")
        db_group.setStyleSheet(UIStyles.get_group_box_style())
        db_form = QFormLayout(db_group)
        db_form.setSpacing(8)

        try:
            with SessionLocal() as db:
                client_count = db.query(Client).count()
                product_count = db.query(Product).count()
                document_count = db.query(Document).count()

                db_form.addRow("Clientes:", QLabel(str(client_count)))
                db_form.addRow("Productos:", QLabel(str(product_count)))
                db_form.addRow("Documentos:", QLabel(str(document_count)))
        except Exception as e:
            logger.error(f"Error getting database info for settings: {e}")
            db_form.addRow("Estado:", QLabel("Error de conexion"))

        info_layout.addWidget(db_group)

        # App info
        app_group = QGroupBox("Informacion Aplicacion")
        app_group.setStyleSheet(UIStyles.get_group_box_style())
        app_form = QFormLayout(app_group)
        app_form.setSpacing(8)

        app_form.addRow("Version:", QLabel("V2.0.0 (Multi-tenant)"))
        app_form.addRow("Desarrollador:", QLabel("DRAGOFACTU Team"))
        app_form.addRow("GitHub:", QLabel("github.com/Copitx/Dragofactu"))
        app_form.addRow("Python:", QLabel(f"3.{sys.version_info.minor}.{sys.version_info.micro}"))

        info_layout.addWidget(app_group)
        info_layout.addStretch()

        tab_widget.addTab(info_tab, "Sistema")

        # Tab 4: Server Configuration
        server_tab = QWidget()
        server_layout = QVBoxLayout(server_tab)
        server_layout.setContentsMargins(16, 16, 16, 16)
        server_layout.setSpacing(12)

        # Current mode info
        mode_group = QGroupBox("Modo de Conexion")
        mode_group.setStyleSheet(UIStyles.get_group_box_style())
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setSpacing(10)

        app_mode = get_app_mode()
        self.server_mode_label = QLabel()
        self.server_url_display = QLabel()
        self._update_server_mode_display(app_mode)

        mode_layout.addWidget(self.server_mode_label)
        mode_layout.addWidget(self.server_url_display)

        server_layout.addWidget(mode_group)

        # Server URL input
        config_group = QGroupBox("Configuracion del Servidor")
        config_group.setStyleSheet(UIStyles.get_group_box_style())
        config_layout = QFormLayout(config_group)
        config_layout.setSpacing(10)

        self.settings_server_url = QLineEdit()
        self.settings_server_url.setPlaceholderText("https://tu-app.railway.app")
        self.settings_server_url.setText(app_mode.server_url)
        self.settings_server_url.setStyleSheet(UIStyles.get_input_style())
        config_layout.addRow("URL Servidor:", self.settings_server_url)

        server_layout.addWidget(config_group)

        # Server actions
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        test_server_btn = QPushButton("Probar Conexion")
        test_server_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        test_server_btn.clicked.connect(self.test_server_connection)
        actions_layout.addWidget(test_server_btn)

        connect_server_btn = QPushButton("Conectar Servidor")
        connect_server_btn.setStyleSheet(UIStyles.get_primary_button_style())
        connect_server_btn.clicked.connect(self.connect_to_server)
        actions_layout.addWidget(connect_server_btn)

        use_local_btn = QPushButton("Usar Modo Local")
        use_local_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        use_local_btn.clicked.connect(self.use_local_mode)
        actions_layout.addWidget(use_local_btn)

        actions_layout.addStretch()
        server_layout.addLayout(actions_layout)

        # Info text
        info_text = QLabel(
            "Modo Local: Los datos se guardan en tu ordenador (SQLite).\n"
            "Modo Servidor: Los datos se sincronizan con el servidor remoto.\n\n"
            "Para usar el servidor, necesitas una URL válida y credenciales."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet(f"color: {UIStyles.COLORS['text_secondary']}; font-size: 11px;")
        server_layout.addWidget(info_text)

        server_layout.addStretch()

        tab_widget.addTab(server_tab, "Servidor")

        layout.addWidget(tab_widget)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        save_btn = QPushButton("Guardar Configuracion")
        save_btn.clicked.connect(self.save_settings)
        save_btn.setStyleSheet(UIStyles.get_primary_button_style())
        save_btn.setMinimumWidth(150)
        buttons_layout.addWidget(save_btn)

        reset_btn = QPushButton("Restablecer")
        reset_btn.clicked.connect(self.reset_settings)
        reset_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        buttons_layout.addWidget(reset_btn)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        buttons_layout.addWidget(cancel_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

    def load_pdf_settings(self):
        """Load PDF settings from config file"""
        settings = self.pdf_settings.get_settings()

        self.pdf_company_name.setText(settings.get('company_name', ''))
        self.pdf_company_address.setText(settings.get('company_address', ''))
        self.pdf_company_phone.setText(settings.get('company_phone', ''))
        self.pdf_company_email.setText(settings.get('company_email', ''))
        self.pdf_company_cif.setText(settings.get('company_cif', ''))
        self.pdf_footer_text.setPlainText(settings.get('footer_text', ''))

        # Load logo preview
        logo_path = settings.get('logo_path', '')
        if logo_path and os.path.exists(logo_path):
            self.update_logo_preview(logo_path)

    def update_logo_preview(self, path):
        """Update logo preview"""
        if path and os.path.exists(path):
            pixmap = QPixmap(path)
            scaled = pixmap.scaled(140, 70, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_preview.setPixmap(scaled)
            self.logo_path_temp = path
        else:
            self.logo_preview.setText("Sin logo")
            self.logo_preview.setPixmap(QPixmap())
            self.logo_path_temp = None

    def select_logo(self):
        """Open file dialog to select logo"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Logo",
            "",
            "Imagenes (*.png *.jpg *.jpeg *.bmp);;PNG (*.png);;JPEG (*.jpg *.jpeg)"
        )
        if file_path:
            self.update_logo_preview(file_path)

    def remove_logo(self):
        """Remove current logo"""
        self.logo_preview.setText("Sin logo")
        self.logo_preview.setPixmap(QPixmap())
        self.logo_path_temp = ""

    def preview_theme(self, theme_name):
        """Preview theme change - applies dark/light mode."""
        if theme_name == "Oscuro":
            UIStyles.set_dark_mode(True)
        else:
            UIStyles.set_dark_mode(False)
        # Refresh the main window stylesheet
        main_window = self.parent()
        if main_window and hasattr(main_window, '_apply_theme'):
            main_window._apply_theme()

    def save_settings(self):
        """Save all settings"""
        try:
            # Save PDF settings
            pdf_data = {
                'company_name': self.pdf_company_name.text(),
                'company_address': self.pdf_company_address.text(),
                'company_phone': self.pdf_company_phone.text(),
                'company_email': self.pdf_company_email.text(),
                'company_cif': self.pdf_company_cif.text(),
                'footer_text': self.pdf_footer_text.toPlainText(),
            }

            # Handle logo
            current_logo = self.pdf_settings.get('logo_path', '')
            if self.logo_path_temp == "":
                # Logo was removed
                self.pdf_settings.remove_logo()
                pdf_data['logo_path'] = ''
            elif self.logo_path_temp and self.logo_path_temp != current_logo:
                # New logo selected - copy it to config dir
                new_path = self.pdf_settings.copy_logo(self.logo_path_temp)
                if new_path:
                    pdf_data['logo_path'] = new_path
                else:
                    pdf_data['logo_path'] = current_logo
            else:
                pdf_data['logo_path'] = current_logo

            self.pdf_settings.save_settings(pdf_data)

            # Save theme preference
            theme = self.theme_combo.currentText()
            theme_config_path = Path.home() / ".dragofactu" / "theme.json"
            theme_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(theme_config_path, 'w') as f:
                json.dump({"theme": theme}, f)

            # Apply theme
            self.preview_theme(theme)

            show_toast(self.parent() or self, "Configuracion guardada correctamente", "success")
            self.accept()

        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            QMessageBox.critical(self, "Error", f"Error guardando configuracion: {str(e)}")

    def reset_settings(self):
        """Reset settings to defaults"""
        reply = QMessageBox.question(
            self,
            "Restablecer",
            "¿Esta seguro de restablecer la configuracion PDF a valores por defecto?"
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.pdf_settings.reset_to_defaults()
            self.load_pdf_settings()
            self.logo_path_temp = None
            self.logo_preview.setText("Sin logo")
            self.logo_preview.setPixmap(QPixmap())

            # Reset other settings
            self.theme_combo.setCurrentText("Auto")
            self.language_combo.setCurrentText("Espanol")
            self.font_size_spin.setValue(12)
            self.currency_combo.setCurrentText("EUR - Euro")
            self.tax_rate_spin.setValue(21)

            QMessageBox.information(self, "Restablecido", "Configuracion restablecida a valores por defecto")

    def _update_server_mode_display(self, app_mode):
        """Update the server mode display labels."""
        if app_mode.is_remote:
            self.server_mode_label.setText("Modo: SERVIDOR REMOTO")
            self.server_mode_label.setStyleSheet(f"""
                font-weight: 600;
                color: {UIStyles.COLORS['success']};
                font-size: 14px;
            """)
            self.server_url_display.setText(f"URL: {app_mode.server_url}")
            self.server_url_display.setStyleSheet(f"color: {UIStyles.COLORS['text_secondary']};")
        else:
            self.server_mode_label.setText("Modo: LOCAL (SQLite)")
            self.server_mode_label.setStyleSheet(f"""
                font-weight: 600;
                color: {UIStyles.COLORS['text_primary']};
                font-size: 14px;
            """)
            self.server_url_display.setText("Los datos se guardan localmente en tu ordenador")
            self.server_url_display.setStyleSheet(f"color: {UIStyles.COLORS['text_secondary']};")

    def test_server_connection(self):
        """Test connection to the server."""
        url = self.settings_server_url.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Ingrese la URL del servidor")
            return

        try:
            from dragofactu.services.api_client import APIClient
            client = APIClient(url)
            health = client.health_check()

            if health.get("status") == "healthy":
                version = health.get("version", "?")
                QMessageBox.information(self, "Conexion Exitosa",
                    f"Servidor funcionando correctamente.\nVersion: {version}")
            else:
                QMessageBox.warning(self, "Error", "El servidor no responde correctamente")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se puede conectar: {str(e)}")

    def connect_to_server(self):
        """Connect to server and switch to remote mode."""
        url = self.settings_server_url.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Ingrese la URL del servidor")
            return

        app_mode = get_app_mode()
        if app_mode.set_remote(url):
            self._update_server_mode_display(app_mode)
            QMessageBox.information(self, "Conectado",
                "Conectado al servidor.\n\n"
                "Debes cerrar sesion y volver a iniciar para usar el servidor.")
        else:
            QMessageBox.critical(self, "Error", "No se pudo conectar al servidor")

    def use_local_mode(self):
        """Switch to local mode."""
        app_mode = get_app_mode()
        app_mode.set_local()
        self._update_server_mode_display(app_mode)
        QMessageBox.information(self, "Modo Local",
            "Cambiado a modo local (SQLite).\n\n"
            "Debes cerrar sesion y volver a iniciar para usar el modo local.")

    def import_external_file(self, file_path):
        """Import external files"""
        import json
        
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    self.import_csv_file(file_path)
                elif file_path.endswith('.json'):
                    self.import_json_file(file_path)
                else:
                    self.import_text_file(file_path)
                    
                QMessageBox.information(self, "✅ Importado", f"Archivo importado correctamente:\n{file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "❌ Error", f"Error importando archivo: {str(e)}")
    
    def import_csv_file(self, file_path):
        """Import CSV file"""
        try:
            import csv
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    # Try to import as client if it looks like client data
                    if 'name' in row and ('email' in row or 'phone' in row):
                        with SessionLocal() as db:
                            client = Client(
                                code=row.get('code', f"C-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                                name=row.get('name', ''),
                                email=row.get('email') or None,
                                phone=row.get('phone') or None,
                                address=row.get('address') or None,
                                tax_id=row.get('tax_id') or None,
                                is_active=True
                            )
                            db.add(client)
                            db.commit()
                            count += 1
                
                QMessageBox.information(self, "✅ CSV Importado", f"Se importaron {count} clientes")
                
        except Exception as e:
            raise Exception(f"Error importando CSV: {str(e)}")
    
    def import_json_file(self, file_path):
        """Import JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                count = 0
                
                if isinstance(data, list):
                    for item in data:
                        if 'name' in item:  # Treat as client
                            with SessionLocal() as db:
                                client = Client(
                                    code=item.get('code', f"C-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                                    name=item.get('name', ''),
                                    email=item.get('email') or None,
                                    phone=item.get('phone') or None,
                                    address=item.get('address') or None,
                                    tax_id=item.get('tax_id') or None,
                                    is_active=item.get('is_active', True)
                                )
                                db.add(client)
                                db.commit()
                                count += 1
                
                QMessageBox.information(self, "✅ JSON Importado", f"Se importaron {count} clientes")
                
        except Exception as e:
            raise Exception(f"Error importando JSON: {str(e)}")
    
    def import_text_file(self, file_path):
        """Import text file as diary notes"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.strip().split('\n')
                
                # Create diary entries from lines
                import json
                self.load_notes()  # Load existing notes
                
                for line in lines:
                    if line.strip():
                        note = {
                            'title': f"Importado: {line[:30]}...",
                            'content': line,
                            'date': datetime.now().strftime('%Y-%m-%d'),
                            'time': datetime.now().strftime('%H:%M'),
                            'priority': '🟢 Normal',
                            'tags': ['importado', 'texto']
                        }
                        self.notes.append(note)
                
                self.save_notes()
                QMessageBox.information(self, "✅ Texto Importado", f"Se importaron {len(lines)} notas al diario")
                
        except Exception as e:
            raise Exception(f"Error importando texto: {str(e)}")

class LoginDialog(QDialog):
    """Modern login dialog with Apple-inspired design - supports local and remote modes"""

    def __init__(self):
        super().__init__()
        self.user = None
        self.user_data = None
        self.app_mode = get_app_mode()
        self.setup_ui()
        self._update_mode_indicator()

    def setup_ui(self):
        """Setup modern login dialog"""
        self.setWindowTitle("Dragofactu - Iniciar Sesión")
        self.setModal(True)
        self.setFixedSize(460, 680)

        # Apply dialog style
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {UIStyles.COLORS['bg_app']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 40, 50, 40)
        layout.setSpacing(16)

        # Logo/Title area
        title = QLabel("Dragofactu")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            font-size: 32px;
            font-weight: 600;
            color: {UIStyles.COLORS['text_primary']};
            background: transparent;
            padding: 16px 0;
        """)
        layout.addWidget(title)

        subtitle = QLabel("Sistema de Gestión Empresarial")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"""
            font-size: 14px;
            color: {UIStyles.COLORS['text_secondary']};
            background: transparent;
            margin-bottom: 16px;
        """)
        layout.addWidget(subtitle)

        # Mode indicator
        self.mode_indicator = QLabel()
        self.mode_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mode_indicator.setStyleSheet(f"""
            font-size: 11px;
            padding: 6px 12px;
            border-radius: 12px;
            background: transparent;
        """)
        layout.addWidget(self.mode_indicator)

        # Form container
        form_frame = QFrame()
        form_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {UIStyles.COLORS['bg_card']};
                border: 1px solid {UIStyles.COLORS['border_light']};
                border-radius: 12px;
            }}
        """)
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(24, 24, 24, 24)
        form_layout.setSpacing(16)

        # Username
        username_label = QLabel("Usuario")
        username_label.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 500;
            color: {UIStyles.COLORS['text_primary']};
            background: transparent;
        """)
        form_layout.addWidget(username_label)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Ingrese su usuario")
        self.username_edit.setStyleSheet(UIStyles.get_input_style())
        form_layout.addWidget(self.username_edit)

        # Password
        password_label = QLabel("Contraseña")
        password_label.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 500;
            color: {UIStyles.COLORS['text_primary']};
            background: transparent;
        """)
        form_layout.addWidget(password_label)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Ingrese su contraseña")
        self.password_edit.setStyleSheet(UIStyles.get_input_style())
        form_layout.addWidget(self.password_edit)

        # Login button
        login_btn = QPushButton("Iniciar Sesión")
        login_btn.clicked.connect(self.handle_login)
        login_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {UIStyles.COLORS['accent']};
                color: {UIStyles.COLORS['text_inverse']};
                border: none;
                border-radius: 8px;
                padding: 14px 24px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {UIStyles.COLORS['accent_hover']};
            }}
            QPushButton:pressed {{
                background-color: #004499;
            }}
        """)
        form_layout.addWidget(login_btn)

        layout.addWidget(form_frame)

        # Server configuration button
        server_btn = QPushButton("Configurar Servidor")
        server_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        server_btn.clicked.connect(self.show_server_config)
        layout.addWidget(server_btn)

        # Hint
        self.hint_label = QLabel("Modo local: admin / admin123")
        self.hint_label.setStyleSheet(f"""
            color: {UIStyles.COLORS['text_tertiary']};
            font-size: 11px;
            background: transparent;
            padding-top: 8px;
        """)
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.hint_label)

        layout.addStretch()

    def _update_mode_indicator(self):
        """Update the mode indicator label."""
        if self.app_mode.is_remote:
            self.mode_indicator.setText(f"Servidor: {self.app_mode.server_url}")
            self.mode_indicator.setStyleSheet(f"""
                font-size: 11px;
                padding: 6px 12px;
                border-radius: 12px;
                background-color: {UIStyles.COLORS['success']};
                color: white;
            """)
            self.hint_label.setText("Conectado al servidor remoto")
        else:
            self.mode_indicator.setText("Modo Local (SQLite)")
            self.mode_indicator.setStyleSheet(f"""
                font-size: 11px;
                padding: 6px 12px;
                border-radius: 12px;
                background-color: {UIStyles.COLORS['bg_hover']};
                color: {UIStyles.COLORS['text_secondary']};
            """)
            self.hint_label.setText("Modo local: admin / admin123")

    def show_server_config(self):
        """Show server configuration dialog."""
        dialog = ServerConfigDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._update_mode_indicator()

    def handle_login(self):
        """Handle login - supports both local and remote modes."""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Por favor ingrese usuario y contraseña")
            return

        if self.app_mode.is_remote:
            self._handle_remote_login(username, password)
        else:
            self._handle_local_login(username, password)

    def _handle_remote_login(self, username: str, password: str):
        """Handle login against remote API."""
        try:
            api = self.app_mode.api
            response = api.login(username, password)
            user_info = response.get("user", {})

            self.user_data = {
                'id': user_info.get('id', ''),
                'username': user_info.get('username', username),
                'full_name': user_info.get('full_name', username),
                'role': user_info.get('role', 'read_only'),
                'company_id': user_info.get('company_id', ''),
                'is_remote': True
            }
            logger.info(f"Remote login successful: {username}")
            self.accept()

        except Exception as e:
            error_msg = str(e)
            if hasattr(e, 'detail'):
                error_msg = e.detail
            QMessageBox.warning(self, "Error", f"Error de autenticación: {error_msg}")

    def _handle_local_login(self, username: str, password: str):
        """Handle login against local SQLite database."""
        try:
            auth_service = AuthService()
            with SessionLocal() as db:
                user = auth_service.authenticate(db, username, password)
                if user:
                    self.user_data = {
                        'id': user.id,
                        'username': user.username,
                        'full_name': user.full_name,
                        'role': user.role.value if hasattr(user.role, 'value') else str(user.role),
                        'is_remote': False
                    }
                    self.user = user
                    self.accept()
                else:
                    QMessageBox.warning(self, "Error", "Usuario o contraseña incorrectos")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error de autenticación: {str(e)}")


class ServerConfigDialog(QDialog):
    """Dialog to configure server connection."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.app_mode = get_app_mode()
        self.setWindowTitle("Configurar Servidor")
        self.setModal(True)
        self.setFixedSize(450, 350)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Title
        title = QLabel("Conexión al Servidor")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {UIStyles.COLORS['text_primary']};
        """)
        layout.addWidget(title)

        # Server URL input
        url_label = QLabel("URL del Servidor:")
        url_label.setStyleSheet(UIStyles.get_label_style())
        layout.addWidget(url_label)

        self.server_url_input = QLineEdit()
        self.server_url_input.setPlaceholderText("https://tu-app.railway.app")
        self.server_url_input.setText(self.app_mode.server_url)
        self.server_url_input.setStyleSheet(UIStyles.get_input_style())
        layout.addWidget(self.server_url_input)

        # Status label
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_status()
        layout.addWidget(self.status_label)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        test_btn = QPushButton("Probar Conexión")
        test_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        test_btn.clicked.connect(self.test_connection)
        btn_layout.addWidget(test_btn)

        local_btn = QPushButton("Usar Modo Local")
        local_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        local_btn.clicked.connect(self.use_local_mode)
        btn_layout.addWidget(local_btn)

        layout.addLayout(btn_layout)

        # Connect button
        self.connect_btn = QPushButton("Conectar al Servidor")
        self.connect_btn.setStyleSheet(UIStyles.get_primary_button_style())
        self.connect_btn.clicked.connect(self.connect_to_server)
        layout.addWidget(self.connect_btn)

        # Register link
        register_btn = QPushButton("Registrar nueva empresa")
        register_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {UIStyles.COLORS['accent']};
                border: none;
                font-size: 12px;
                text-decoration: underline;
            }}
            QPushButton:hover {{
                color: {UIStyles.COLORS['accent_hover']};
            }}
        """)
        register_btn.clicked.connect(self.show_register_dialog)
        layout.addWidget(register_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

    def _update_status(self):
        if self.app_mode.is_remote:
            self.status_label.setText("Conectado al servidor")
            self.status_label.setStyleSheet(f"color: {UIStyles.COLORS['success']}; font-size: 12px;")
        else:
            self.status_label.setText("Modo local activo")
            self.status_label.setStyleSheet(f"color: {UIStyles.COLORS['text_secondary']}; font-size: 12px;")

    def test_connection(self):
        """Test connection to server."""
        url = self.server_url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Ingrese la URL del servidor")
            return

        try:
            from dragofactu.services.api_client import APIClient
            client = APIClient(url)
            health = client.health_check()

            if health.get("status") == "healthy":
                version = health.get("version", "?")
                QMessageBox.information(self, "Conexión Exitosa",
                    f"Servidor funcionando correctamente.\nVersión: {version}")
            else:
                QMessageBox.warning(self, "Error", "El servidor no responde correctamente")
        except Exception as e:
            QMessageBox.critical(self, "Error de Conexión", f"No se puede conectar: {str(e)}")

    def connect_to_server(self):
        """Connect to the server and set remote mode."""
        url = self.server_url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Ingrese la URL del servidor")
            return

        try:
            if self.app_mode.set_remote(url):
                QMessageBox.information(self, "Conectado", "Conectado al servidor correctamente")
                self._update_status()
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "No se pudo conectar al servidor")
        except Exception as e:
            QMessageBox.critical(self, "Error de Conexion", str(e))

    def use_local_mode(self):
        """Switch to local mode."""
        self.app_mode.set_local()
        QMessageBox.information(self, "Modo Local", "Cambiado a modo local (SQLite)")
        self._update_status()
        self.accept()

    def show_register_dialog(self):
        """Show company registration dialog."""
        url = self.server_url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Primero ingrese la URL del servidor")
            return

        dialog = RegisterCompanyDialog(url, self)
        dialog.exec()


class RegisterCompanyDialog(QDialog):
    """Dialog to register a new company on the remote server."""

    def __init__(self, server_url: str, parent=None):
        super().__init__(parent)
        self.server_url = server_url
        self.setWindowTitle("Registrar Nueva Empresa")
        self.setModal(True)
        self.setMinimumSize(500, 600)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Title
        title = QLabel("Registrar Nueva Empresa")
        title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 600;
            color: {UIStyles.COLORS['text_primary']};
        """)
        layout.addWidget(title)

        subtitle = QLabel(f"Servidor: {self.server_url}")
        subtitle.setStyleSheet(f"color: {UIStyles.COLORS['text_secondary']}; font-size: 12px;")
        layout.addWidget(subtitle)

        # Company info
        company_group = QGroupBox("Datos de la Empresa")
        company_group.setStyleSheet(UIStyles.get_group_box_style())
        company_layout = QFormLayout(company_group)
        company_layout.setSpacing(10)

        self.company_code = QLineEdit()
        self.company_code.setPlaceholderText("EMP001")
        self.company_code.setStyleSheet(UIStyles.get_input_style())
        company_layout.addRow("Código*:", self.company_code)

        self.company_name = QLineEdit()
        self.company_name.setPlaceholderText("Mi Empresa S.L.")
        self.company_name.setStyleSheet(UIStyles.get_input_style())
        company_layout.addRow("Nombre*:", self.company_name)

        self.company_tax_id = QLineEdit()
        self.company_tax_id.setPlaceholderText("B12345678")
        self.company_tax_id.setStyleSheet(UIStyles.get_input_style())
        company_layout.addRow("CIF/NIF:", self.company_tax_id)

        layout.addWidget(company_group)

        # Admin user info
        admin_group = QGroupBox("Usuario Administrador")
        admin_group.setStyleSheet(UIStyles.get_group_box_style())
        admin_layout = QFormLayout(admin_group)
        admin_layout.setSpacing(10)

        self.username = QLineEdit()
        self.username.setPlaceholderText("admin")
        self.username.setStyleSheet(UIStyles.get_input_style())
        admin_layout.addRow("Usuario*:", self.username)

        self.email = QLineEdit()
        self.email.setPlaceholderText("admin@empresa.com")
        self.email.setStyleSheet(UIStyles.get_input_style())
        admin_layout.addRow("Email*:", self.email)

        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText("Minimo 8 caracteres")
        self.password.setStyleSheet(UIStyles.get_input_style())
        admin_layout.addRow("Contraseña*:", self.password)

        self.password_confirm = QLineEdit()
        self.password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_confirm.setPlaceholderText("Repetir contraseña")
        self.password_confirm.setStyleSheet(UIStyles.get_input_style())
        admin_layout.addRow("Confirmar*:", self.password_confirm)

        self.first_name = QLineEdit()
        self.first_name.setStyleSheet(UIStyles.get_input_style())
        admin_layout.addRow("Nombre:", self.first_name)

        self.last_name = QLineEdit()
        self.last_name.setStyleSheet(UIStyles.get_input_style())
        admin_layout.addRow("Apellidos:", self.last_name)

        layout.addWidget(admin_group)

        # Password requirements hint
        hint = QLabel("La contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula y un número.")
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {UIStyles.COLORS['text_tertiary']}; font-size: 11px;")
        layout.addWidget(hint)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        register_btn = QPushButton("Registrar Empresa")
        register_btn.setStyleSheet(UIStyles.get_primary_button_style())
        register_btn.clicked.connect(self.register)
        btn_layout.addWidget(register_btn)

        layout.addLayout(btn_layout)

    def register(self):
        """Register the company."""
        # Validate required fields
        if not all([
            self.company_code.text().strip(),
            self.company_name.text().strip(),
            self.username.text().strip(),
            self.email.text().strip(),
            self.password.text()
        ]):
            QMessageBox.warning(self, "Error", "Complete todos los campos obligatorios (*)")
            return

        if self.password.text() != self.password_confirm.text():
            QMessageBox.warning(self, "Error", "Las contraseñas no coinciden")
            return

        if len(self.password.text()) < 8:
            QMessageBox.warning(self, "Error", "La contraseña debe tener al menos 8 caracteres")
            return

        try:
            from dragofactu.services.api_client import APIClient
            client = APIClient(self.server_url)

            result = client.register(
                company_code=self.company_code.text().strip(),
                company_name=self.company_name.text().strip(),
                company_tax_id=self.company_tax_id.text().strip() or None,
                username=self.username.text().strip(),
                email=self.email.text().strip(),
                password=self.password.text(),
                first_name=self.first_name.text().strip() or None,
                last_name=self.last_name.text().strip() or None
            )

            QMessageBox.information(self, "Registro Exitoso",
                f"Empresa '{self.company_name.text()}' registrada correctamente.\n\n"
                f"Usuario: {self.username.text()}\n"
                "Ya puedes iniciar sesión con tus credenciales.")
            self.accept()

        except Exception as e:
            error_msg = str(e)
            if hasattr(e, 'detail'):
                error_msg = e.detail
            QMessageBox.critical(self, "Error de Registro", f"No se pudo registrar: {error_msg}")


class App(QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        apply_stylesheet(self)
        self.current_user = None
        self.current_user_data = None
        self.setup_app()

    def try_auto_login(self) -> bool:
        """Attempt auto-login with saved tokens.

        Returns True if auto-login succeeded, False otherwise.
        """
        app_mode = get_app_mode()

        # Only try auto-login in remote mode
        if not app_mode.is_remote:
            logger.info("Auto-login skipped: local mode")
            return False

        api = app_mode.api
        if api is None:
            logger.info("Auto-login skipped: no API client")
            return False

        if not api.is_authenticated:
            logger.info("Auto-login skipped: no saved tokens")
            return False

        try:
            # Validate tokens with /auth/me
            user_info = api.get_me()
            if user_info and user_info.get('id'):
                self.current_user_data = {
                    'id': user_info.get('id'),
                    'username': user_info.get('username'),
                    'full_name': user_info.get('full_name', user_info.get('username', '')),
                    'role': user_info.get('role', 'read_only'),
                    'is_remote': True
                }
                logger.info(f"Auto-login successful for user: {user_info.get('username')}")
                return True
            else:
                logger.warning("Auto-login failed: invalid user info from API")
                return False
        except Exception as e:
            logger.warning(f"Auto-login failed: {e}")
            return False

    def setup_app(self):
        """Setup application"""
        # Create database tables (for local mode)
        Base.metadata.create_all(bind=engine)

        # Try auto-login with saved tokens first
        if self.try_auto_login():
            self.show_main_window()
        else:
            self.show_login()
    
    def show_login(self):
        """Show login dialog"""
        login_dialog = LoginDialog()
        
        if login_dialog.exec() == QDialog.DialogCode.Accepted:
            # Use the pre-extracted user_data to avoid DetachedInstanceError
            self.current_user_data = login_dialog.user_data
            self.show_main_window()
        else:
            self.quit()
    
    def show_main_window(self):
        """Show main window"""
        self.main_window = MainWindow()
        
        # Create a simple user object with basic attributes
        class SimpleUser:
            def __init__(self, data):
                self.id = data['id']
                self.username = data['username']
                self.full_name = data['full_name']
                self.role = data['role']
        
        simple_user = SimpleUser(self.current_user_data)
        self.main_window.set_current_user(simple_user)
        self.main_window.show()

def main():
    """Main function"""
    app = App()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
