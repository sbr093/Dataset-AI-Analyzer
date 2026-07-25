from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

class DatasetReportBase(BaseModel):
    filename: str
    total_rows: int
    anomaly_count: int
    statistical_summary: Dict[str, Any]

class DatasetReportCreate(DatasetReportBase):
    pass

class DatasetReportResponse(DatasetReportBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True