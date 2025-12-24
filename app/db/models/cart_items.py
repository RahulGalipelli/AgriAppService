class CartItem(Base):
    __tablename__ = "cart_items"

    cart_id = mapped_column(ForeignKey("carts.id"), primary_key=True)
    product_id = mapped_column(ForeignKey("products.id"), primary_key=True)
    quantity = mapped_column(Integer)
