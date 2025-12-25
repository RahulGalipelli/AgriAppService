from uuid import uuid4
from sqlalchemy import String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column
from app.db.base import Base
from sqlalchemy.sql import func

class PlantScan(Base):
    __tablename__ = "plant_scans"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = mapped_column(UUID(as_uuid=True), nullable=False)
    image_filename = mapped_column(String, nullable=False)
    image_hash_phash = mapped_column(String, nullable=True, index=True)  # Perceptual hash
    image_hash_dct = mapped_column(String, nullable=True, index=True)  # DCT hash
    image_hash_md5 = mapped_column(String, nullable=True, index=True)  # MD5 for exact duplicates
    is_duplicate = mapped_column(Boolean, default=False)  # Flag for duplicate scans
    original_scan_id = mapped_column(UUID(as_uuid=True), ForeignKey("plant_scans.id"), nullable=True)  # Reference to original
    created_at = mapped_column(DateTime, server_default=func.now())
