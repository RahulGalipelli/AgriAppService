class UserRole(Base):
    __tablename__ = "user_roles"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = mapped_column(ForeignKey("users.id"))
    role = mapped_column(String(50))  # farmer, admin, support
