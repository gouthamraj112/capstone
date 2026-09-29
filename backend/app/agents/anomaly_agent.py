import pandas as pd
from app.ml.anomaly_detection import detect
from app.services.energy_service import anomaly_count, dashboard_stats, records, time_filter


def run(df=None, start_date=None, end_date=None):
    has_range = bool(start_date or end_date)
    if df is None:
        query = time_filter(start_date, end_date) if has_range else None
        items = records("anomalies", query=query, limit=20)
        total_count = len(items) if has_range else anomaly_count()
        observations = dashboard_stats()["observations"]
        has_data = len(items) > 0 if has_range else observations > 0
    else:
        if has_range and isinstance(df.index, pd.DatetimeIndex):
            tz = df.index.tz
            if start_date:
                df = df[df.index >= pd.Timestamp(start_date, tz=tz)]
            if end_date:
                df = df[df.index <= pd.Timestamp(end_date, tz=tz)]
        items = detect(df)
        total_count = len(items)
        observations = len(df)
        has_data = observations > 0

    for item in items:
        if "timestamp" in item:
            item["timestamp"] = str(item["timestamp"])

    date_str = f"{start_date} to {end_date}" if start_date and end_date else f"From {start_date}" if start_date else f"Until {end_date}" if end_date else "2006-12-16 to 2010-11-26 (Full Dataset)"
    citations = [{
        "dataset_name": "Smart Grid Historical Anomalies",
        "repository": "Antigravity Local Energy ML Engine",
        "collection": "anomalies",
        "date_range": date_str,
        "observations_analyzed": total_count,
        "features": ["actual_value", "expected_value", "deviation", "anomaly_score", "severity"],
        "algorithm": "Seasonal Median Absolute Deviation (MAD z-score >= 3.5)"
    }]

    return {"source_agent": "anomaly_agent", "target_agent": "insight_agent", "task": "anomaly_analysis",
            "data": {"count": total_count, "has_data": has_data, "sample_size": len(items)}, "evidence": items[:10],
            "citations": citations,
            "confidence": min(1.0, observations / 1000)}
