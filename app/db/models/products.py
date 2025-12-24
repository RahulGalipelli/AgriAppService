class Product(Base):
    __tablename__ = "products"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = mapped_column(String)
    description = mapped_column(Text)
    price = mapped_column(Numeric(10,2))
    is_active = mapped_column(Boolean, default=True)
