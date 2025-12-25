from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import mapped_column
from app.db.base import Base


class ScanProductRecommendation(Base):
    __tablename__ = "scan_product_recommendations"

    scan_id = mapped_column(ForeignKey("plant_scans.id"), primary_key=True)
    product_id = mapped_column(ForeignKey("products.id"), primary_key=True)
    rank = mapped_column(Integer)
