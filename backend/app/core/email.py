"""
Email service for sending documents as attachments.
Uses smtplib (built-in Python, no extra dependencies).
"""
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

from app.config import get_settings

logger = logging.getLogger(__name__)


def is_smtp_configured() -> bool:
    """Check if SMTP settings are configured."""
    settings = get_settings()
    return bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)


def send_document_email(
    recipient_email: str,
    subject: str,
    body_html: str,
    pdf_bytes: bytes,
    pdf_filename: str,
) -> None:
    """
    Send an email with a PDF attachment.

    Raises:
        ValueError: If SMTP is not configured.
        smtplib.SMTPException: On SMTP errors.
    """
    settings = get_settings()

    if not is_smtp_configured():
        raise ValueError("SMTP not configured. Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD environment variables.")

    msg = MIMEMultipart()
    msg["From"] = settings.SMTP_USER
    msg["To"] = recipient_email
    msg["Subject"] = subject

    # HTML body
    msg.attach(MIMEText(body_html, "html"))

    # PDF attachment
    pdf_part = MIMEApplication(pdf_bytes, _subtype="pdf")
    pdf_part.add_header("Content-Disposition", "attachment", filename=pdf_filename)
    msg.attach(pdf_part)

    # Send via SMTP
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)

    logger.info(f"Email sent to {recipient_email} with attachment {pdf_filename}")


def build_document_email_html(
    company_name: str,
    doc_type: str,
    doc_code: str,
) -> str:
    """Build a simple HTML email body for a document."""
    doc_type_labels = {
        "quote": "Presupuesto",
        "delivery_note": "Albarán",
        "invoice": "Factura",
    }
    doc_label = doc_type_labels.get(doc_type, "Documento")

    return f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #1D1D1F; padding: 20px;">
        <h2 style="color: #007AFF;">{company_name}</h2>
        <p>Estimado cliente,</p>
        <p>Adjuntamos el documento <strong>{doc_label} {doc_code}</strong>.</p>
        <p>No dude en contactarnos si tiene alguna pregunta.</p>
        <br>
        <p style="color: #6E6E73; font-size: 12px;">
            Este es un mensaje automático enviado desde {company_name}.
        </p>
    </body>
    </html>
    """
