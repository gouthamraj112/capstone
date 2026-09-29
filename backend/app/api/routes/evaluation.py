from fastapi import APIRouter
from app.ml.evaluation import (
    evaluate_controlled_anomalies,
    evaluate_groundedness,
    evaluate_natural_language_queries,
    evaluate_seasonal_forecast,
)
from app.services.energy_service import frame

router = APIRouter()


@router.get("/evaluation")
def evaluation():
    hourly = frame("hourly_energy")
    raw = frame() if hourly.empty else None
    series = hourly["demand"] if not hourly.empty and "demand" in hourly else raw["Global_active_power"] if raw is not None and "Global_active_power" in raw else None
    forecast_scores = evaluate_seasonal_forecast(series) if series is not None else {"mae": None, "rmse": None, "mape": None, "note": "No readings available."}
    anomaly_scores = evaluate_controlled_anomalies(series) if series is not None else {"precision": None, "recall": None, "f1": None, "methodology": "No readings available."}
    query_scores = evaluate_natural_language_queries()
    groundedness_scores = evaluate_groundedness()
    return {"forecast": forecast_scores,
            "anomaly": anomaly_scores,
            "query": query_scores,
            "groundedness": groundedness_scores}

