from uuid import uuid4
from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column
from app.db.base import Base


class ProductImage(Base):
    __tablename__ = "product_images"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id = mapped_column(ForeignKey("products.id"))
    image_url = mapped_column(Text)
