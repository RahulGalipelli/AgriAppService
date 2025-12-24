class ProductImage(Base):
    __tablename__ = "product_images"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id = mapped_column(ForeignKey("products.id"))
    image_url = mapped_column(Text)
