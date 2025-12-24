class PlantScan(Base):
    __tablename__ = "plant_scans"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = mapped_column(ForeignKey("users.id"))
    image_url = mapped_column(Text)
    status = mapped_column(String(20))  # uploaded, processed
    created_at = mapped_column(DateTime, default=func.now())
