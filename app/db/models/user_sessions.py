class UserSession(Base):
    __tablename__ = "user_sessions"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = mapped_column(ForeignKey("users.id"))
    token = mapped_column(String, unique=True)
    expires_at = mapped_column(DateTime)
