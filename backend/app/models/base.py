"""
Base model class and common types for all SQLAlchemy models.
"""
from sqlalchemy.orm import declarative_base
from sqlalchemy import TypeDecorator, CHAR
import uuid

Base = declarative_base()


class GUID(TypeDecorator):
    """
    Platform-independent GUID type.
    Uses CHAR(32) for SQLite, storing as hex string.
    Works with both SQLite and PostgreSQL.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is not None:
            if isinstance(value, uuid.UUID):
                return value.hex
            return uuid.UUID(value).hex
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return uuid.UUID(value)
        return value
