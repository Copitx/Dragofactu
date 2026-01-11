from typing import Optional, Dict, Any
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import logging

from ...config.config import AppConfig


class EmailService:
    """Service for sending emails and managing email operations"""
    
    def __init__(self):
        self.smtp_host = AppConfig.SMTP_HOST
        self.smtp_port = AppConfig.SMTP_PORT
        self.smtp_user = AppConfig.SMTP_USER
        self.smtp_password = AppConfig.SMTP_PASSWORD
        self.smtp_use_tls = AppConfig.SMTP_USE_TLS
        
        self.logger = logging.getLogger(__name__)
    
    def test_connection(self) -> bool:
        """Test SMTP connection"""
        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            if self.smtp_use_tls:
                server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.quit()
            return True
        except Exception as e:
            self.logger.error(f"SMTP connection test failed: {e}")
            return False
    
    def send_email(self, to_email: str, subject: str, body: str, 
                   html_body: str = None, attachments: list = None) -> Dict[str, Any]:
        """
        Send email with optional HTML body and attachments
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: HTML body (optional)
            attachments: List of file paths to attach
            
        Returns:
            Dict with success status and message
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add plain text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                        
                        encoders.encode_base64(part)
                        filename = os.path.basename(file_path)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {filename}'
                        )
                        msg.attach(part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            self.logger.info(f"Email sent successfully to {to_email}")
            return {
                'success': True,
                'message': f"Email sent successfully to {to_email}"
            }
            
        except Exception as e:
            error_msg = f"Failed to send email to {to_email}: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg
            }
    
    def send_document_email(self, to_email: str, document_type: str, 
                          document_code: str, document_path: str,
                          client_name: str = None) -> Dict[str, Any]:
        """
        Send document as email attachment
        
        Args:
            to_email: Recipient email
            document_type: Type of document (quote, invoice, etc.)
            document_code: Document code/number
            document_path: Path to PDF file
            client_name: Client name (optional)
            
        Returns:
            Dict with success status and message
        """
        subject = f"{document_type.title()} {document_code}"
        
        if client_name:
            greeting = f"Dear {client_name},\n\n"
        else:
            greeting = "Hello,\n\n"
        
        body = f"""{greeting}Please find attached your {document_type} {document_code}.

Thank you for your business.

Best regards,
{AppConfig.PDF_COMPANY_NAME}
{AppConfig.PDF_COMPANY_EMAIL}
{AppConfig.PDF_COMPANY_PHONE}
"""
        
        html_body = f"""
        <html>
        <body>
        <p>{greeting}</p>
        <p>Please find attached your {document_type} <strong>{document_code}</strong>.</p>
        <p>Thank you for your business.</p>
        <p>Best regards,<br>
        {AppConfig.PDF_COMPANY_NAME}<br>
        {AppConfig.PDF_COMPANY_EMAIL}<br>
        {AppConfig.PDF_COMPANY_PHONE}</p>
        </body>
        </html>
        """
        
        return self.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            html_body=html_body,
            attachments=[document_path]
        )
    
    def send_report_email(self, to_email: str, report_name: str, 
                         report_path: str, report_data: Dict = None) -> Dict[str, Any]:
        """
        Send report as email attachment
        
        Args:
            to_email: Recipient email
            report_name: Name of the report
            report_path: Path to report file
            report_data: Report data summary (optional)
            
        Returns:
            Dict with success status and message
        """
        subject = f"Report: {report_name}"
        
        body = f"""Hello,

Please find attached the requested report: {report_name}

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Best regards,
{AppConfig.PDF_COMPANY_NAME}
"""
        
        if report_data:
            body += f"\n\nReport Summary:\n{self._format_report_data(report_data)}"
        
        return self.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            attachments=[report_path]
        )
    
    def _format_report_data(self, data: Dict) -> str:
        """Format report data for email body"""
        formatted = []
        for key, value in data.items():
            formatted.append(f"- {key}: {value}")
        return "\n".join(formatted)
    
    def validate_email_config(self) -> Dict[str, Any]:
        """
        Validate email configuration
        
        Returns:
            Dict with validation results
        """
        results = {
            'valid': True,
            'errors': []
        }
        
        if not self.smtp_host:
            results['errors'].append("SMTP host is not configured")
            results['valid'] = False
        
        if not self.smtp_user:
            results['errors'].append("SMTP username is not configured")
            results['valid'] = False
        
        if not self.smtp_password:
            results['errors'].append("SMTP password is not configured")
            results['valid'] = False
        
        return results