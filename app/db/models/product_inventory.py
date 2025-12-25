from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import mapped_column
from app.db.base import Base


class ProductInventory(Base):
    __tablename__ = "product_inventory"

    product_id = mapped_column(ForeignKey("products.id"), primary_key=True)
    quantity = mapped_column(Integer)
