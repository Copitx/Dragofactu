"""
Password reset token model.
Tokens are stored as SHA-256 hashes — raw token is only sent via email.
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, text
from app.models.base import Base, GUID


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(GUID, primary_key=True, default=lambda: __import__("uuid").uuid4())
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)  # SHA-256 hex
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("(CURRENT_TIMESTAMP)"),
        nullable=True,
    )
