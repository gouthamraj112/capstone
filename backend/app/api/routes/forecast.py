from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query

from app.core.database import db
from app.ml.forecasting import forecast as make_forecast
from app.services.energy_service import format_timestamp, frame

router = APIRouter()


@router.get("/forecast")
def forecast(hours: int = Query(24, ge=1, le=168)):
    df = frame("hourly_energy")
    if not df.empty and "demand" in df:
        df["Global_active_power"] = df["demand"]
    else:
        df = frame()
    if df.empty:
        return {"items": [], "error": "No energy data has been ingested."}
    try:
        items = make_forecast(df["Global_active_power"], hours)
        formatted = [{**row, "timestamp": format_timestamp(row["timestamp"])} for row in items]
        try:
            for item in items:
                db.forecasts.update_one(
                    {"timestamp": item["timestamp"]},
                    {"$set": {
                        "timestamp": item["timestamp"],
                        "predicted_demand": item["predicted_demand"],
                        "lower_bound": item["lower_bound"],
                        "upper_bound": item["upper_bound"],
                        "horizon_hours": hours,
                        "created_at": datetime.now(timezone.utc)
                    }},
                    upsert=True
                )
        except Exception:
            pass
        return {"items": formatted, "model": "seasonal naive (24-hour baseline)"}
    except ValueError as exc:
        return {"items": [], "error": str(exc), "model": "seasonal naive (24-hour baseline)"}
