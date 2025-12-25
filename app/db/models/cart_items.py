from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import mapped_column
from app.db.base import Base


class CartItem(Base):
    __tablename__ = "cart_items"

    cart_id = mapped_column(ForeignKey("carts.id"), primary_key=True)
    product_id = mapped_column(ForeignKey("products.id"), primary_key=True)
    quantity = mapped_column(Integer)
