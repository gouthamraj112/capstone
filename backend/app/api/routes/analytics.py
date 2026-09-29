from fastapi import APIRouter

from app.analytics.consumption import grouped_consumption
from app.analytics.trends import patterns
from app.core.database import db
from app.services.energy_service import format_timestamp, frame, json_records, top_peak_records

router = APIRouter(prefix="/energy")


@router.get("/trends")
def trends():
    hourly = frame("hourly_energy")
    if not hourly.empty and "demand" in hourly:
        profile = hourly[["demand"]].rename(columns={"demand": "Global_active_power"})
    else:
        profile = frame()
    daily = frame("daily_energy")
    daily_series = daily["demand"] if not daily.empty and "demand" in daily else grouped_consumption(profile, "D")
    weekly_series = hourly["demand"].resample("W").mean().dropna() if not hourly.empty and "demand" in hourly else grouped_consumption(profile, "W")
    monthly_series = hourly["demand"].resample("MS").mean().dropna() if not hourly.empty and "demand" in hourly else grouped_consumption(profile, "MS")
    return {"patterns": patterns(profile), "hourly": json_records(hourly["demand"], "demand") if "demand" in hourly else json_records(grouped_consumption(profile, "h"), "demand"),
            "daily": json_records(daily_series, "demand"), "weekly": json_records(weekly_series, "demand"),
            "monthly": json_records(monthly_series, "demand"),
            "rolling_mean": json_records(hourly["demand"].rolling(24, min_periods=1).mean(), "demand") if "demand" in hourly else [],
            "rolling_std": json_records(hourly["demand"].rolling(24, min_periods=2).std().dropna(), "demand") if "demand" in hourly else []}


@router.get("/peaks")
def peaks(limit: int = 10):
    size = max(1, min(limit, 100))
    items = top_peak_records(size)
    hourly = frame("hourly_energy")
    daily = frame("daily_energy")
    hourly_profile = hourly["demand"].groupby(hourly.index.hour).mean() if not hourly.empty and "demand" in hourly else None
    daily_peak = daily["demand"].idxmax() if not daily.empty and "demand" in daily else None
    top_values = [x["demand"] for x in items]
    return {"items": items, "maximum_demand": top_values[0] if top_values else None,
            "peak_hour": int(hourly_profile.idxmax()) if hourly_profile is not None and len(hourly_profile) else None,
            "peak_day": format_timestamp(daily_peak) if daily_peak is not None else None,
            "average_peak_demand": round(sum(top_values) / len(top_values), 3) if top_values else None}


@router.get("/hourly")
def hourly():
    df = frame("hourly_energy")
    if df.empty:
        df = frame()
        return {"items": json_records(grouped_consumption(df, "h"), "demand")}
    return {"items": json_records(df)}


@router.get("/daily")
def daily():
    df = frame("daily_energy")
    if df.empty:
        return {"items": json_records(grouped_consumption(frame(), "D"), "demand")}
    return {"items": json_records(df)}


@router.get("/monthly")
def monthly():
    hourly = frame("hourly_energy")
    if not hourly.empty and "demand" in hourly:
        return {"items": json_records(hourly["demand"].resample("MS").mean().dropna(), "demand")}
    return {"items": json_records(grouped_consumption(frame(), "MS"), "demand")}
