import pandas as pd
from app.analytics.consumption import consumption_summary
from app.analytics.peaks import peak_periods
from app.services.energy_service import dashboard_stats, frame, top_peak_records, time_filter


SUBMETER_LABELS = {
    "Sub_metering_1": "Kitchen-related consumption",
    "Sub_metering_2": "Laundry-related consumption",
    "Sub_metering_3": "Heating/AC-related consumption",
}


def _submeter_evening_profile(df):
    if df is None or df.empty:
        return {}, None
    if not isinstance(df.index, pd.DatetimeIndex):
        return {}, None

    available = {field: label for field, label in SUBMETER_LABELS.items() if field in df.columns}
    if not available:
        return {}, None

    evening = df[df.index.hour.isin([18, 19, 20])]
    if evening.empty:
        return {}, None

    profile = {}
    for field in available:
        values = evening[field].dropna()
        profile[field] = round(float(values.mean()), 3) if len(values) else 0.0

    dominant_field, dominant_value = max(profile.items(), key=lambda item: item[1]) if profile else (None, 0.0)
    dominant = {
        "field": dominant_field,
        "label": available.get(dominant_field, dominant_field),
        "value": dominant_value,
    } if dominant_field else None
    return profile, dominant


def _peak_submeter_profile(peak, df=None):
    """Read submeter values from the same minute as the observed household peak."""
    if df is not None and not df.empty and "Global_active_power" in df:
        row = df.loc[df["Global_active_power"].idxmax()]
        source = row.to_dict()
    else:
        source = peak or {}
    profile = {
        field: round(float(source[field]), 3)
        for field in SUBMETER_LABELS
        if source.get(field) is not None and pd.notna(source[field])
    }
    if not profile:
        return {}, None
    field = max(profile, key=profile.get)
    return profile, {"field": field, "label": SUBMETER_LABELS[field], "value": profile[field]}


