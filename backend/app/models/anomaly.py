from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class AnomalyRecord(BaseModel):
    timestamp: datetime
    actual_value: float
    expected_value: float
    deviation: float
    anomaly_score: float = Field(ge=0, le=1)
    severity: Literal["low", "medium", "high"]
    reason: str
