class ScanResult(Base):
    __tablename__ = "scan_results"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    scan_id = mapped_column(ForeignKey("plant_scans.id"))
    disease = mapped_column(String)
    confidence = mapped_column(Float)
    advice = mapped_column(Text)
