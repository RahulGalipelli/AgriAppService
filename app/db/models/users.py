class User(Base):
    __tablename__ = "users"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    phone = mapped_column(String(15), unique=True, index=True)
    name = mapped_column(String(100), nullable=True)
    language = mapped_column(String(10), default="en")
    is_active = mapped_column(Boolean, default=True)
    created_at = mapped_column(DateTime, default=func.now())
