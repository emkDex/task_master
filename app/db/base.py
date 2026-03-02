"""
SQLAlchemy base configuration for TaskMaster Pro.
Defines the declarative base and metadata.
"""

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

# Naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    
    metadata = MetaData(naming_convention=convention)
    
    def __repr__(self) -> str:
        """Default string representation."""
        columns = [f"{col}={getattr(self, col)}" for col in self.__table__.columns.keys()]
        return f"<{self.__class__.__name__}({', '.join(columns)})>"
    
    def to_dict(self) -> dict:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
