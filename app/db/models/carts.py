from uuid import uuid4
from sqlalchemy import ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column
from app.db.base import Base


class Cart(Base):
    __tablename__ = "carts"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = mapped_column(ForeignKey("users.id"))
    is_active = mapped_column(Boolean, default=True)
