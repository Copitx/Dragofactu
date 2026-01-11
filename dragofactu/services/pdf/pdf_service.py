from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import os
import tempfile

from dragofactu.config.config import AppConfig
from dragofactu.models.entities import Document, DocumentLine, Client


class PDFService:
    """Service for generating PDF documents"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
        # Company information
        self.company_name = AppConfig.PDF_COMPANY_NAME
        self.company_address = AppConfig.PDF_COMPANY_ADDRESS
        self.company_phone = AppConfig.PDF_COMPANY_PHONE
        self.company_email = AppConfig.PDF_COMPANY_EMAIL
        self.company_cif = AppConfig.PDF_COMPANY_CIF
        self.logo_path = AppConfig.PDF_LOGO_PATH
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Company header style
        self.styles.add(ParagraphStyle(
            name='CompanyHeader',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=12,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Document title style
        self.styles.add(ParagraphStyle(
            name='DocumentTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            alignment=TA_CENTER
        ))
        
        # Client info style
        self.styles.add(ParagraphStyle(
            name='ClientInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.grey
        ))
    
    def generate_document_pdf(self, document: Document, client: Client, 
                             lines: list, file_path: str = None) -> str:
        """
        Generate PDF for a document (quote, invoice, delivery note)
        
        Args:
            document: Document entity
            client: Client entity
            lines: List of DocumentLine objects
            file_path: Optional file path, generates temp file if None
            
        Returns:
            Path to generated PDF file
        """
        if not file_path:
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, f"{document.code}.pdf")
        
        # Create PDF document
        doc = SimpleDocTemplate(
            file_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build document content
        story = []
        
        # Header section
        story.extend(self._build_header(document))
        story.append(Spacer(1, 20))
        
        # Client information
        story.extend(self._build_client_info(client))
        story.append(Spacer(1, 20))
        
        # Document lines table
        story.extend(self._build_document_table(lines))
        story.append(Spacer(1, 20))
        
        # Totals section
        story.extend(self._build_totals(document))
        story.append(Spacer(1, 30))
        
        # Notes and terms
        if document.notes or document.terms:
            story.extend(self._build_notes(document))
        
        # Footer
        story.extend(self._build_footer())
        
        # Generate PDF
        doc.build(story)
        
        return file_path
    
    def _build_header(self, document: Document) -> list:
        """Build document header"""
        elements = []
        
        # Company name
        elements.append(Paragraph(self.company_name, self.styles['CompanyHeader']))
        
        # Document type and code
        doc_type_map = {
            'quote': 'QUOTE',
            'invoice': 'INVOICE',
            'delivery_note': 'DELIVERY NOTE'
        }
        doc_title = f"{doc_type_map.get(document.type.value, 'DOCUMENT')} {document.code}"
        elements.append(Paragraph(doc_title, self.styles['DocumentTitle']))
        
        # Document dates
        date_info = [
            f"Date: {document.issue_date.strftime('%d/%m/%Y')}",
            f"Due: {document.due_date.strftime('%d/%m/%Y') if document.due_date else 'N/A'}"
        ]
        
        date_table = Table([date_info], colWidths=[2*inch, 2*inch])
        date_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(date_table)
        
        return elements
    
    def _build_client_info(self, client: Client) -> list:
        """Build client information section"""
        elements = []
        
        # Client details
        client_info = []
        
        if client.name:
            client_info.append(f"Client: {client.name}")
        
        if client.address:
            client_info.append(f"Address: {client.address}")
        
        if client.phone:
            client_info.append(f"Phone: {client.phone}")
        
        if client.email:
            client_info.append(f"Email: {client.email}")
        
        if client.tax_id:
            client_info.append(f"Tax ID: {client.tax_id}")
        
        # Company info on the right
        company_info = []
        company_info.append(f"CIF: {self.company_cif}")
        company_info.append(f"Phone: {self.company_phone}")
        company_info.append(f"Email: {self.company_email}")
        if self.company_address:
            company_info.append(f"Address: {self.company_address}")
        
        # Create table with client and company info
        table_data = []
        max_rows = max(len(client_info), len(company_info))
        
        for i in range(max_rows):
            client_row = client_info[i] if i < len(client_info) else ""
            company_row = company_info[i] if i < len(company_info) else ""
            table_data.append([client_row, company_row])
        
        info_table = Table(table_data, colWidths=[3*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(info_table)
        
        return elements
    
    def _build_document_table(self, lines: list) -> list:
        """Build document lines table"""
        elements = []
        
        # Table headers
        headers = [
            "Description",
            "Qty",
            "Unit Price",
            "Discount",
            "Subtotal"
        ]
        
        # Table data
        table_data = [headers]
        
        for line in lines:
            description = line.description or ""
            quantity = str(line.quantity) if line.quantity else ""
            unit_price = f"{line.unit_price:.2f}" if line.unit_price else ""
            discount = f"{line.discount_percent:.2f}%" if line.discount_percent else ""
            subtotal = f"{line.subtotal:.2f}" if line.subtotal else ""
            
            table_data.append([
                description,
                quantity,
                unit_price,
                discount,
                subtotal
            ])
        
        # Create table
        table = Table(table_data, colWidths=[3*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
        
        # Style table
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            
            # Data styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _build_totals(self, document: Document) -> list:
        """Build totals section"""
        elements = []
        
        # Totals data
        totals_data = [
            ["Subtotal:", f"{document.subtotal:.2f}" if document.subtotal else "0.00"],
            ["Tax (21%):", f"{document.tax_amount:.2f}" if document.tax_amount else "0.00"],
            ["TOTAL:", f"{document.total:.2f}" if document.total else "0.00"]
        ]
        
        # Create totals table
        totals_table = Table(totals_data, colWidths=[4*inch, 1.5*inch])
        
        # Style totals table
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-2, -2), 'Helvetica'),
            ('FONTNAME', (-1, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (-1, -1), (-1, -1), colors.darkblue),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LINEBELOW', (0, 2), (-1, 2), 2, colors.darkblue),
        ]))
        
        elements.append(totals_table)
        
        return elements
    
    def _build_notes(self, document: Document) -> list:
        """Build notes and terms section"""
        elements = []
        
        if document.notes:
            elements.append(Paragraph("Notes:", self.styles['Heading3']))
            elements.append(Paragraph(document.notes, self.styles['Normal']))
            elements.append(Spacer(1, 12))
        
        if document.terms:
            elements.append(Paragraph("Terms:", self.styles['Heading3']))
            elements.append(Paragraph(document.terms, self.styles['Normal']))
        
        return elements
    
    def _build_footer(self) -> list:
        """Build document footer"""
        elements = []
        
        footer_text = f"""
        {self.company_name} | CIF: {self.company_cif}
        {self.company_address} | {self.company_phone} | {self.company_email}
        Generated on {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        """
        
        elements.append(Paragraph(footer_text, self.styles['Footer']))
        
        return elements
    
    def generate_report_pdf(self, report_data: Dict[str, Any], title: str, 
                          file_path: str = None) -> str:
        """
        Generate PDF for reports
        
        Args:
            report_data: Report data dictionary
            title: Report title
            file_path: Optional file path
            
        Returns:
            Path to generated PDF file
        """
        if not file_path:
            temp_dir = tempfile.gettempdir()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = os.path.join(temp_dir, f"report_{title}_{timestamp}.pdf")
        
        # Create PDF document
        doc = SimpleDocTemplate(
            file_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build report content
        story = []
        
        # Report title
        story.append(Paragraph(title, self.styles['CompanyHeader']))
        story.append(Spacer(1, 20))
        
        # Report date
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 20))
        
        # Report content
        for key, value in report_data.items():
            story.append(Paragraph(f"{key}:", self.styles['Heading3']))
            story.append(Paragraph(str(value), self.styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Footer
        story.extend(self._build_footer())
        
        # Generate PDF
        doc.build(story)
        
        return file_path