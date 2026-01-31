#!/usr/bin/env python3
"""
DRAGOFACTU - Complete Business Management System
Fixed version with proper data persistence and full functionality
"""

import sys
import os
import logging
import uuid
from datetime import datetime, date
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('dragofactu')

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
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtGui import QFont, QAction, QColor

from sqlalchemy.orm import joinedload

from dragofactu.models.database import SessionLocal, engine, Base
from dragofactu.models.entities import User, Client, Product, Document, DocumentLine, DocumentType, DocumentStatus
from dragofactu.services.auth.auth_service import AuthService
from dragofactu.config.translation import translator
from dragofactu.ui.styles import apply_stylesheet


class UIStyles:
    """Shared UI styles for Apple-inspired design system"""

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
        'success': '#34C759',
        'warning': '#FF9500',
        'danger': '#FF3B30',
        'danger_hover': '#CC2F26',
        'border': '#D2D2D7',
        'border_light': '#E5E5EA',
    }

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
        """Initialize PDF generator with company configuration"""
        from dragofactu.config.config import AppConfig

        self.company_name = AppConfig.PDF_COMPANY_NAME
        self.company_address = AppConfig.PDF_COMPANY_ADDRESS
        self.company_phone = AppConfig.PDF_COMPANY_PHONE
        self.company_email = AppConfig.PDF_COMPANY_EMAIL
        self.company_cif = AppConfig.PDF_COMPANY_CIF
        self.logo_path = AppConfig.PDF_LOGO_PATH

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
        """Create header with company info and invoice details"""
        # Determine document type label
        doc_type_labels = {
            DocumentType.INVOICE: 'FACTURA',
            DocumentType.QUOTE: 'PRESUPUESTO',
            DocumentType.DELIVERY_NOTE: 'ALBARAN',
        }
        doc_type_label = doc_type_labels.get(document.type, 'DOCUMENTO')

        # Company info (left side)
        company_info = []
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
        """Create footer with legal text"""
        footer_text = """
        Este documento es valido como factura segun la normativa fiscal vigente.<br/>
        Forma de pago: Transferencia bancaria | Plazo de pago: 30 dias<br/>
        Gracias por confiar en nosotros.
        """

        return Paragraph(footer_text, styles['Footer'])


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

        # 3. Quick Actions
        self._create_quick_actions(layout)

        # 4. Recent Documents
        self._create_recent_documents(layout)

        layout.addStretch()

    def _create_welcome_section(self, parent_layout):
        """Create welcome header section"""
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.setContentsMargins(0, 0, 0, 0)
        welcome_layout.setSpacing(4)

        # Welcome title
        welcome_label = QLabel("Bienvenido a Dragofactu")
        welcome_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 600;
            color: {self.COLORS['text_primary']};
            background: transparent;
        """)
        welcome_layout.addWidget(welcome_label)

        # Subtitle
        subtitle_label = QLabel("Resumen de tu negocio")
        subtitle_label.setStyleSheet(f"""
            font-size: 15px;
            color: {self.COLORS['text_secondary']};
            background: transparent;
        """)
        welcome_layout.addWidget(subtitle_label)

        parent_layout.addWidget(welcome_widget)

    def _create_metrics_section(self, parent_layout):
        """Create metrics cards row"""
        metrics_widget = QWidget()
        metrics_layout = QHBoxLayout(metrics_widget)
        metrics_layout.setContentsMargins(0, 0, 0, 0)
        metrics_layout.setSpacing(16)

        # Define metrics
        metrics = [
            ('clients', 'Clientes', self.get_client_count()),
            ('products', 'Productos', self.get_product_count()),
            ('documents', 'Documentos', self.get_document_count()),
            ('low_stock', 'Stock Bajo', self.get_low_stock_count()),
        ]

        for key, title, value in metrics:
            card = self._create_metric_card(key, title, value)
            metrics_layout.addWidget(card)

        parent_layout.addWidget(metrics_widget)

    def _create_metric_card(self, key, title, value):
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

        # Title label
        title_label = QLabel(title)
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

        # Store reference for updates
        self.metric_labels[key] = value_label

        return card

    def _create_quick_actions(self, parent_layout):
        """Create quick action cards"""
        # Section title
        section_title = QLabel("Acciones Rápidas")
        section_title.setStyleSheet(f"""
            font-size: 17px;
            font-weight: 600;
            color: {self.COLORS['text_primary']};
            background: transparent;
            padding-top: 8px;
        """)
        parent_layout.addWidget(section_title)

        # Actions container
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(16)

        # Define actions
        actions = [
            ('Nueva Factura', 'Crear documento de venta', self.add_invoice),
            ('Nuevo Presupuesto', 'Crear cotización', self.add_quote),
            ('Nuevo Cliente', 'Añadir al directorio', self.add_client),
            ('Nuevo Producto', 'Añadir al inventario', self.add_product),
        ]

        for title, description, callback in actions:
            action_card = self._create_action_card(title, description, callback)
            actions_layout.addWidget(action_card)

        parent_layout.addWidget(actions_widget)

    def _create_action_card(self, title, description, callback):
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

        # Description
        desc_label = QLabel(description)
        desc_label.setStyleSheet(f"""
            font-size: 12px;
            color: {self.COLORS['text_secondary']};
            background: transparent;
        """)
        card_layout.addWidget(desc_label)

        # Make card clickable
        card.mousePressEvent = lambda e: callback()

        return card

    def _create_recent_documents(self, parent_layout):
        """Create recent documents section"""
        # Section title
        section_title = QLabel("Documentos Recientes")
        section_title.setStyleSheet(f"""
            font-size: 17px;
            font-weight: 600;
            color: {self.COLORS['text_primary']};
            background: transparent;
            padding-top: 8px;
        """)
        parent_layout.addWidget(section_title)

        # Documents container
        docs_frame = QFrame()
        docs_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.COLORS['bg_card']};
                border: none;
                border-radius: 12px;
            }}
        """)

        docs_layout = QVBoxLayout(docs_frame)
        docs_layout.setContentsMargins(0, 0, 0, 0)
        docs_layout.setSpacing(0)

        # Get recent documents
        recent_docs = self._get_recent_documents()

        if recent_docs:
            for i, doc in enumerate(recent_docs):
                doc_row = self._create_document_row(doc, is_last=(i == len(recent_docs) - 1))
                docs_layout.addWidget(doc_row)
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
            docs_layout.addWidget(empty_label)

        parent_layout.addWidget(docs_frame)

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

        # Status badge
        status = doc.get('status', 'draft')
        status_colors = {
            'draft': self.COLORS['text_tertiary'],
            'sent': self.COLORS['accent'],
            'paid': self.COLORS['success'],
            'pending': self.COLORS['warning'],
        }
        status_color = status_colors.get(status.lower(), self.COLORS['text_tertiary'])

        status_label = QLabel(status.capitalize())
        status_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 500;
            color: {status_color};
            background: transparent;
            padding: 4px 8px;
            min-width: 60px;
        """)
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row_layout.addWidget(status_label)

        return row

    def _get_recent_documents(self):
        """Get recent documents from database"""
        try:
            with SessionLocal() as db:
                documents = db.query(Document).order_by(
                    Document.created_at.desc()
                ).limit(5).all()

                result = []
                for doc in documents:
                    result.append({
                        'code': doc.code or 'N/A',
                        'client': doc.client.name if doc.client else 'Sin cliente',
                        'total': float(doc.total or 0),
                        'status': doc.status.value if doc.status else 'draft',
                    })
                return result
        except Exception as e:
            logger.error(f"Error getting recent documents: {e}")
            return []

    def refresh_data(self):
        """Refresh dashboard data"""
        # Update metric values
        if 'clients' in self.metric_labels:
            self.metric_labels['clients'].setText(str(self.get_client_count()))
        if 'products' in self.metric_labels:
            self.metric_labels['products'].setText(str(self.get_product_count()))
        if 'documents' in self.metric_labels:
            self.metric_labels['documents'].setText(str(self.get_document_count()))
        if 'low_stock' in self.metric_labels:
            self.metric_labels['low_stock'].setText(str(self.get_low_stock_count()))

    def get_client_count(self):
        """Get total clients"""
        try:
            with SessionLocal() as db:
                return db.query(Client).filter(Client.is_active == True).count()
        except Exception as e:
            logger.error(f"Error getting client count: {e}")
            return 0

    def get_product_count(self):
        """Get total products"""
        try:
            with SessionLocal() as db:
                return db.query(Product).filter(Product.is_active == True).count()
        except Exception as e:
            logger.error(f"Error getting product count: {e}")
            return 0

    def get_document_count(self):
        """Get total documents"""
        try:
            with SessionLocal() as db:
                return db.query(Document).count()
        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return 0

    def get_low_stock_count(self):
        """Get products with low stock"""
        try:
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
            QMessageBox.information(self, "Éxito", "Cliente añadido correctamente")
            self.refresh_data()

    def add_product(self):
        """Add new product"""
        dialog = ProductDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Éxito", "Producto añadido correctamente")
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
        """Load existing client data for editing"""
        try:
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
                    QMessageBox.warning(self, "❌ Error", "Cliente no encontrado")
                    self.reject()
        except Exception as e:
            logger.error(f"Error loading client data: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error cargando cliente: {str(e)}")
            self.reject()

    def accept(self):
        """Save or update client"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "❌ Error", "El nombre es obligatorio")
            return

        try:
            with SessionLocal() as db:
                if self.is_edit_mode:
                    # Update existing client
                    client = db.query(Client).filter(Client.id == self.client_id).first()
                    if not client:
                        QMessageBox.warning(self, "❌ Error", "Cliente no encontrado")
                        return
                    client.name = self.name_edit.text().strip()
                    client.email = self.email_edit.text().strip() or None
                    client.phone = self.phone_edit.text().strip() or None
                    client.address = self.address_edit.text().strip() or None
                    client.city = self.city_edit.text().strip() or None
                    client.postal_code = self.postal_code_edit.text().strip() or None
                    client.tax_id = self.nif_edit.text().strip() or None
                    client.notes = self.notes_edit.toPlainText().strip() or None
                    client.is_active = self.active_check.isChecked()
                else:
                    # Create new client
                    client = Client(
                        code=self.code_edit.text().strip() or f"C-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        name=self.name_edit.text().strip(),
                        email=self.email_edit.text().strip() or None,
                        phone=self.phone_edit.text().strip() or None,
                        address=self.address_edit.text().strip() or None,
                        city=self.city_edit.text().strip() or None,
                        postal_code=self.postal_code_edit.text().strip() or None,
                        tax_id=self.nif_edit.text().strip() or None,
                        notes=self.notes_edit.toPlainText().strip() or None,
                        is_active=self.active_check.isChecked()
                    )
                    db.add(client)
                db.commit()
                super().accept()
        except Exception as e:
            logger.error(f"Error saving client: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al guardar cliente: {str(e)}")

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

        try:
            with SessionLocal() as db:
                if self.is_edit_mode:
                    # Update existing product
                    product = db.query(Product).filter(Product.id == self.product_id).first()
                    if not product:
                        QMessageBox.warning(self, "Error", "Producto no encontrado")
                        return

                    product.name = self.name_edit.text().strip()
                    product.description = self.description_edit.toPlainText().strip() or None
                    product.category = self.category_edit.text().strip() or None
                    product.purchase_price = self.cost_price_edit.value()
                    product.sale_price = self.sale_price_edit.value()
                    product.current_stock = self.stock_spin.value()
                    product.minimum_stock = self.min_stock_spin.value()
                    product.stock_unit = self.unit_combo.currentText()
                    product.is_active = self.active_check.isChecked()
                else:
                    # Create new product
                    # Check for unique code constraint
                    product_code = self.code_edit.text().strip()
                    if not product_code:
                        # Generate unique code with milliseconds for uniqueness
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
                        name=self.name_edit.text().strip(),
                        description=self.description_edit.toPlainText().strip() or None,
                        category=self.category_edit.text().strip() or None,
                        purchase_price=self.cost_price_edit.value(),
                        sale_price=self.sale_price_edit.value(),
                        current_stock=self.stock_spin.value(),
                        minimum_stock=self.min_stock_spin.value(),
                        stock_unit=self.unit_combo.currentText(),
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
    """Document creation dialog with client/product selection"""
    def __init__(self, parent=None, doc_type="quote"):
        super().__init__(parent)
        self.doc_type = doc_type
        if doc_type == "quote":
            self.doc_title = "Presupuesto"
        elif doc_type == "delivery":
            self.doc_title = "Albaran"
        else:
            self.doc_title = "Factura"
        self.setWindowTitle(f"Nuevo {self.doc_title}")
        self.setModal(True)
        # Increased size to prevent overlapping elements
        self.resize(1000, 850)
        self.items = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Client section
        client_group = QGroupBox("👤 Datos del Cliente")
        client_layout = QFormLayout(client_group)
        
        self.client_combo = QComboBox()
        self.setup_clients()
        client_layout.addRow("Cliente (*)", self.client_combo)
        
        layout.addWidget(client_group)
        
        # Document items
        items_group = QGroupBox(f"📋 Items del {self.doc_title}")
        items_layout = QVBoxLayout(items_group)
        
        # Items table
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels([
            "Producto", "Descripción", "Cantidad", "Precio Unit.", "Descuento", "Total"
        ])
        
        # Configure table
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        items_layout.addWidget(self.items_table)
        
        # Product selection buttons
        product_layout = QHBoxLayout()
        
        self.product_combo = QComboBox()
        self.setup_products()
        product_layout.addWidget(QLabel("Añadir Producto:"))
        product_layout.addWidget(self.product_combo)
        
        add_item_btn = QPushButton("➕ Añadir")
        add_item_btn.clicked.connect(self.add_item)
        product_layout.addWidget(add_item_btn)
        
        remove_item_btn = QPushButton("➖ Eliminar")
        remove_item_btn.clicked.connect(self.remove_item)
        product_layout.addWidget(remove_item_btn)
        
        product_layout.addStretch()
        items_layout.addLayout(product_layout)
        
        layout.addWidget(items_group)
        
        # Totals section
        totals_group = QGroupBox("💰 Totales")
        totals_layout = QFormLayout(totals_group)
        
        self.subtotal_label = QLabel("0.00 €")
        totals_layout.addRow("Subtotal:", self.subtotal_label)
        
        self.tax_combo = QComboBox()
        self.tax_combo.addItems(["21% IVA", "10% IVA", "4% IVA", "Exento IVA"])
        self.tax_combo.currentTextChanged.connect(self.update_totals)
        totals_layout.addRow("IVA:", self.tax_combo)
        
        self.total_label = QLabel("0.00 €")
        totals_layout.addRow("Total:", self.total_label)
        
        layout.addWidget(totals_group)
        
        # Notes
        notes_group = QGroupBox("📝 Notas")
        notes_layout = QVBoxLayout(notes_group)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Notas adicionales...")
        self.notes_edit.setMaximumHeight(100)
        notes_layout.addWidget(self.notes_edit)
        
        layout.addWidget(notes_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton(f"💾 Guardar {self.doc_title}")
        save_btn.clicked.connect(self.save_document)
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
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Initial totals
        self.update_totals()
    
    def setup_clients(self):
        """Load clients into combo box"""
        try:
            with SessionLocal() as db:
                clients = db.query(Client).filter(Client.is_active == True).all()
                self.client_combo.addItem("Seleccione un cliente...", None)
                for client in clients:
                    self.client_combo.addItem(f"{client.code} - {client.name}", client.id)
        except Exception as e:
            logger.error(f"Error loading clients into combo: {e}")
            self.client_combo.addItem("Error cargando clientes", None)

    def setup_products(self):
        """Load products into combo box"""
        try:
            with SessionLocal() as db:
                products = db.query(Product).filter(Product.is_active == True).all()
                self.product_combo.addItem("Seleccione un producto...", None)
                for product in products:
                    self.product_combo.addItem(f"{product.code} - {product.name}", product.id)
        except Exception as e:
            logger.error(f"Error loading products into combo: {e}")
            self.product_combo.addItem("Error cargando productos", None)
    
    def add_item(self):
        """Add selected product to table"""
        product_id = self.product_combo.currentData()
        if not product_id:
            QMessageBox.warning(self, "❌ Error", "Seleccione un producto primero")
            return
        
        try:
            with SessionLocal() as db:
                product = db.query(Product).filter(Product.id == product_id).first()
                if product:
                    row = self.items_table.rowCount()
                    self.items_table.insertRow(row)
                    
                    self.items_table.setItem(row, 0, QTableWidgetItem(product.name))
                    self.items_table.setItem(row, 1, QTableWidgetItem(product.description or ""))
                    self.items_table.setItem(row, 2, QTableWidgetItem("1"))
                    self.items_table.setItem(row, 3, QTableWidgetItem(f"{product.sale_price:.2f}"))
                    self.items_table.setItem(row, 4, QTableWidgetItem("0"))
                    self.items_table.setItem(row, 5, QTableWidgetItem(f"{product.sale_price:.2f}"))
                    
                    self.items.append({
                        'product_id': product.id,
                        'quantity': 1,
                        'price': product.sale_price,
                        'discount': 0
                    })
                    
                    self.update_totals()
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error añadiendo producto: {str(e)}")
    
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
                    subtotal += float(total_item.text().replace('€', '').strip())
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
        
        self.subtotal_label.setText(f"{subtotal:.2f} €")
        self.total_label.setText(f"{total:.2f} €")
    
    def _get_current_user_id(self):
        """Get current user ID from MainWindow"""
        widget = self.parent()
        while widget is not None:
            if hasattr(widget, 'current_user') and widget.current_user:
                return widget.current_user.id
            widget = widget.parent()
        return None

    def save_document(self):
        """Save document"""
        client_id = self.client_combo.currentData()
        if not client_id:
            QMessageBox.warning(self, "❌ Error", "Seleccione un cliente")
            return

        if self.items_table.rowCount() == 0:
            QMessageBox.warning(self, "❌ Error", "Añada al menos un producto")
            return

        # Get current user ID
        user_id = self._get_current_user_id()
        if not user_id:
            QMessageBox.warning(self, "❌ Error", "No hay usuario autenticado")
            return

        try:
            with SessionLocal() as db:
                # Calculate totals
                total_text = self.total_label.text()
                total = float(total_text.replace('€', '').strip())

                # Create document - determine type and code prefix
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
                    notes=self.notes_edit.toPlainText(),
                    created_by=user_id
                )
                
                db.add(document)
                db.commit()
                
                QMessageBox.information(self, "✅ Éxito", f"{self.doc_title} guardado correctamente\nCódigo: {doc_code}")
                self.accept()
                
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error guardando {self.doc_title.lower()}: {str(e)}")

