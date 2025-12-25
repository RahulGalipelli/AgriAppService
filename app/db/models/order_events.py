from uuid import uuid4
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column
from sqlalchemy.sql import func
from app.db.base import Base


class OrderEvent(Base):
    __tablename__ = "order_events"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id = mapped_column(ForeignKey("orders.id"))
    event = mapped_column(String)
    created_at = mapped_column(DateTime, default=func.now())