def run(df=None, start_date=None, end_date=None):
    has_range = bool(start_date or end_date)
    if df is None:
        if has_range:
            raw_query = time_filter(start_date, end_date)
            df = frame("energy_data", raw_query)
            summary = consumption_summary(df)
            summary["analysis_day"] = (start_date or end_date or "")[:10]
            peaks = peak_periods(df)
            if not df.empty and "Global_active_power" in df:
                values = df["Global_active_power"].dropna()
                evening = values[values.index.hour.isin([18, 19, 20])]
                summary["evening_average"] = round(float(evening.mean()), 3) if len(evening) else None
                summary["average_demand"] = round(float(values.mean()), 3) if len(values) else None
                summary["evening_change_pct"] = round((summary["evening_average"] - summary["average_demand"]) / summary["average_demand"] * 100, 1) if summary["evening_average"] is not None and summary["average_demand"] else None
                summary["top_hours"] = [{"hour": int(hour), "average": round(float(value), 3)} for hour, value in values.groupby(values.index.hour).mean().nlargest(5).items()]
            else:
                summary.update({"evening_average": None, "evening_change_pct": None, "top_hours": []})
            compact = pd.DataFrame()
        else:
            compact = frame("hourly_energy")

            summary = dashboard_stats()
            peaks = top_peak_records(10)

        if not has_range and not compact.empty and "demand" in compact:
            values = compact["demand"].dropna()
            top_hours = values.groupby(values.index.hour).mean().nlargest(5)
            evening = values[values.index.hour.isin([18, 19, 20])]
            weekday = values[values.index.dayofweek < 5]
            weekend = values[values.index.dayofweek >= 5]
            summary["top_hours"] = [{"hour": int(k), "average": round(float(v), 3)} for k, v in top_hours.items()]
            summary["evening_average"] = round(float(evening.mean()), 3) if len(evening) else None
            baseline = summary.get("average_demand")
            summary["evening_change_pct"] = round((summary["evening_average"] - baseline) / baseline * 100, 1) if summary["evening_average"] is not None and baseline else None
            summary["weekday_average"] = round(float(weekday.mean()), 3) if len(weekday) else None
            summary["weekend_average"] = round(float(weekend.mean()), 3) if len(weekend) else None
        elif not has_range:
            summary.update({"top_hours": [], "evening_average": None, "evening_change_pct": None, "weekday_average": None, "weekend_average": None})
    else:
        if has_range and isinstance(df.index, pd.DatetimeIndex):
            tz = df.index.tz
            if start_date:
                df = df[df.index >= pd.Timestamp(start_date, tz=tz)]
            if end_date:
                df = df[df.index <= pd.Timestamp(end_date, tz=tz)]
        summary = consumption_summary(df)
        peaks = peak_periods(df)

    peak_submeter_profile, peak_submeter_driver = _peak_submeter_profile(peaks[0] if peaks else None, df)
    if peak_submeter_profile:
        summary["peak_submetering"] = peak_submeter_profile
        summary["peak_submeter_driver"] = peak_submeter_driver

    submeter_source = df if has_range else (df if df is not None else frame("energy_data"))
    submeter_profile, dominant_submeter = _submeter_evening_profile(submeter_source)
    if has_range and submeter_source is not None and not submeter_source.empty:
        available = [field for field in SUBMETER_LABELS if field in submeter_source]
        period_profile = {field: round(float(submeter_source[field].mean()), 3) for field in available if submeter_source[field].notna().any()}
        if period_profile:
            summary["submetering_period_average"] = period_profile
            field = max(period_profile, key=period_profile.get)
            summary["dominant_period_submeter"] = {"field": field, "label": SUBMETER_LABELS[field], "value": period_profile[field]}
            if has_range:
                summary["submetering_evening_average"] = period_profile
                summary["dominant_submeter"] = summary["dominant_period_submeter"]
    if submeter_profile:
        summary["submetering_evening_average"] = submeter_profile
        summary["dominant_submeter"] = dominant_submeter

    evidence = list(peaks[:5])
    if summary.get("analysis_day"):
        evidence.append({"label": "Selected analysis day", "value": summary["analysis_day"], "unit": "date"})
    for field, label in SUBMETER_LABELS.items():
        value = peak_submeter_profile.get(field)
        if value is not None:
            evidence.append({"label": f"Sub-meter reading at household peak: {label} ({field})", "value": value, "unit": "Wh"})
    if peak_submeter_driver:
        evidence.append({"label": "Largest sub-meter reading at household peak", "value": peak_submeter_driver["label"], "unit": "observed load contributor"})
    for key, label in (("average_demand", "Overall mean demand"), ("evening_average", "Mean demand (18:00-21:00)"),
                       ("evening_change_pct", "Evening change vs overall mean"),
                       ("weekday_average", "Weekday mean demand"), ("weekend_average", "Weekend mean demand")):
        if summary.get(key) is not None:
            evidence.append({"label": label, "value": summary[key], "unit": "%" if key == "evening_change_pct" else "kW"})
    for field, label in SUBMETER_LABELS.items():
        value = summary.get("submetering_period_average", {}).get(field) if has_range else summary.get("submetering_evening_average", {}).get(field)
        if value is not None:
            scope = "Selected-day mean" if has_range else "Evening mean"
            evidence.append({"label": f"{scope} {label} ({field})", "value": value, "unit": "Wh per minute"})
    if summary.get("dominant_submeter"):
        dominant = summary["dominant_submeter"]
        evidence.append({"label": "Dominant evening load driver", "value": dominant["label"], "unit": "submeter"})
    evidence.extend({"label": f"Average demand at {item['hour']:02d}:00", "value": item["average"], "unit": "kW"}
                    for item in summary.get("top_hours", []))

    date_str = f"{start_date} to {end_date}" if start_date and end_date else f"From {start_date}" if start_date else f"Until {end_date}" if end_date else "2006-12-16 to 2010-11-26 (Full Dataset)"
    citations = [{
        "dataset_name": "Individual Household Electric Power Consumption",
        "repository": "UCI Machine Learning Repository / EDF R&D",
        "collection": "hourly_energy",
        "date_range": date_str,
        "observations_analyzed": summary.get("observations", 0),
        "features": ["Global_active_power", "demand", "valid_samples", *SUBMETER_LABELS.keys()],
        "unit": "kW"
    }]

    return {"source_agent": "energy_data_agent", "target_agent": "insight_agent", "task": "energy_analysis",
            "data": summary, "evidence": evidence, "citations": citations,
            "confidence": min(1.0, summary.get("observations", 0) / 1000)}
