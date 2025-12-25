from uuid import uuid4
from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column
from app.db.base import Base


class UserRole(Base):
    __tablename__ = "user_roles"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = mapped_column(ForeignKey("users.id"))
    role = mapped_column(String(50))  # farmer, admin, support
