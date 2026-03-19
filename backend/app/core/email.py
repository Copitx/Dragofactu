"""
Email service for sending documents as attachments.
Uses smtplib (built-in Python, no extra dependencies).
"""
import smtplib
import logging
import base64
from typing import Optional, Dict, Any
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import requests

from app.config import get_settings
from app.core.security import decrypt_secret_value

logger = logging.getLogger(__name__)


def get_company_smtp_config(company: Optional[Any]) -> Optional[Dict[str, Any]]:
    """Build SMTP config dict from company settings if available."""
    if not company:
        return None

    encrypted = getattr(company, "smtp_password_encrypted", None)
    password = decrypt_secret_value(encrypted) if encrypted else None
    if not (getattr(company, "smtp_host", None) and getattr(company, "smtp_user", None) and password):
        return None

    return {
        "host": company.smtp_host,
        "port": company.smtp_port or 587,
        "user": company.smtp_user,
        "password": password,
        "use_tls": bool(company.smtp_use_tls),
        "from_email": company.smtp_from_email or company.smtp_user,
        "from_name": company.smtp_from_name,
    }


def get_managed_email_config() -> Optional[Dict[str, str]]:
    """Build managed HTTPS email channel config (Brevo)."""
    settings = get_settings()
    if not (settings.BREVO_API_KEY and settings.BREVO_SENDER_EMAIL):
        return None
    return {
        "api_key": settings.BREVO_API_KEY,
        "sender_email": settings.BREVO_SENDER_EMAIL,
        "sender_name": settings.BREVO_SENDER_NAME or "Dragofactu",
    }


def is_smtp_configured(company: Optional[Any] = None) -> bool:
    """Check if any email channel is configured (company SMTP, global SMTP, or managed API)."""
    company_config = get_company_smtp_config(company)
    if company_config:
        return True

    if get_managed_email_config():
        return True

    settings = get_settings()
    return bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)


def _send_via_brevo_api(
    recipient_email: str,
    subject: str,
    body_html: str,
    pdf_bytes: bytes,
    pdf_filename: str,
    managed_config: Dict[str, str],
) -> None:
    """Send email via Brevo transactional API over HTTPS."""
    payload = {
        "sender": {
            "name": managed_config["sender_name"],
            "email": managed_config["sender_email"],
        },
        "to": [{"email": recipient_email}],
        "subject": subject,
        "htmlContent": body_html,
        "attachment": [
            {
                "name": pdf_filename,
                "content": base64.b64encode(pdf_bytes).decode("ascii"),
            }
        ],
    }

    response = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={
            "accept": "application/json",
            "api-key": managed_config["api_key"],
            "content-type": "application/json",
        },
        json=payload,
        timeout=20,
    )

    if response.status_code >= 400:
        detail = response.text[:300]
        raise RuntimeError(f"Brevo API error ({response.status_code}): {detail}")


def send_document_email(
    recipient_email: str,
    subject: str,
    body_html: str,
    pdf_bytes: bytes,
    pdf_filename: str,
    smtp_config: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Send an email with a PDF attachment.

    Raises:
        ValueError: If SMTP is not configured.
        smtplib.SMTPException: On SMTP errors.
    """
    settings = get_settings()
    managed_config = get_managed_email_config()

    effective_config = smtp_config or {
        "host": settings.SMTP_HOST,
        "port": settings.SMTP_PORT,
        "user": settings.SMTP_USER,
        "password": settings.SMTP_PASSWORD,
        "use_tls": True,
        "from_email": settings.SMTP_USER,
        "from_name": None,
    }

    smtp_ready = bool(effective_config.get("host") and effective_config.get("user") and effective_config.get("password"))
    if not smtp_ready and not managed_config:
        raise ValueError("Email not configured. Configure company SMTP or managed email channel.")

    msg = MIMEMultipart()
    from_email = effective_config.get("from_email") or effective_config.get("user")
    from_name = effective_config.get("from_name")
    msg["From"] = f"{from_name} <{from_email}>" if from_name else from_email
    msg["To"] = recipient_email
    msg["Subject"] = subject

    # HTML body
    msg.attach(MIMEText(body_html, "html"))

    # PDF attachment
    pdf_part = MIMEApplication(pdf_bytes, _subtype="pdf")
    pdf_part.add_header("Content-Disposition", "attachment", filename=pdf_filename)
    msg.attach(pdf_part)

    if smtp_ready:
        try:
            with smtplib.SMTP(effective_config["host"], effective_config["port"], timeout=20) as server:
                if effective_config.get("use_tls", True):
                    server.starttls()
                server.login(effective_config["user"], effective_config["password"])
                server.send_message(msg)
            logger.info(f"Email sent to {recipient_email} with attachment {pdf_filename} via SMTP")
            return
        except Exception as smtp_error:
            if not managed_config:
                raise smtp_error
            logger.warning("SMTP failed, falling back to managed email API: %s", smtp_error)

    if managed_config:
        _send_via_brevo_api(
            recipient_email=recipient_email,
            subject=subject,
            body_html=body_html,
            pdf_bytes=pdf_bytes,
            pdf_filename=pdf_filename,
            managed_config=managed_config,
        )
        logger.info(f"Email sent to {recipient_email} with attachment {pdf_filename} via managed API")
        return

    raise RuntimeError("No email delivery channel available")


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
