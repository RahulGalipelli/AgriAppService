class OrderItem(Base):
    __tablename__ = "order_items"

    order_id = mapped_column(ForeignKey("orders.id"), primary_key=True)
    product_id = mapped_column(ForeignKey("products.id"), primary_key=True)
    quantity = mapped_column(Integer)
    price = mapped_column(Numeric(10,2))
