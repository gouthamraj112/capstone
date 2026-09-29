import pandas as pd
from app.ml.forecasting import forecast
from app.services.energy_service import frame


def run(df=None, hours=6, start_date=None, end_date=None):
    compact = frame("hourly_energy")
    has_range = bool(start_date or end_date)
    if not compact.empty and "demand" in compact:
        df = compact.rename(columns={"demand": "Global_active_power"})
    elif df is None:
        df = frame()

    if df is not None and not df.empty and has_range and isinstance(df.index, pd.DatetimeIndex):
        tz = df.index.tz
        if start_date:
            df = df[df.index >= pd.Timestamp(start_date, tz=tz)]
        if end_date:
            df = df[df.index <= pd.Timestamp(end_date, tz=tz)]

    date_str = f"{start_date} to {end_date}" if start_date and end_date else f"From {start_date}" if start_date else f"Until {end_date}" if end_date else "2006-12-16 to 2010-11-26 (Full Dataset)"
    citations = [{
        "dataset_name": "Individual Household Electric Power Consumption",
        "repository": "UCI Machine Learning Repository / EDF R&D",
        "collection": "hourly_energy",
        "date_range": date_str,
        "observations_analyzed": len(df) if df is not None else 0,
        "features": ["Global_active_power"],
        "model": f"Seasonal Naive Forecast ({hours}h horizon)"
    }]

    if df is None or df.empty or "Global_active_power" not in df:
        return {"source_agent": "forecasting_agent", "target_agent": "insight_agent", "task": "forecast",
                "data": {"hours": hours, "error": "No energy data is available for the requested range.", "has_data": False},
                "evidence": [], "citations": citations, "confidence": 0.0}
    try:
        result = forecast(df["Global_active_power"], hours)
    except ValueError as exc:
        return {"source_agent": "forecasting_agent", "target_agent": "insight_agent", "task": "forecast",
                "data": {"hours": hours, "error": str(exc), "has_data": True},
                "evidence": [], "citations": citations, "confidence": 0.0}
    return {"source_agent": "forecasting_agent", "target_agent": "insight_agent", "task": "forecast",
            "data": {"hours": hours}, "evidence": result, "citations": citations,
            "confidence": min(1.0, len(df) / 168)}
