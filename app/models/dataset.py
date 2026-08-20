from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from app.database.connection import Base

class DatasetReport(Base):
    __tablename__ = "dataset_reports"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    total_rows = Column(Integer)
    total_columns = Column(Integer)
    duplicate_rows = Column(Integer)
    total_missing_values = Column(Integer)
    anomaly_count = Column(Integer)
    data_quality_score = Column(Integer)
    data_quality_label = Column(String)
    data_quality_breakdown = Column(JSON)

    # We store the Pandas statistical profile as a JSON object
    statistical_summary = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)