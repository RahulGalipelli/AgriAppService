from uuid import uuid4
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column
from app.db.base import Base
from sqlalchemy.sql import func

class PlantScan(Base):
    __tablename__ = "plant_scans"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = mapped_column(UUID(as_uuid=True), nullable=False)
    image_filename = mapped_column(String, nullable=False)
    created_at = mapped_column(DateTime, server_default=func.now())
