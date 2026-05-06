"""
PDF generation service for documents.
Uses ReportLab to generate PDF invoices, quotes, and delivery notes.
"""
from datetime import datetime
from io import BytesIO
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus import Frame, PageTemplate

from app.models import Document, Company


class InvoicePDFGenerator:
    """Generate PDF invoices using ReportLab."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='DocumentTitle',
            parent=self.styles['Heading1'],
            fontSize=22,
            spaceAfter=16,
            textColor=HexColor('#1D1D1F'),
            alignment=1
        ))
        self.styles.add(ParagraphStyle(
            name='HeaderInfo',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=2,
            textColor=HexColor('#6E6E73')
        ))
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=11,
            spaceAfter=6,
            spaceBefore=14,
            textColor=HexColor('#1D1D1F')
        ))
        self.styles.add(ParagraphStyle(
            name='Measurements',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=HexColor('#6E6E73'),
            leftIndent=4,
        ))
        self.styles.add(ParagraphStyle(
            name='FooterText',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=HexColor('#6E6E73'),
        ))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_pdf(self, document: Document, buffer: BytesIO, company: Optional[Company] = None) -> None:
        """Generate PDF document into provided buffer."""
        page_width, page_height = A4
        margin = 20 * mm

        # We use a canvas-level callback to draw page numbers in footer
        page_count_holder = [0]

        def on_later_pages(canvas, doc):
            page_count_holder[0] = doc.page
            _draw_page_footer(canvas, doc, company)

        def on_first_page(canvas, doc):
            page_count_holder[0] = doc.page
            _draw_page_footer(canvas, doc, company)

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=margin,
            leftMargin=margin,
            topMargin=margin,
            bottomMargin=28 * mm,  # leave room for footer
        )

        story = self._build_story(document, company)

        doc.build(story, onFirstPage=on_first_page, onLaterPages=on_later_pages)

    # ------------------------------------------------------------------
    # Story builder
    # ------------------------------------------------------------------

    def _build_story(self, document: Document, company: Optional[Company]) -> list:
        story = []

        # --- Company header ---
        if company:
            # Use trade_name if set and different from name
            display_name = (company.trade_name or company.name or "")
            parts = []
            if display_name:
                parts.append(f"<b>{display_name}</b>")
            if company.legal_name and company.legal_name != display_name:
                parts.append(company.legal_name)
            addr_parts = [p for p in [company.address, company.postal_code, company.city] if p]
            if addr_parts:
                parts.append(", ".join(addr_parts))
            contact_parts = []
            if company.phone:
                contact_parts.append(f"Tel: {company.phone}")
            if company.email:
                contact_parts.append(company.email)
            if company.tax_id:
                contact_parts.append(f"CIF: {company.tax_id}")
            if contact_parts:
                parts.append(" | ".join(contact_parts))
            for line in parts:
                story.append(Paragraph(line, self.styles['HeaderInfo']))
            story.append(Spacer(1, 14))

        # --- Document title ---
        doc_type_map = {
            'quote': 'PRESUPUESTO',
            'delivery_note': 'ALBARÁN',
            'invoice': 'FACTURA',
        }
        doc_title = doc_type_map.get(
            document.type.value if hasattr(document.type, 'value') else document.type,
            'DOCUMENTO'
        )
        story.append(Paragraph(doc_title, self.styles['DocumentTitle']))
        story.append(Spacer(1, 10))

        # --- Document metadata table ---
        doc_info = [
            ['Código:', document.code],
            ['Fecha:', document.issue_date.strftime('%d/%m/%Y')],
            ['Estado:', self._get_status_label(
                document.status.value if hasattr(document.status, 'value') else document.status
            )],
        ]
        if document.due_date:
            doc_info.append(['Vencimiento:', document.due_date.strftime('%d/%m/%Y')])

        # client_reference — show alongside code
        client_ref = getattr(document, 'client_reference', None)
        if client_ref:
            doc_info.append(['Ref. cliente:', client_ref])

        # payment_date when paid
        payment_date = getattr(document, 'payment_date', None)
        status_val = document.status.value if hasattr(document.status, 'value') else document.status
        if payment_date and status_val == 'paid':
            doc_info.append(['Pagado el:', payment_date.strftime('%d/%m/%Y')])

        doc_table = Table(doc_info, colWidths=[50 * mm, 90 * mm])
        doc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#F5F5F7')),
            ('TEXTCOLOR', (0, 0), (-1, -1), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#E5E5EA')),
        ]))
        story.append(doc_table)
        story.append(Spacer(1, 14))

        # --- execution_location (obra) ---
        exec_loc = getattr(document, 'execution_location', None)
        if exec_loc:
            story.append(Paragraph(
                f"<b>Lugar de ejecución:</b> {exec_loc}", self.styles['Normal']
            ))
            story.append(Spacer(1, 8))

        # --- Client block ---
        client = document.client
        if client:
            client_lines = [f"<b>{client.name}</b>"]
            if client.tax_id:
                client_lines.append(f"CIF/NIF: {client.tax_id}")
            if client.address:
                client_lines.append(client.address)
            addr = ", ".join(p for p in [client.postal_code, client.city, client.province] if p)
            if addr:
                client_lines.append(addr)
            if client.phone:
                client_lines.append(f"Tel: {client.phone}")
            if client.email:
                client_lines.append(client.email)

            story.append(Paragraph('<b>CLIENTE</b>', self.styles['SectionTitle']))
            for ln in client_lines:
                story.append(Paragraph(ln, self.styles['Normal']))
            story.append(Spacer(1, 20))

        # --- Lines table ---
        if document.lines:
            header = ['Descripción', 'Medidas', 'Cantidad', 'P. Unit.', 'Dto.%', 'Total']
            rows = [header]

            for line in document.lines:
                qty = float(line.quantity or 1)
                price = float(line.unit_price or 0)
                discount = float(line.discount_percent or 0)
                subtotal = qty * price * (1 - discount / 100)

                desc = line.description or ''
                measurements = getattr(line, 'measurements', None) or ''

                rows.append([
                    desc,
                    measurements,
                    f"{qty:.2f}",
                    f"€{price:.2f}",
                    f"{discount:.0f}%" if discount else "",
                    f"€{subtotal:.2f}",
                ])

            col_widths = [60 * mm, 30 * mm, 18 * mm, 22 * mm, 14 * mm, 24 * mm]
            lines_table = Table(rows, colWidths=col_widths)
            lines_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#007AFF')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), white),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#E5E5EA')),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('ALIGN', (0, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#FAFAFA')]),
            ]))
            story.append(lines_table)

        # --- Totals ---
        story.append(Spacer(1, 16))
        subtotal = float(document.subtotal or 0)
        tax_amount = float(document.tax_amount or 0)
        total = float(document.total or 0)
        tax_rate_pct = round((tax_amount / subtotal * 100) if subtotal else 21)

        totals_data = [
            ['Subtotal:', f"€{subtotal:.2f}"],
            [f'IVA ({tax_rate_pct:.0f}%):', f"€{tax_amount:.2f}"],
            ['TOTAL:', f"€{total:.2f}"],
        ]
        totals_table = Table(totals_data, colWidths=[40 * mm, 28 * mm], hAlign='RIGHT')
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -2), 9),
            ('FONTSIZE', (0, 2), (-1, 2), 11),
            ('TEXTCOLOR', (0, 2), (-1, 2), HexColor('#007AFF')),
            ('LINEABOVE', (0, 2), (-1, 2), 1, HexColor('#007AFF')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(totals_table)

        # --- Notes ---
        if document.notes:
            story.append(Spacer(1, 20))
            story.append(Paragraph('<b>Notas:</b>', self.styles['SectionTitle']))
            story.append(Paragraph(document.notes, self.styles['Normal']))

        # --- Payment method ---
        pay_method = getattr(document, 'payment_method', None)
        if pay_method:
            story.append(Spacer(1, 10))
            story.append(Paragraph(
                f"<b>Forma de pago:</b> {pay_method}", self.styles['Normal']
            ))

        # --- Terms or default footer ---
        if document.terms:
            story.append(Spacer(1, 10))
            story.append(Paragraph('<b>Condiciones:</b>', self.styles['SectionTitle']))
            story.append(Paragraph(document.terms, self.styles['Normal']))

        # --- Company custom footer text ---
        if company and company.pdf_footer_text:
            story.append(Spacer(1, 16))
            story.append(Paragraph(company.pdf_footer_text, self.styles['FooterText']))

        return story

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_status_label(self, status: str) -> str:
        return {
            'draft': 'Borrador',
            'not_sent': 'No Enviado',
            'sent': 'Enviado',
            'accepted': 'Aceptado',
            'rejected': 'Rechazado',
            'paid': 'Pagado',
            'partially_paid': 'Parcialmente Pagado',
            'cancelled': 'Cancelado',
        }.get(status, status)


# ---------------------------------------------------------------------------
# Canvas-level footer with page numbers (Pág. X de N)
# ---------------------------------------------------------------------------

def _draw_page_footer(canvas, doc, company: Optional[Company]):
    """Draw footer with page number. Called per page."""
    canvas.saveState()
    width, height = A4
    margin = 20 * mm
    footer_y = 12 * mm

    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(HexColor('#6E6E73'))

    # Left: company name
    company_name = ""
    if company:
        company_name = company.trade_name or company.name or ""
    canvas.drawString(margin, footer_y, company_name)

    # Right: page number (two-pass not supported simply in ReportLab without canvasmaker)
    page_text = f"Pág. {doc.page}"
    canvas.drawRightString(width - margin, footer_y, page_text)

    # Separator line
    canvas.setStrokeColor(HexColor('#E5E5EA'))
    canvas.line(margin, footer_y + 6, width - margin, footer_y + 6)

    canvas.restoreState()
