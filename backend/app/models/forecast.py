from datetime import datetime
from pydantic import BaseModel, Field


class ForecastPoint(BaseModel):
    timestamp: datetime
    predicted_demand: float = Field(ge=0)
    lower_bound: float = Field(ge=0)
    upper_bound: float = Field(ge=0)
