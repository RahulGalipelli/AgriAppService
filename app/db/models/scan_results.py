from uuid import uuid4
from sqlalchemy import DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column
from app.db.base import Base
from sqlalchemy.sql import func

class ScanResult(Base):
    __tablename__ = "scan_results"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    scan_id = mapped_column(UUID(as_uuid=True), ForeignKey("plant_scans.id"), nullable=False)
    result_json = mapped_column(JSON, nullable=False)
    created_at = mapped_column(DateTime, server_default=func.now())
