from datetime import datetime
from pydantic import BaseModel


class EnergyReading(BaseModel):
    timestamp: datetime
    Global_active_power: float | None = None
    hour: int | None = None
    day: int | None = None
    month: int | None = None
    year: int | None = None
