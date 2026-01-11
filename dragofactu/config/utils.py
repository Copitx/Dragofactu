import os
from typing import Optional, Dict, Any
from datetime import datetime


def format_currency(amount: float, currency: str = "EUR") -> str:
    """Format amount as currency"""
    return f"{amount:,.2f} {currency}"


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M") -> str:
    """Format datetime for display"""
    if not dt:
        return ""
    return dt.strftime(format_str)


def generate_unique_code(prefix: str) -> str:
    """Generate a unique code with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{prefix}{timestamp}"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    import re
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    return filename


def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return os.path.splitext(filename)[1].lower()


def validate_email(email: str) -> bool:
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_tax_id(tax_id: str, country: str = "ES") -> bool:
    """Validate tax ID format (basic validation)"""
    if not tax_id:
        return True  # Optional field
    
    tax_id = tax_id.replace(' ', '').replace('-', '').upper()
    
    if country == "ES":
        # Spanish CIF/NIF validation (basic)
        if len(tax_id) == 9:
            return True  # Basic check, can be enhanced
    
    return len(tax_id) >= 3  # Basic length check


def calculate_vat(amount: float, vat_rate: float) -> float:
    """Calculate VAT amount"""
    return amount * (vat_rate / 100)


def calculate_with_vat(amount: float, vat_rate: float) -> float:
    """Calculate total amount including VAT"""
    vat = calculate_vat(amount, vat_rate)
    return amount + vat


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length"""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely load JSON string"""
    import json
    try:
        return json.loads(json_str) if json_str else default
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """Safely dump object to JSON string"""
    import json
    try:
        return json.dumps(obj) if obj is not None else default
    except (TypeError, ValueError):
        return default


def copy_entity_attributes(source: Any, target: Any, exclude_fields: list = None) -> None:
    """Copy attributes from one entity to another"""
    if exclude_fields is None:
        exclude_fields = ['id', 'created_at', 'updated_at']
    
    for attr in dir(source):
        if not attr.startswith('_') and attr not in exclude_fields:
            if hasattr(target, attr):
                setattr(target, attr, getattr(source, attr))


def log_activity(user_id: str, action: str, entity_type: str, entity_id: str = None, 
                 details: Dict[str, Any] = None) -> None:
    """Log user activity (can be enhanced with proper logging)"""
    from .config import AppConfig
    import logging
    
    logger = logging.getLogger(__name__)
    
    log_data = {
        'user_id': user_id,
        'action': action,
        'entity_type': entity_type,
        'entity_id': entity_id,
        'timestamp': datetime.utcnow().isoformat(),
        'details': details or {}
    }
    
    if AppConfig.DEBUG:
        logger.info(f"Activity: {log_data}")
    
    # In production, this would be stored in database or proper log system