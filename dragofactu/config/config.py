import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()


class AppConfig:
    """Application configuration loaded from environment variables"""
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/dragofactu')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', '5432'))
    DB_NAME = os.getenv('DB_NAME', 'dragofactu')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    
    # Email Configuration
    SMTP_HOST = os.getenv('SMTP_HOST', '')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
    
    # Application Configuration
    APP_NAME = os.getenv('APP_NAME', 'Dragofactu')
    APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))
    
    # PDF Configuration
    PDF_COMPANY_NAME = os.getenv('PDF_COMPANY_NAME', 'Your Company Name')
    PDF_COMPANY_ADDRESS = os.getenv('PDF_COMPANY_ADDRESS', 'Your Address')
    PDF_COMPANY_PHONE = os.getenv('PDF_COMPANY_PHONE', 'Your Phone')
    PDF_COMPANY_EMAIL = os.getenv('PDF_COMPANY_EMAIL', 'your-email@company.com')
    PDF_COMPANY_CIF = os.getenv('PDF_COMPANY_CIF', 'Your CIF')
    PDF_LOGO_PATH = os.getenv('PDF_LOGO_PATH', 'assets/logo.png')
    
    # File Paths
    DATA_DIR = os.getenv('DATA_DIR', './data')
    EXPORTS_DIR = os.getenv('EXPORTS_DIR', './exports')
    ATTACHMENTS_DIR = os.getenv('ATTACHMENTS_DIR', './attachments')
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get full database URL"""
        if cls.DATABASE_URL:
            return cls.DATABASE_URL
        
        return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        directories = [cls.DATA_DIR, cls.EXPORTS_DIR, cls.ATTACHMENTS_DIR]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)


def get_config() -> AppConfig:
    """Get application configuration instance"""
    return AppConfig()


def setup_logging():
    """Setup logging configuration"""
    import logging
    import sys
    
    level = getattr(logging, AppConfig.LOG_LEVEL.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    return root_logger