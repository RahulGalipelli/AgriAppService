class ProductInventory(Base):
    __tablename__ = "product_inventory"

    product_id = mapped_column(ForeignKey("products.id"), primary_key=True)
    quantity = mapped_column(Integer)
