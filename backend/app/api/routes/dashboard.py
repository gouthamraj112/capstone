from fastapi import APIRouter

from app.core.database import database_status, db
from app.services.energy_service import anomaly_count, dashboard_stats, format_timestamp

router = APIRouter()


@router.get("/health")
def health():
    connected, reason = database_status()
    return {"status": "ok" if connected else "degraded", "mongodb": connected, "detail": reason if not connected else None}


@router.get("/dashboard")
def dashboard():
    summary = dashboard_stats()
    try:
        first = db.energy_data.find_one({}, {"_id": 0, "timestamp": 1}, sort=[("timestamp", 1)])
        last = db.energy_data.find_one({}, {"_id": 0, "timestamp": 1}, sort=[("timestamp", -1)])
        coverage = {"start": format_timestamp(first["timestamp"]) if first else None,
                    "end": format_timestamp(last["timestamp"]) if last else None}
    except Exception:
        coverage = {"start": None, "end": None}
    forecasted_demand = None
    try:
        latest_fc = db.forecasts.find_one({}, sort=[("timestamp", -1)])
        if latest_fc and latest_fc.get("predicted_demand") is not None:
            forecasted_demand = round(float(latest_fc["predicted_demand"]), 3)
    except Exception:
        pass
    return {**summary, "anomalies": anomaly_count(), "forecasted_demand": forecasted_demand,
            "data_coverage": coverage}
