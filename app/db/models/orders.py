class Order(Base):
    __tablename__ = "orders"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = mapped_column(ForeignKey("users.id"))
    status = mapped_column(String(30))  # placed, shipped, delivered
    total_amount = mapped_column(Numeric(10,2))
    created_at = mapped_column(DateTime, default=func.now())
