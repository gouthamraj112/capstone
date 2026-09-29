from typing import Any

import pandas as pd
import numpy as np
from fastapi import HTTPException
from pymongo.errors import PyMongoError

from app.core.database import db


def records(collection="energy_data", query=None, limit=250000) -> list[dict[str, Any]]:
    try:
        sort_field = "date" if collection == "daily_energy" else "timestamp"
        return list(db[collection].find(query or {}, {"_id": 0}).sort(sort_field, 1).limit(limit))
    except PyMongoError as exc:
        raise HTTPException(503, "MongoDB is unavailable; energy data could not be loaded.") from exc


def frame(collection="energy_data", query=None) -> pd.DataFrame:
    rows = records(collection, query)
    if not rows:
        return pd.DataFrame()
    result = pd.DataFrame(rows)
    if "timestamp" in result:
        result["timestamp"] = pd.to_datetime(result["timestamp"], utc=True)
        result = result.set_index("timestamp").sort_index()
    elif "date" in result:
        result["date"] = pd.to_datetime(result["date"], utc=True)
        result = result.set_index("date").sort_index()
    return result


def time_filter(start: str | None, end: str | None) -> dict:
    query = {}
    if start or end:
        query["timestamp"] = {}
        if start:
            query["timestamp"]["$gte"] = pd.Timestamp(start).to_pydatetime()
        if end:
            query["timestamp"]["$lte"] = pd.Timestamp(end).to_pydatetime()
    return query


def dashboard_stats() -> dict:
    """Compute KPIs from compact hourly summaries rather than scanning minute rows."""
    try:
        summary = db.hourly_energy.find_one({}, {"_id": 0, "valid_samples": 1, "active_power_sum": 1})
        if summary and "valid_samples" in summary and "active_power_sum" in summary:
            row = next(iter(db.hourly_energy.aggregate([
                {"$group": {"_id": None, "total_kw_minutes": {"$sum": "$active_power_sum"},
                            "observations": {"$sum": "$valid_samples"}}}
            ])), None)
            peak_record = db.energy_data.find_one({"Global_active_power": {"$gt": 0}},
                                                   {"_id": 0, "Global_active_power": 1},
                                                   sort=[("Global_active_power", -1)])
            peak = peak_record.get("Global_active_power") if peak_record else None
            average = row["total_kw_minutes"] / row["observations"] if row and row["observations"] else None
        else:
            # Compatibility with data ingested by an earlier version.
            row = next(iter(db.energy_data.aggregate([
                {"$group": {"_id": None, "average": {"$avg": "$Global_active_power"},
                            "peak": {"$max": "$Global_active_power"}, "total_kw_minutes": {"$sum": "$Global_active_power"},
                            "observations": {"$sum": {"$cond": [{"$isNumber": "$Global_active_power"}, 1, 0]}}}}
            ])), None)
            average = row.get("average") if row else None
            peak = row.get("peak") if row else None
        if not row or not row.get("observations"):
            return {"total_consumption": None, "average_demand": None, "peak_demand": None, "observations": 0}
        return {"total_consumption": round(float(row["total_kw_minutes"] / 60), 3) if row.get("total_kw_minutes") is not None else None,
                "average_demand": round(float(average), 3) if average is not None else None,
                "peak_demand": round(float(peak), 3) if peak is not None else None,
                "observations": int(row["observations"])}
    except PyMongoError as exc:
        raise HTTPException(503, "MongoDB is unavailable; dashboard analytics could not be loaded.") from exc


def anomaly_count() -> int:
    try:
        return db.anomalies.count_documents({})
    except PyMongoError as exc:
        raise HTTPException(503, "MongoDB is unavailable; anomaly count could not be loaded.") from exc


def top_peak_records(limit: int = 10) -> list[dict]:
    try:
        rows = db.energy_data.find({"Global_active_power": {"$ne": None}},
                                   {"_id": 0, "timestamp": 1, "Global_active_power": 1,
                                    "Sub_metering_1": 1, "Sub_metering_2": 1, "Sub_metering_3": 1})
        return [{"timestamp": format_timestamp(r["timestamp"]), "demand": round(float(r["Global_active_power"]), 3),
                 **{field: round(float(r[field]), 3) for field in ("Sub_metering_1", "Sub_metering_2", "Sub_metering_3") if r.get(field) is not None}}
                for r in rows.sort("Global_active_power", -1).limit(max(1, min(limit, 100)))]
    except PyMongoError as exc:
        raise HTTPException(503, "MongoDB is unavailable; peak readings could not be loaded.") from exc


def format_timestamp(value) -> str:
    """Serialize the source's timezone-naive clock value without local-time shifting."""
    timestamp = pd.Timestamp(value)
    if timestamp.tz is not None:
        timestamp = timestamp.tz_convert("UTC").tz_localize(None)
    return timestamp.isoformat(timespec="seconds")


def json_records(df: pd.Series | pd.DataFrame, name="value") -> list[dict]:
    if isinstance(df, pd.Series):
        df = df.rename(name).to_frame()
    if df.empty:
        return []
    result = df.reset_index()
    result = result.rename(columns={result.columns[0]: "timestamp"})
    time_key = "timestamp" if "timestamp" in result else result.columns[0]
    result = result.rename(columns={time_key: "timestamp"})
    result["timestamp"] = result["timestamp"].map(format_timestamp)
    result = result.replace([np.inf, -np.inf], np.nan)
    return result.astype(object).where(pd.notna(result), None).to_dict("records")
