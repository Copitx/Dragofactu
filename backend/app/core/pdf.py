"""
PDF generation service for documents.
Uses ReportLab to generate PDF invoices, quotes, and delivery notes.
"""
from datetime import datetime
from io import BytesIO
from typing import Optional
from uuid import UUID

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus.tableofcontents import TableOfContents
from sqlalchemy.orm import Session

from app.models import Document, DocumentLine, Client


class InvoicePDFGenerator:
    """Generate PDF invoices using ReportLab."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='DocumentTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=HexColor('#1D1D1F'),
            alignment=1  # Center
        ))

        # Header info style
        self.styles.add(ParagraphStyle(
            name='HeaderInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=2,
            textColor=HexColor('#6E6E73')
        ))

        # Section title style
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=20,
            textColor=HexColor('#1D1D1F')
        ))

    def generate_pdf(self, document: Document, buffer: BytesIO) -> None:
        """Generate PDF document into provided buffer."""
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Build story (content elements)
        story = []

        # Document title and type
        doc_type_map = {
            'quote': 'PRESUPUESTO',
            'delivery_note': 'ALBARAN',
            'invoice': 'FACTURA'
        }
        doc_title = doc_type_map.get(document.type.value, 'DOCUMENTO')
        story.append(Paragraph(doc_title, self.styles['DocumentTitle']))
        story.append(Spacer(1, 20))

        # Document info table (code, date, etc.)
        doc_info = [
            ['Código:', document.code],
            ['Fecha:', document.issue_date.strftime('%d/%m/%Y')],
            ['Estado:', self._get_status_label(document.status.value)]
        ]

        if document.due_date:
            doc_info.append(['Vencimiento:', document.due_date.strftime('%d/%m/%Y')])

        doc_table = Table(doc_info, colWidths=[60*mm, 80*mm])
        doc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#F5F5F7')),
            ('TEXTCOLOR', (0, 0), (-1, -1), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#E5E5EA'))
        ]))
        story.append(doc_table)
        story.append(Spacer(1, 20))

        # Client and company info
        if document.client:
            client_info = [
                [Paragraph('<b>CLIENTE</b>', self.styles['SectionTitle'])],
                [document.client.name],
                [document.client.address or ''],
                [document.client.tax_id or '']
            ]
        else:
            client_info = [
                [Paragraph('<b>CLIENTE</b>', self.styles['SectionTitle'])],
                [''],
                [''],
                ['']
            ]

        # Create two-column layout
        client_table = Table(client_info, colWidths=[120*mm])
        client_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LINEBELOW', (0, 0), (-1, -1), 1, HexColor('#E5E5EA'))
        ]))
        story.append(client_table)
        story.append(Spacer(1, 30))

        # Document lines table
        if document.lines:
            lines_data = []
            
            # Headers
            lines_data.append([
                'Código',
                'Descripción',
                'Cantidad',
                'Precio',
                'Descuento',
                'Total'
            ])
            
            # Data rows
            for line in document.lines:
                product_name = ''
                if line.product:
                    product_name = line.product.name
                elif line.description:
                    product_name = line.description
                
                quantity = float(line.quantity) if line.quantity else 0
                unit_price = float(line.unit_price) if line.unit_price else 0
                discount = float(line.discount_percent or 0)
                subtotal = quantity * unit_price * (1 - discount / 100)
                
                lines_data.append([
                    line.product.code if line.product else '',
                    product_name,
                    f"{quantity:.2f}",
                    f"€{unit_price:.2f}",
                    f"{discount:.0f}%" if discount else "",
                    f"€{subtotal:.2f}"
                ])
            
            # Create table
            lines_table = Table(lines_data, colWidths=[25*mm, 60*mm, 20*mm, 25*mm, 20*mm, 30*mm])
            lines_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#007AFF')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), white),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#E5E5EA')),
                ('ALIGN', (2, 1), (5, -1), 'RIGHT')  # Right align numbers
            ]))
            story.append(lines_table)
        
        # Totals section
        story.append(Spacer(1, 20))
        
        # Calculate totals
        subtotal = float(document.subtotal or 0)
        tax_rate = 0.21  # Default 21% IVA
        tax_amount = subtotal * tax_rate
        total = float(document.total or 0)
        
        totals_data = [
            ['', '', '', '', 'Subtotal:', f"€{subtotal:.2f}"],
            ['', '', '', '', f'IVA ({tax_rate*100:.0f}%):', f"€{tax_amount:.2f}"],
            ['', '', '', '', 'TOTAL:', f"€{total:.2f}"]
        ]
        
        totals_table = Table(totals_data, colWidths=[25*mm, 60*mm, 20*mm, 25*mm, 25*mm, 30*mm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (4, 0), (5, -1), 'RIGHT'),
            ('FONTNAME', (4, 0), (5, 2), 'Helvetica-Bold'),
            ('FONTNAME', (5, 2), (5, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (5, 2), (5, 2), 12),
            ('TEXTCOLOR', (5, 2), (5, 2), HexColor('#007AFF'))
        ]))
        story.append(totals_table)
        
        # Notes section
        if document.notes:
            story.append(Spacer(1, 30))
            story.append(Paragraph('<b>Notas:</b>', self.styles['SectionTitle']))
            story.append(Paragraph(document.notes, self.styles['Normal']))
        
        # Payment terms
        payment_terms = "Forma de pago: Transferencia bancaria\n\n" \
                       "El pago debe realizarse en un plazo de 30 dias desde la fecha de emision.\n\n" \
                       "Le agradecemos su confianza y quedamos a su disposicion para cualquier consulta."
        
        story.append(Spacer(1, 30))
        story.append(Paragraph('<b>Condiciones de pago:</b>', self.styles['SectionTitle']))
        story.append(Paragraph(payment_terms, self.styles['Normal']))

        # Build PDF
        doc.build(story)

    def _get_status_label(self, status: str) -> str:
        """Get Spanish label for document status."""
        status_labels = {
            'draft': 'Borrador',
            'not_sent': 'No Enviado',
            'sent': 'Enviado',
            'accepted': 'Aceptado',
            'rejected': 'Rechazado',
            'paid': 'Pagado',
            'partially_paid': 'Parcialmente Pagado',
            'cancelled': 'Cancelado'
        }
        return status_labels.get(status, status)