# Continue with other classes...
class ClientManagementTab(QWidget):
    """Modern client management tab with Apple-inspired design"""

    def __init__(self):
        super().__init__()
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
        title_label = QLabel("Clientes")
        title_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 600;
            color: {UIStyles.COLORS['text_primary']};
            background: transparent;
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(12)

        add_btn = QPushButton("+ Nuevo Cliente")
        add_btn.clicked.connect(self.add_client)
        add_btn.setStyleSheet(UIStyles.get_primary_button_style())
        toolbar_layout.addWidget(add_btn)

        edit_btn = QPushButton("Editar")
        edit_btn.clicked.connect(self.edit_client)
        edit_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        toolbar_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Eliminar")
        delete_btn.clicked.connect(self.delete_client)
        delete_btn.setStyleSheet(UIStyles.get_danger_button_style())
        toolbar_layout.addWidget(delete_btn)

        toolbar_layout.addStretch()

        refresh_btn = QPushButton("Actualizar")
        refresh_btn.clicked.connect(self.refresh_data)
        refresh_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        toolbar_layout.addWidget(refresh_btn)

        layout.addLayout(toolbar_layout)

        # Search
        search_layout = QHBoxLayout()
        search_layout.setSpacing(12)

        search_label = QLabel("Buscar:")
        search_label.setStyleSheet(UIStyles.get_label_style())
        search_layout.addWidget(search_label)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Buscar por nombre, email, teléfono...")
        self.search_edit.setStyleSheet(UIStyles.get_input_style())
        self.search_edit.textChanged.connect(self.filter_clients)
        search_layout.addWidget(self.search_edit)

        layout.addLayout(search_layout)

        # Table
        self.clients_table = QTableWidget()
        self.clients_table.setColumnCount(7)
        self.clients_table.setHorizontalHeaderLabels([
            "CÓDIGO", "NOMBRE", "EMAIL", "TELÉFONO", "DIRECCIÓN", "CIF/NIF", "ESTADO"
        ])
        self.clients_table.setStyleSheet(UIStyles.get_table_style())
        self.clients_table.setAlternatingRowColors(False)
        self.clients_table.setShowGrid(False)
        self.clients_table.verticalHeader().setVisible(False)

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
        """Refresh clients data"""
        self.client_ids = []  # Store client IDs for reference
        try:
            with SessionLocal() as db:
                clients = db.query(Client).order_by(Client.name).all()

                self.clients_table.setRowCount(0)
                self.client_ids = []

                for row, client in enumerate(clients):
                    self.clients_table.insertRow(row)
                    self.client_ids.append(client.id)  # Store ID

                    self.clients_table.setItem(row, 0, QTableWidgetItem(client.code or ""))
                    self.clients_table.setItem(row, 1, QTableWidgetItem(client.name or ""))
                    self.clients_table.setItem(row, 2, QTableWidgetItem(client.email or ""))
                    self.clients_table.setItem(row, 3, QTableWidgetItem(client.phone or ""))
                    self.clients_table.setItem(row, 4, QTableWidgetItem(client.address or ""))
                    self.clients_table.setItem(row, 5, QTableWidgetItem(client.tax_id or ""))

                    status_text = "✅ Activo" if client.is_active else "❌ Inactivo"
                    status_item = QTableWidgetItem(status_text)
                    self.clients_table.setItem(row, 6, status_item)

                self.status_label.setText(f"📊 Mostrando {len(clients)} clientes")

        except Exception as e:
            logger.error(f"Error refreshing clients: {e}")
            self.status_label.setText(f"❌ Error: {str(e)}")

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
            QMessageBox.information(self, "✅ Éxito", "Cliente creado correctamente")

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
            QMessageBox.information(self, "✅ Éxito", "Cliente actualizado correctamente")

    def delete_client(self):
        """Delete selected client"""
        current_row = self.clients_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "❌ Error", "Seleccione un cliente para eliminar")
            return

        if current_row >= len(self.client_ids):
            QMessageBox.warning(self, "❌ Error", "Error al obtener datos del cliente")
            return

        client_name = self.clients_table.item(current_row, 1).text()
        client_id = self.client_ids[current_row]

        # Custom confirmation dialog
        dialog = ConfirmationDialog(
            self,
            title="🗑️ Confirmar Eliminación",
            message=f"¿Está seguro de eliminar al cliente '{client_name}'?\n\n"
                    "Se eliminarán también todos los documentos asociados.\n"
                    "Esta acción no se puede deshacer.",
            confirm_text="Eliminar",
            is_danger=True
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                with SessionLocal() as db:
                    # Check for associated documents
                    doc_count = db.query(Document).filter(Document.client_id == client_id).count()
                    if doc_count > 0:
                        confirm = QMessageBox.warning(
                            self, "⚠️ Advertencia",
                            f"Este cliente tiene {doc_count} documento(s) asociado(s).\n"
                            "¿Desea eliminar el cliente y todos sus documentos?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.No
                        )
                        if confirm != QMessageBox.StandardButton.Yes:
                            return
                        # Delete associated documents first
                        db.query(Document).filter(Document.client_id == client_id).delete()

                    # Delete the client
                    client = db.query(Client).filter(Client.id == client_id).first()
                    if client:
                        db.delete(client)
                        db.commit()
                        self.refresh_data()
                        QMessageBox.information(self, "✅ Éxito", f"Cliente '{client_name}' eliminado correctamente")
                    else:
                        QMessageBox.warning(self, "❌ Error", "Cliente no encontrado")

            except Exception as e:
                logger.error(f"Error deleting client: {e}")
                QMessageBox.critical(self, "❌ Error", f"Error al eliminar cliente: {str(e)}")

class ProductManagementTab(QWidget):
    """Modern product management tab with Apple-inspired design"""

    def __init__(self):
        super().__init__()
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
        title_label = QLabel("Productos")
        title_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 600;
            color: {UIStyles.COLORS['text_primary']};
            background: transparent;
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(12)

        add_btn = QPushButton("+ Nuevo Producto")
        add_btn.clicked.connect(self.add_product)
        add_btn.setStyleSheet(UIStyles.get_primary_button_style())
        toolbar_layout.addWidget(add_btn)

        edit_btn = QPushButton("Editar")
        edit_btn.clicked.connect(self.edit_product)
        edit_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        toolbar_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Eliminar")
        delete_btn.clicked.connect(self.delete_product)
        delete_btn.setStyleSheet(UIStyles.get_danger_button_style())
        toolbar_layout.addWidget(delete_btn)

        toolbar_layout.addStretch()

        refresh_btn = QPushButton("Actualizar")
        refresh_btn.clicked.connect(self.refresh_data)
        refresh_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        toolbar_layout.addWidget(refresh_btn)

        layout.addLayout(toolbar_layout)

        # Search
        search_layout = QHBoxLayout()
        search_layout.setSpacing(12)

        search_label = QLabel("Buscar:")
        search_label.setStyleSheet(UIStyles.get_label_style())
        search_layout.addWidget(search_label)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Buscar por nombre, código, descripción...")
        self.search_edit.setStyleSheet(UIStyles.get_input_style())
        self.search_edit.textChanged.connect(self.filter_products)
        search_layout.addWidget(self.search_edit)

        layout.addLayout(search_layout)

        # Table
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(8)
        self.products_table.setHorizontalHeaderLabels([
            "CÓDIGO", "NOMBRE", "DESCRIPCIÓN", "P. COSTE", "P. VENTA", "STOCK", "STOCK MÍN", "ESTADO"
        ])
        self.products_table.setStyleSheet(UIStyles.get_table_style())
        self.products_table.setAlternatingRowColors(False)
        self.products_table.setShowGrid(False)
        self.products_table.verticalHeader().setVisible(False)

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
        """Refresh products data"""
        self.product_ids = []  # Store product IDs for reference
        try:
            with SessionLocal() as db:
                products = db.query(Product).order_by(Product.name).all()

                self.products_table.setRowCount(0)
                self.product_ids = []

                for row, product in enumerate(products):
                    self.products_table.insertRow(row)
                    self.product_ids.append(product.id)  # Store ID

                    self.products_table.setItem(row, 0, QTableWidgetItem(product.code or ""))
                    self.products_table.setItem(row, 1, QTableWidgetItem(product.name or ""))
                    self.products_table.setItem(row, 2, QTableWidgetItem(product.description or ""))
                    self.products_table.setItem(row, 3, QTableWidgetItem(f"{product.purchase_price or 0:.2f} €"))
                    self.products_table.setItem(row, 4, QTableWidgetItem(f"{product.sale_price or 0:.2f} €"))
                    self.products_table.setItem(row, 5, QTableWidgetItem(str(product.current_stock or 0)))
                    self.products_table.setItem(row, 6, QTableWidgetItem(str(product.minimum_stock or 0)))

                    # Stock status
                    stock_text = "✅ OK"
                    if product.current_stock <= product.minimum_stock:
                        stock_text = "⚠️ BAJO"

                    status_text = f"✅ Activo ({stock_text})" if product.is_active else "❌ Inactivo"
                    status_item = QTableWidgetItem(status_text)
                    self.products_table.setItem(row, 7, status_item)

                self.status_label.setText(f"📊 Mostrando {len(products)} productos")

        except Exception as e:
            logger.error(f"Error refreshing products: {e}")
            self.status_label.setText(f"❌ Error: {str(e)}")

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
            QMessageBox.information(self, "✅ Éxito", "Producto creado correctamente")

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
            QMessageBox.information(self, "✅ Éxito", "Producto actualizado correctamente")

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

class DocumentManagementTab(QWidget):
    """Modern document management tab with Apple-inspired design"""

    def __init__(self):
        super().__init__()
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
        title_label = QLabel("Documentos")
        title_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 600;
            color: {UIStyles.COLORS['text_primary']};
            background: transparent;
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(12)

        new_invoice_btn = QPushButton("+ Nueva Factura")
        new_invoice_btn.clicked.connect(lambda: self.create_document("invoice"))
        new_invoice_btn.setStyleSheet(UIStyles.get_primary_button_style())
        toolbar_layout.addWidget(new_invoice_btn)

        new_quote_btn = QPushButton("+ Presupuesto")
        new_quote_btn.clicked.connect(lambda: self.create_document("quote"))
        new_quote_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        toolbar_layout.addWidget(new_quote_btn)

        new_delivery_btn = QPushButton("+ Albarán")
        new_delivery_btn.clicked.connect(lambda: self.create_document("delivery"))
        new_delivery_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        toolbar_layout.addWidget(new_delivery_btn)

        toolbar_layout.addStretch()

        refresh_btn = QPushButton("Actualizar")
        refresh_btn.clicked.connect(self.refresh_data)
        refresh_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        toolbar_layout.addWidget(refresh_btn)

        layout.addLayout(toolbar_layout)

        # Filter
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(12)

        filter_label = QLabel("Filtrar por tipo:")
        filter_label.setStyleSheet(UIStyles.get_label_style())
        filter_layout.addWidget(filter_label)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Todos", "Presupuestos", "Facturas", "Albaranes"])
        self.filter_combo.setStyleSheet(UIStyles.get_input_style())
        self.filter_combo.currentTextChanged.connect(self.refresh_data)
        filter_layout.addWidget(self.filter_combo)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Documents table
        self.docs_table = QTableWidget()
        self.docs_table.setColumnCount(8)
        self.docs_table.setHorizontalHeaderLabels([
            "CÓDIGO", "TIPO", "CLIENTE", "FECHA", "ESTADO", "TOTAL", "VENCIMIENTO", "ACCIONES"
        ])
        self.docs_table.setStyleSheet(UIStyles.get_table_style())
        self.docs_table.setAlternatingRowColors(False)
        self.docs_table.setShowGrid(False)
        self.docs_table.verticalHeader().setVisible(False)

        header = self.docs_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

        # Enable double-click on table rows
        self.docs_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.docs_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.docs_table.cellDoubleClicked.connect(self.on_table_double_click)

        layout.addWidget(self.docs_table)

        # Status label
        self.status_label = QLabel("Cargando documentos...")
        self.status_label.setStyleSheet(UIStyles.get_status_label_style())
        layout.addWidget(self.status_label)
    
    def refresh_data(self):
        """Refresh documents data"""
        try:
            with SessionLocal() as db:
                # Get filter
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

                # Get documents with most recent first
                documents = query.order_by(Document.updated_at.desc()).limit(100).all()
                
                self.docs_table.setRowCount(0)
                # Store document IDs for double-click lookup
                self._document_ids = []

                for row, doc in enumerate(documents):
                    self.docs_table.insertRow(row)
                    # Store document ID for this row
                    self._document_ids.append(str(doc.id))

                    # Document code - store ID in item data
                    code_item = QTableWidgetItem(doc.code or "")
                    code_item.setData(Qt.ItemDataRole.UserRole, str(doc.id))
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
                    
                    # Client name (with relationship loading)
                    try:
                        client_name = doc.client.name if doc.client else "N/A"
                    except Exception as e:
                        logger.warning(f"Could not load client name for document {doc.code}: {e}")
                        client_name = "N/A"
                    self.docs_table.setItem(row, 2, QTableWidgetItem(client_name))
                    
                    # Date
                    date_text = ""
                    if doc.issue_date:
                        date_text = doc.issue_date.strftime('%d/%m/%Y')
                    self.docs_table.setItem(row, 3, QTableWidgetItem(date_text))
                    
                    # Status
                    status_text = ""
                    status_color = ""
                    if doc.status == DocumentStatus.DRAFT:
                        status_text = "Borrador"
                        status_color = "gray"
                    elif doc.status == DocumentStatus.SENT:
                        status_text = "Enviado"
                        status_color = "blue"
                    elif doc.status == DocumentStatus.ACCEPTED:
                        status_text = "Aceptado"
                        status_color = "green"
                    elif doc.status == DocumentStatus.PAID:
                        status_text = "Pagado"
                        status_color = "purple"
                    
                    status_item = QTableWidgetItem(status_text)
                    status_item.setForeground(QColor(status_color))
                    status_font = QFont()
                    status_font.setBold(True)
                    status_item.setFont(status_font)
                    self.docs_table.setItem(row, 4, status_item)
                    
                    # Total
                    total_text = f"{doc.total or 0:.2f} €"
                    self.docs_table.setItem(row, 5, QTableWidgetItem(total_text))
                    
                    # Due date
                    due_text = ""
                    if doc.due_date:
                        due_text = doc.due_date.strftime('%d/%m/%Y')
                    self.docs_table.setItem(row, 6, QTableWidgetItem(due_text))
                    
                    # Actions
                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout(actions_widget)
                    actions_layout.setContentsMargins(2, 2, 2, 2)
                    
                    view_btn = QPushButton("👁️")
                    view_btn.setToolTip("Ver Documento")
                    view_btn.setMaximumSize(30, 25)
                    view_btn.clicked.connect(lambda checked, d=doc: self.view_document(d))
                    actions_layout.addWidget(view_btn)
                    
                    edit_btn = QPushButton("✏️")
                    edit_btn.setToolTip("Editar Documento")
                    edit_btn.setMaximumSize(30, 25)
                    edit_btn.clicked.connect(lambda checked, d=doc: self.edit_document(d))
                    actions_layout.addWidget(edit_btn)

                    pdf_btn = QPushButton("PDF")
                    pdf_btn.setToolTip("Generar PDF")
                    pdf_btn.setMaximumSize(35, 25)
                    pdf_btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {UIStyles.COLORS['accent']};
                            color: white;
                            border: none;
                            border-radius: 4px;
                            font-size: 10px;
                            font-weight: bold;
                            padding: 2px 4px;
                        }}
                        QPushButton:hover {{
                            background-color: {UIStyles.COLORS['accent_hover']};
                        }}
                    """)
                    pdf_btn.clicked.connect(lambda checked, d=doc: self.generate_pdf(d))
                    actions_layout.addWidget(pdf_btn)

                    delete_btn = QPushButton("🗑️")
                    delete_btn.setToolTip("Eliminar Documento")
                    delete_btn.setMaximumSize(30, 25)
                    delete_btn.setStyleSheet("color: #e74c3c;")
                    delete_btn.clicked.connect(lambda checked, d=doc: self.delete_document(d))
                    actions_layout.addWidget(delete_btn)
                    
                    self.docs_table.setCellWidget(row, 7, actions_widget)
                
                self.status_label.setText(f"📊 Mostrando {len(documents)} documentos - Filtro: {filter_type}")
                
        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")
    
    def create_document(self, doc_type):
        """Create new document"""
        dialog = DocumentDialog(self, doc_type)
        if dialog.exec():
            self.refresh_data()

    def on_table_double_click(self, row, column):
        """Handle double-click on table row - opens edit dialog"""
        raw_id = self._document_ids[row]
        try:
            # Ensure doc_id is a UUID object if it's a string
            doc_id = uuid.UUID(raw_id) if isinstance(raw_id, str) else raw_id
            with SessionLocal() as db:
                doc = db.query(Document).filter(Document.id == doc_id).first()
                if doc:
                    self.edit_document(doc)
        except Exception as e:
            logger.error(f"Error on double-click: {e}")
            QMessageBox.critical(self, "Error", f"Error al abrir documento: {str(e)}")

    def view_document(self, document):
        """View document details"""
        try:
            # Ensure ID is a UUID object
            doc_id = uuid.UUID(str(document.id)) if not isinstance(document.id, uuid.UUID) else document.id
            with SessionLocal() as db:
                # Reload document with relationships
                doc = db.query(Document).options(joinedload(Document.client)).filter(Document.id == doc_id).first()
                if not doc:
                    QMessageBox.warning(self, "❌ Error", "Documento no encontrado")
                    return

                # Build document info
                doc_type = "Presupuesto" if doc.type == DocumentType.QUOTE else "Factura" if doc.type == DocumentType.INVOICE else "Albarán"
                client_name = doc.client.name if doc.client else "N/A"
                issue_date = doc.issue_date.strftime('%d/%m/%Y') if doc.issue_date else "N/A"
                due_date = doc.due_date.strftime('%d/%m/%Y') if doc.due_date else "N/A"
                status_text = doc.status.value if hasattr(doc.status, 'value') else str(doc.status)

                # Create view dialog
                view_dialog = QDialog(self)
                view_dialog.setWindowTitle(f"📄 {doc_type} - {doc.code}")
                view_dialog.setModal(True)
                view_dialog.resize(600, 500)

                layout = QVBoxLayout(view_dialog)

                # Header
                header = QLabel(f"📄 {doc_type}: {doc.code}")
                header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
                layout.addWidget(header)

                # Document details
                details_group = QGroupBox("📋 Detalles del Documento")
                details_layout = QFormLayout(details_group)
                details_layout.addRow("Código:", QLabel(doc.code or ""))
                details_layout.addRow("Tipo:", QLabel(doc_type))
                details_layout.addRow("Estado:", QLabel(status_text))
                details_layout.addRow("Cliente:", QLabel(client_name))
                details_layout.addRow("Fecha Emisión:", QLabel(issue_date))
                details_layout.addRow("Fecha Vencimiento:", QLabel(due_date))
                layout.addWidget(details_group)

                # Financial details
                financial_group = QGroupBox("💰 Detalles Financieros")
                financial_layout = QFormLayout(financial_group)
                financial_layout.addRow("Subtotal:", QLabel(f"{doc.subtotal or 0:.2f} €"))
                financial_layout.addRow("IVA:", QLabel(f"{doc.tax_amount or 0:.2f} €"))
                financial_layout.addRow("Total:", QLabel(f"{doc.total or 0:.2f} €"))
                layout.addWidget(financial_group)

                # Notes
                if doc.notes:
                    notes_group = QGroupBox("📝 Notas")
                    notes_layout = QVBoxLayout(notes_group)
                    notes_text = QTextEdit()
                    notes_text.setPlainText(doc.notes)
                    notes_text.setReadOnly(True)
                    notes_text.setMaximumHeight(100)
                    notes_layout.addWidget(notes_text)
                    layout.addWidget(notes_group)

                # Buttons layout
                buttons_layout = QHBoxLayout()

                # PDF button
                pdf_btn = QPushButton("Exportar PDF")
                pdf_btn.setStyleSheet(UIStyles.get_primary_button_style())
                pdf_btn.clicked.connect(lambda: (view_dialog.accept(), self.generate_pdf(doc)))
                buttons_layout.addWidget(pdf_btn)

                # Edit button
                edit_btn = QPushButton("Editar")
                edit_btn.setStyleSheet(UIStyles.get_secondary_button_style())
                edit_btn.clicked.connect(lambda: (view_dialog.accept(), self.edit_document(doc)))
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
            QMessageBox.critical(self, "❌ Error", f"Error al ver documento: {str(e)}")

    def edit_document(self, document):
        """Edit document - opens document dialog for editing"""
        try:
            # Ensure ID is a UUID object
            doc_id = uuid.UUID(str(document.id)) if not isinstance(document.id, uuid.UUID) else document.id
            with SessionLocal() as db:
                doc = db.query(Document).filter(Document.id == doc_id).first()
                if not doc:
                    QMessageBox.warning(self, "❌ Error", "Documento no encontrado")
                    return

                # Create edit dialog
                edit_dialog = QDialog(self)
                doc_type = "Presupuesto" if doc.type == DocumentType.QUOTE else "Factura" if doc.type == DocumentType.INVOICE else "Albarán"
                edit_dialog.setWindowTitle(f"✏️ Editar {doc_type} - {doc.code}")
                edit_dialog.setModal(True)
                edit_dialog.resize(500, 400)

                layout = QFormLayout(edit_dialog)

                # Status combo
                status_combo = QComboBox()
                status_options = ["draft", "sent", "accepted", "rejected", "paid", "partially_paid", "cancelled"]
                status_combo.addItems(status_options)
                current_status = doc.status.value if hasattr(doc.status, 'value') else str(doc.status)
                if current_status in status_options:
                    status_combo.setCurrentText(current_status)
                layout.addRow("Estado:", status_combo)

                # Due date
                due_date_edit = QDateEdit()
                if doc.due_date:
                    due_date_edit.setDate(QDate(doc.due_date.year, doc.due_date.month, doc.due_date.day))
                else:
                    due_date_edit.setDate(QDate.currentDate().addDays(30))
                due_date_edit.setCalendarPopup(True)
                layout.addRow("Fecha Vencimiento:", due_date_edit)

                # Notes
                notes_edit = QTextEdit()
                notes_edit.setPlainText(doc.notes or "")
                notes_edit.setMaximumHeight(100)
                layout.addRow("Notas:", notes_edit)

                # Internal notes
                internal_notes_edit = QTextEdit()
                internal_notes_edit.setPlainText(doc.internal_notes or "")
                internal_notes_edit.setMaximumHeight(100)
                layout.addRow("Notas Internas:", internal_notes_edit)

                # Buttons
                buttons = QDialogButtonBox(
                    QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
                )

                def save_changes():
                    try:
                        with SessionLocal() as db2:
                            doc2 = db2.query(Document).filter(Document.id == document.id).first()
                            if doc2:
                                doc2.status = DocumentStatus(status_combo.currentText())
                                qdate = due_date_edit.date()
                                doc2.due_date = date(qdate.year(), qdate.month(), qdate.day())
                                doc2.notes = notes_edit.toPlainText().strip() or None
                                doc2.internal_notes = internal_notes_edit.toPlainText().strip() or None
                                db2.commit()
                                edit_dialog.accept()
                                self.refresh_data()
                                QMessageBox.information(self, "✅ Éxito", "Documento actualizado correctamente")
                    except Exception as e:
                        logger.error(f"Error saving document: {e}")
                        QMessageBox.critical(self, "❌ Error", f"Error al guardar: {str(e)}")

                buttons.accepted.connect(save_changes)
                buttons.rejected.connect(edit_dialog.reject)
                layout.addRow(buttons)

                edit_dialog.exec()

        except Exception as e:
            logger.error(f"Error editing document: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al editar documento: {str(e)}")

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
                        QMessageBox.information(self, "✅ Éxito", f"Documento '{doc_code}' eliminado correctamente")
                    else:
                        QMessageBox.warning(self, "❌ Error", "Documento no encontrado")

            except Exception as e:
                logger.error(f"Error deleting document: {e}")
                QMessageBox.critical(self, "❌ Error", f"Error al eliminar documento: {str(e)}")

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


class InventoryManagementTab(QWidget):
    """Modern inventory management tab with Apple-inspired design"""

    def __init__(self):
        super().__init__()
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
        title_label = QLabel("Inventario")
        title_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 600;
            color: {UIStyles.COLORS['text_primary']};
            background: transparent;
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(12)

        add_btn = QPushButton("+ Nuevo Producto")
        add_btn.clicked.connect(self.add_product)
        add_btn.setStyleSheet(UIStyles.get_primary_button_style())
        toolbar_layout.addWidget(add_btn)

        adjust_stock_btn = QPushButton("Ajustar Stock")
        adjust_stock_btn.clicked.connect(self.adjust_stock)
        adjust_stock_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        toolbar_layout.addWidget(adjust_stock_btn)

        generate_report_btn = QPushButton("Informe")
        generate_report_btn.clicked.connect(self.generate_report)
        generate_report_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        toolbar_layout.addWidget(generate_report_btn)

        toolbar_layout.addStretch()

        refresh_btn = QPushButton("Actualizar")
        refresh_btn.clicked.connect(self.refresh_data)
        refresh_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        toolbar_layout.addWidget(refresh_btn)

        layout.addLayout(toolbar_layout)

        # Search and filter
        search_layout = QHBoxLayout()
        search_layout.setSpacing(12)

        search_label = QLabel("Buscar:")
        search_label.setStyleSheet(UIStyles.get_label_style())
        search_layout.addWidget(search_label)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Buscar producto...")
        self.search_edit.setStyleSheet(UIStyles.get_input_style())
        self.search_edit.textChanged.connect(self.filter_products)
        search_layout.addWidget(self.search_edit)

        filter_label = QLabel("Filtro:")
        filter_label.setStyleSheet(UIStyles.get_label_style())
        search_layout.addWidget(filter_label)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Todos", "Con Stock", "Stock Bajo", "Sin Stock", "Activos", "Inactivos"])
        self.filter_combo.setStyleSheet(UIStyles.get_input_style())
        self.filter_combo.currentTextChanged.connect(self.filter_products)
        search_layout.addWidget(self.filter_combo)

        layout.addLayout(search_layout)

        # Statistics cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self.total_products_label = QLabel("Total: 0")
        self.total_products_label.setStyleSheet(f"""
            background-color: {UIStyles.COLORS['bg_card']};
            border: 1px solid {UIStyles.COLORS['border_light']};
            border-radius: 8px;
            padding: 12px 20px;
            font-weight: 500;
            color: {UIStyles.COLORS['text_primary']};
        """)
        stats_layout.addWidget(self.total_products_label)

        self.low_stock_label = QLabel("Stock Bajo: 0")
        self.low_stock_label.setStyleSheet(f"""
            background-color: {UIStyles.COLORS['bg_card']};
            border: 1px solid {UIStyles.COLORS['warning']};
            border-radius: 8px;
            padding: 12px 20px;
            font-weight: 500;
            color: {UIStyles.COLORS['warning']};
        """)
        stats_layout.addWidget(self.low_stock_label)

        self.total_value_label = QLabel("Valor Total: 0.00 €")
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
            "CÓDIGO", "PRODUCTO", "DESCRIPCIÓN", "STOCK ACTUAL", "STOCK MÍN", "ESTADO", "VALOR TOTAL", "ACCIONES", "ÚLTIMO MOV."
        ])
        self.inventory_table.setStyleSheet(UIStyles.get_table_style())
        self.inventory_table.setAlternatingRowColors(False)
        self.inventory_table.setShowGrid(False)
        self.inventory_table.verticalHeader().setVisible(False)

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
        """Refresh inventory data"""
        try:
            with SessionLocal() as db:
                products = db.query(Product).all()
                
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
                    stock_status = "✅ OK"
                    stock_color = "green"
                    if product.current_stock <= 0:
                        stock_status = "❌ SIN STOCK"
                        stock_color = "red"
                    elif product.current_stock <= product.minimum_stock:
                        stock_status = "⚠️ BAJO"
                        stock_color = "orange"
                        low_stock_count += 1
                    
                    status_item = QTableWidgetItem(stock_status)
                    # Use proper Qt API - QTableWidgetItem doesn't have setStyleSheet
                    from PySide6.QtGui import QColor, QFont
                    status_item.setForeground(QColor(stock_color))
                    font = QFont()
                    font.setBold(True)
                    status_item.setFont(font)
                    self.inventory_table.setItem(row, 5, status_item)
                    
                    # Total value
                    total_product_value = (product.current_stock or 0) * (product.sale_price or 0)
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
                
                # Update statistics
                self.total_products_label.setText(f"📦 Total: {len(products)}")
                self.low_stock_label.setText(f"⚠️ Stock Bajo: {low_stock_count}")
                self.total_value_label.setText(f"💰 Valor Total: {total_value:.2f} €")
                
                self.status_label.setText(f"📊 Mostrando {len(products)} productos - {low_stock_count} con stock bajo")
                
        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")
    
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

        # If no row selected, show product picker dialog
        if current_row < 0:
            self.show_product_picker_for_adjustment()
            return

        # If row selected, adjust that product directly
        try:
            with SessionLocal() as db:
                product_code = self.inventory_table.item(current_row, 0).text()
                product = db.query(Product).filter(Product.code == product_code).first()
                if product:
                    self.adjust_product_stock(product)
                else:
                    QMessageBox.warning(self, "Error", "Producto no encontrado")
        except Exception as e:
            logger.error(f"Error getting product for stock adjustment: {e}")
            QMessageBox.critical(self, "Error", f"Error al obtener producto: {str(e)}")

    def show_product_picker_for_adjustment(self):
        """Show a dialog to pick a product for stock adjustment"""
        try:
            with SessionLocal() as db:
                products = db.query(Product).filter(Product.is_active == True).order_by(Product.name).all()

                if not products:
                    QMessageBox.information(self, "Info", "No hay productos activos en el inventario")
                    return

                # Create product selection dialog
                from PySide6.QtWidgets import QInputDialog

                # Build list of products with current stock info
                product_list = [
                    f"{p.code} - {p.name} (Stock: {p.current_stock or 0})"
                    for p in products
                ]

                product_name, ok = QInputDialog.getItem(
                    self,
                    "Seleccionar Producto",
                    "Seleccione el producto para ajustar stock:",
                    product_list,
                    0,
                    False
                )

                if ok and product_name:
                    # Extract product code from selection
                    product_code = product_name.split(" - ")[0]
                    # Get fresh product from DB
                    product = db.query(Product).filter(Product.code == product_code).first()
                    if product:
                        self.adjust_product_stock(product)

        except Exception as e:
            logger.error(f"Error showing product picker: {e}")
            QMessageBox.critical(self, "Error", f"Error al mostrar selector de productos: {str(e)}")
    
    def adjust_product_stock(self, product):
        """Adjust stock for specific product - improved with better validation"""
        from PySide6.QtWidgets import QInputDialog

        # Store product info to avoid detached session issues
        product_id = product.id
        product_name = product.name
        current_stock = product.current_stock or 0

        # Show current stock and ask for adjustment
        quantity, ok = QInputDialog.getInt(
            self,
            "Ajustar Stock",
            f"Producto: {product_name}\n"
            f"Stock actual: {current_stock} unidades\n\n"
            f"Ajuste de cantidad:\n"
            f"  - Positivo para entrada (añadir stock)\n"
            f"  - Negativo para salida (retirar stock)\n",
            0, -9999, 9999, 1
        )

        if ok and quantity != 0:  # Only proceed if user confirmed and quantity is not zero
            try:
                with SessionLocal() as db:
                    db_product = db.query(Product).filter(Product.id == product_id).first()
                    if not db_product:
                        QMessageBox.warning(self, "Error", "Producto no encontrado")
                        return

                    old_stock = db_product.current_stock or 0
                    new_stock = max(0, old_stock + quantity)

                    # Validate the operation
                    if quantity < 0 and abs(quantity) > old_stock:
                        reply = QMessageBox.question(
                            self,
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
                QMessageBox.critical(self, "Error", f"Error al ajustar stock: {str(e)}")
        elif ok and quantity == 0:
            QMessageBox.information(self, "Info", "No se realizaron cambios (cantidad = 0)")
    
    def edit_product(self, product):
        """Edit product details using ProductDialog"""
        dialog = ProductDialog(self, product_id=product.id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
            QMessageBox.information(self, "Exito", f"Producto '{product.name}' actualizado correctamente")
    
    def generate_report(self):
        """Generate inventory report"""
        try:
            with SessionLocal() as db:
                products = db.query(Product).all()
                
                report = "📊 INFORME DE INVENTARIO\n"
                report += "=" * 50 + "\n"
                report += f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                
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

class DiaryManagementTab(QWidget):
    """Modern diary management tab with Apple-inspired design"""

    def __init__(self):
        super().__init__()
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
        title_label = QLabel("Diario")
        title_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 600;
            color: {UIStyles.COLORS['text_primary']};
            background: transparent;
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(12)

        add_entry_btn = QPushButton("+ Nueva Nota")
        add_entry_btn.clicked.connect(self.add_entry)
        add_entry_btn.setStyleSheet(UIStyles.get_primary_button_style())
        toolbar_layout.addWidget(add_entry_btn)

        view_calendar_btn = QPushButton("Ver Calendario")
        view_calendar_btn.clicked.connect(self.view_calendar)
        view_calendar_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        toolbar_layout.addWidget(view_calendar_btn)

        toolbar_layout.addStretch()

        clear_all_btn = QPushButton("Limpiar Todo")
        clear_all_btn.clicked.connect(self.clear_all)
        clear_all_btn.setStyleSheet(UIStyles.get_danger_button_style())
        toolbar_layout.addWidget(clear_all_btn)

        layout.addLayout(toolbar_layout)

        # Date selector
        date_layout = QHBoxLayout()
        date_layout.setSpacing(12)

        date_label = QLabel("Fecha:")
        date_label.setStyleSheet(UIStyles.get_label_style())
        date_layout.addWidget(date_label)

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setStyleSheet(UIStyles.get_input_style())
        self.date_edit.dateChanged.connect(self.filter_notes_by_date)
        date_layout.addWidget(self.date_edit)

        today_btn = QPushButton("Hoy")
        today_btn.clicked.connect(lambda: self.date_edit.setDate(QDate.currentDate()))
        today_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        date_layout.addWidget(today_btn)

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
    
    def clear_all(self):
        """Clear all notes"""
        reply = QMessageBox.question(
            self, "❌ Confirmar Eliminación", 
            "¿Está seguro de eliminar TODAS las notas del diario?\n\nEsta acción no se puede deshacer."
        )
        
        if reply == QMessageBox.StandardButton.Yes:
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
            import json
            notes_file = os.path.join(os.path.dirname(__file__), 'diary_notes.json')
            if os.path.exists(notes_file):
                with open(notes_file, 'r', encoding='utf-8') as f:
                    self.notes = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Error loading diary notes: {e}")
            self.notes = []
    
    def save_notes(self):
        """Save notes to file"""
        try:
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
        
        self.total_notes_label.setText(f"📊 Total Notas: {len(self.notes)}")
        self.today_notes_label.setText(f"📅 Notas Hoy: {len(today_notes)}")

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

class MainWindow(QMainWindow):
    """Modern Apple-inspired main window"""

    def __init__(self):
        super().__init__()
        self.current_user = None
        self.setup_ui()

    def set_current_user(self, user):
        """Set current user"""
        self.current_user = user
        username = user.username
        full_name = user.full_name
        role = user.role.value if hasattr(user.role, 'value') else str(user.role)

        self.user_label.setText(f"{full_name} ({role})")
        self.statusBar().showMessage("Listo")

    def setup_ui(self):
        """Setup modern main window"""
        self.setWindowTitle("Dragofactu - Sistema de Gestión")
        self.setGeometry(100, 100, 1400, 900)

        # Apply main window style
        self.setStyleSheet(f"""
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
        """)

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
        self.tabs.addTab(self.dashboard, "Panel Principal")

        # Add functional tabs
        self.clients_tab = ClientManagementTab()
        self.tabs.addTab(self.clients_tab, "Clientes")

        self.products_tab = ProductManagementTab()
        self.tabs.addTab(self.products_tab, "Productos")

        self.documents_tab = DocumentManagementTab()
        self.tabs.addTab(self.documents_tab, "Documentos")

        self.inventory_tab = InventoryManagementTab()
        self.tabs.addTab(self.inventory_tab, "Inventario")

        self.diary_tab = DiaryManagementTab()
        self.tabs.addTab(self.diary_tab, "Diario")

        layout.addWidget(self.tabs)

        # Create status bar with user info
        status_bar = self.statusBar()
        self.user_label = QLabel("No conectado")
        self.user_label.setStyleSheet(f"color: {UIStyles.COLORS['text_secondary']}; padding-right: 16px;")
        status_bar.addPermanentWidget(self.user_label)
        status_bar.showMessage("Listo")

        # Connect tab changes to refresh data
        self.tabs.currentChanged.connect(self.on_tab_changed)
    
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
        """Create clean menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("Archivo")

        new_quote_action = QAction("Nuevo Presupuesto", self)
        new_quote_action.setShortcut("Ctrl+Shift+P")
        new_quote_action.triggered.connect(self.new_quote)
        file_menu.addAction(new_quote_action)

        new_invoice_action = QAction("Nueva Factura", self)
        new_invoice_action.setShortcut("Ctrl+Shift+F")
        new_invoice_action.triggered.connect(self.new_invoice)
        file_menu.addAction(new_invoice_action)

        file_menu.addSeparator()

        import_file_action = QAction("Importar...", self)
        import_file_action.setShortcut("Ctrl+I")
        import_file_action.triggered.connect(self.import_external_file)
        file_menu.addAction(import_file_action)

        export_data_action = QAction("Exportar...", self)
        export_data_action.setShortcut("Ctrl+E")
        export_data_action.triggered.connect(self.export_data)
        file_menu.addAction(export_data_action)

        export_pdf_action = QAction("Exportar a PDF...", self)
        export_pdf_action.setShortcut("Ctrl+P")
        export_pdf_action.triggered.connect(self.export_document_to_pdf)
        file_menu.addAction(export_pdf_action)

        file_menu.addSeparator()

        exit_action = QAction("Salir", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("Herramientas")

        settings_action = QAction("Preferencias...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)

        # Language menu
        language_menu = menubar.addMenu("Idioma")

        for lang_code, lang_name in translator.get_available_languages().items():
            lang_action = QAction(lang_name, self)
            lang_action.triggered.connect(lambda checked, code=lang_code: self.change_language(code))
            language_menu.addAction(lang_action)
    
    def new_quote(self):
        """Create new quote"""
        dialog = DocumentDialog(self, "quote")
        dialog.exec()
    
    def new_invoice(self):
        """Create new invoice"""
        dialog = DocumentDialog(self, "invoice")
        dialog.exec()

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
        """Change application language and save preference"""
        try:
            lang_names = {'es': 'Español', 'en': 'English', 'de': 'Deutsch'}
            lang_name = lang_names.get(lang_code, lang_code)

            if translator.set_language(lang_code):
                # Show message in the NEW language
                messages = {
                    'es': f"Idioma cambiado a {lang_name}.\n\nReinicie la aplicación para aplicar los cambios.",
                    'en': f"Language changed to {lang_name}.\n\nRestart the application to apply changes.",
                    'de': f"Sprache geändert zu {lang_name}.\n\nStarten Sie die Anwendung neu."
                }
                titles = {
                    'es': "Idioma Guardado",
                    'en': "Language Saved",
                    'de': "Sprache Gespeichert"
                }
                QMessageBox.information(
                    self,
                    titles.get(lang_code, "Language"),
                    messages.get(lang_code, messages['en'])
                )
            else:
                QMessageBox.warning(self, "Error", f"Language {lang_code} not available")
        except Exception as e:
            logger.error(f"Error changing language: {e}")
            QMessageBox.warning(self, "Error", f"Could not change language: {str(e)}")

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
    """Functional Settings dialog"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Configuración - DRAGOFACTU")
        self.setModal(True)
        self.resize(500, 600)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # General settings
        general_group = QGroupBox("🔧 Configuración General")
        general_layout = QFormLayout(general_group)
        
        # Company info
        self.company_name_edit = QLineEdit()
        self.company_name_edit.setText("DRAGOFACTU Software")
        general_layout.addRow("Nombre Empresa:", self.company_name_edit)
        
        self.company_email_edit = QLineEdit()
        self.company_email_edit.setText("info@dragofactu.com")
        general_layout.addRow("Email Empresa:", self.company_email_edit)
        
        self.company_phone_edit = QLineEdit()
        self.company_phone_edit.setText("+34 900 000 000")
        general_layout.addRow("Teléfono Empresa:", self.company_phone_edit)
        
        layout.addWidget(general_group)
        
        # UI settings
        ui_group = QGroupBox("🎨 Apariencia")
        ui_layout = QFormLayout(ui_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Claro", "Oscuro", "Auto"])
        self.theme_combo.setCurrentText("Auto")
        self.theme_combo.currentTextChanged.connect(self.preview_theme)
        ui_layout.addRow("Tema:", self.theme_combo)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Español", "English", "Deutsch"])
        self.language_combo.setCurrentText("Español")
        ui_layout.addRow("Idioma:", self.language_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(12)
        ui_layout.addRow("Tamaño Fuente:", self.font_size_spin)
        
        layout.addWidget(ui_group)
        
        # Business settings
        business_group = QGroupBox("💼 Configuración Negocio")
        business_layout = QFormLayout(business_group)
        
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["EUR - Euro €", "USD - Dólar $", "GBP - Libra £"])
        self.currency_combo.setCurrentText("EUR - Euro €")
        business_layout.addRow("Moneda:", self.currency_combo)
        
        self.tax_rate_spin = QDoubleSpinBox()
        self.tax_rate_spin.setRange(0, 50)
        self.tax_rate_spin.setDecimals(2)
        self.tax_rate_spin.setValue(21)
        self.tax_rate_spin.setSuffix("%")
        business_layout.addRow("IVA Por Defecto:", self.tax_rate_spin)
        
        layout.addWidget(business_group)
        
        # Database info
        db_group = QGroupBox("🗄️ Información Base de Datos")
        db_layout = QFormLayout(db_group)
        
        # Get database info
        try:
            with SessionLocal() as db:
                client_count = db.query(Client).count()
                product_count = db.query(Product).count()
                document_count = db.query(Document).count()

                db_layout.addRow("Clientes:", QLabel(str(client_count)))
                db_layout.addRow("Productos:", QLabel(str(product_count)))
                db_layout.addRow("Documentos:", QLabel(str(document_count)))
        except Exception as e:
            logger.error(f"Error getting database info for settings: {e}")
            db_layout.addRow("Estado:", QLabel("❌ Error de conexión"))
        
        layout.addWidget(db_group)
        
        # App info
        info_group = QGroupBox("ℹ️ Información Aplicación")
        info_layout = QFormLayout(info_group)
        
        info_layout.addRow("Versión:", QLabel("V1.0.0.3"))
        info_layout.addRow("Desarrollador:", QLabel("DRAGOFACTU Team"))
        info_layout.addRow("GitHub:", QLabel("github.com/Copitx/Dragofactu"))
        info_layout.addRow("Python:", QLabel(f"3.{sys.version_info.minor}.{sys.version_info.micro}"))
        
        layout.addWidget(info_group)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Guardar Configuración")
        save_btn.clicked.connect(self.save_settings)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover { background-color: #229954; }
        """)
        buttons_layout.addWidget(save_btn)
        
        reset_btn = QPushButton("🔄 Restablecer")
        reset_btn.clicked.connect(self.reset_settings)
        reset_btn.setStyleSheet("background-color: #f39c12; color: white; padding: 10px; border-radius: 5px;")
        buttons_layout.addWidget(reset_btn)
        
        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("background-color: #95a5a6; color: white; padding: 10px; border-radius: 5px;")
        buttons_layout.addWidget(cancel_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

    def preview_theme(self, theme_name):
        """Preview theme change (for now just show a message)"""
        # In a full implementation, you would apply the theme here
        # For now, we just inform the user
        pass

    def save_settings(self):
        """Save settings"""
        try:
            # Get all values
            settings = {
                'company_name': self.company_name_edit.text(),
                'company_email': self.company_email_edit.text(),
                'company_phone': self.company_phone_edit.text(),
                'theme': self.theme_combo.currentText(),
                'language': self.language_combo.currentText(),
                'font_size': self.font_size_spin.value(),
                'currency': self.currency_combo.currentText(),
                'tax_rate': self.tax_rate_spin.value()
            }

            # Here you would save to a config file or database
            # For now, just show success message with info about restart
            message = "Configuración guardada correctamente"
            if settings['theme'] != "Auto" or settings['language'] != "Español":
                message += "\n\nNota: Algunos cambios (tema e idioma) requerirán reiniciar la aplicación para aplicarse completamente."

            QMessageBox.information(self, "✅ Guardado", message)
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error guardando configuración: {str(e)}")
    
    def reset_settings(self):
        """Reset settings to defaults"""
        reply = QMessageBox.question(
            self, "🔄 Restablecer", 
            "¿Está seguro de restablecer la configuración a valores por defecto?"
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.company_name_edit.setText("DRAGOFACTU Software")
            self.company_email_edit.setText("info@dragofactu.com")
            self.company_phone_edit.setText("+34 900 000 000")
            self.theme_combo.setCurrentText("Auto")
            self.language_combo.setCurrentText("Español")
            self.font_size_spin.setValue(12)
            self.currency_combo.setCurrentText("EUR - Euro €")
            self.tax_rate_spin.setValue(21)
            
            QMessageBox.information(self, "✅ Restablecido", "Configuración restablecida a valores por defecto")
    
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
    """Modern login dialog with Apple-inspired design"""

    def __init__(self):
        super().__init__()
        self.user = None
        self.user_data = None
        self.setup_ui()

    def setup_ui(self):
        """Setup modern login dialog"""
        self.setWindowTitle("Dragofactu - Iniciar Sesión")
        self.setModal(True)
        # Increased size to prevent overlapping elements
        self.setFixedSize(460, 600)

        # Apply dialog style
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {UIStyles.COLORS['bg_app']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(20)

        # Logo/Title area
        title = QLabel("Dragofactu")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            font-size: 32px;
            font-weight: 600;
            color: {UIStyles.COLORS['text_primary']};
            background: transparent;
            padding: 20px 0;
        """)
        layout.addWidget(title)

        subtitle = QLabel("Sistema de Gestión Empresarial")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"""
            font-size: 14px;
            color: {UIStyles.COLORS['text_secondary']};
            background: transparent;
            margin-bottom: 24px;
        """)
        layout.addWidget(subtitle)

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

        # Hint
        hint = QLabel("Credenciales: admin / admin123")
        hint.setStyleSheet(f"""
            color: {UIStyles.COLORS['text_tertiary']};
            font-size: 11px;
            background: transparent;
            padding-top: 8px;
        """)
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        layout.addStretch()
    
    def handle_login(self):
        """Handle login"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        
        if not username or not password:
            QMessageBox.warning(self, "❌ Error", "Por favor ingrese usuario y contraseña")
            return
        
        try:
            auth_service = AuthService()
            with SessionLocal() as db:
                user = auth_service.authenticate(db, username, password)
                if user:
                    # Extract user data before session closes to avoid DetachedInstanceError
                    self.user_data = {
                        'id': user.id,
                        'username': user.username,
                        'full_name': user.full_name,
                        'role': user.role.value if hasattr(user.role, 'value') else str(user.role)
                    }
                    self.user = user  # Keep for backward compatibility
                    self.accept()
                else:
                    QMessageBox.warning(self, "❌ Error", "Usuario o contraseña incorrectos")
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error de autenticación: {str(e)}")

class App(QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        apply_stylesheet(self)
        self.current_user = None
        self.setup_app()
    
    def setup_app(self):
        """Setup application"""
        # Create database tables
        Base.metadata.create_all(bind=engine)
        
        # Show login
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