class Cart(Base):
    __tablename__ = "carts"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = mapped_column(ForeignKey("users.id"))
    is_active = mapped_column(Boolean, default=True)
