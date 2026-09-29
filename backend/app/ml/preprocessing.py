import pandas as pd

NUMERIC_COLUMNS = ["Global_active_power", "Global_reactive_power", "Voltage", "Global_intensity", "Sub_metering_1", "Sub_metering_2", "Sub_metering_3"]


def preprocess(raw: pd.DataFrame) -> pd.DataFrame:
    """Parse UCI semicolon data; invalid readings become null, timestamps are deduped and sorted.

    Missing power readings are interpolated only for gaps of at most five minutes;
    longer gaps remain missing to avoid inventing extended consumption periods.
    """
    df, _ = preprocess_with_report(raw)
    return df


def preprocess_with_report(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Preprocess one source chunk and return auditable row and missing-value counts."""
    df = raw.copy()
    input_count = len(df)
    if "Date" in df and "Time" in df:
        timestamp = pd.to_datetime(df["Date"].astype(str) + " " + df["Time"].astype(str), dayfirst=True, errors="coerce")
        df = df.drop(columns=["Date", "Time"])
        df.insert(0, "timestamp", timestamp)
    elif "timestamp" in df:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    invalid_timestamps = int(df["timestamp"].isna().sum())
    df = df.dropna(subset=["timestamp"])
    for col in NUMERIC_COLUMNS:
        if col in df:
            df[col] = pd.to_numeric(df[col].replace("?", None), errors="coerce")
            df[col] = df[col].replace([float("inf"), float("-inf")], pd.NA)
    numeric = [column for column in NUMERIC_COLUMNS if column in df]
    missing_value_records = int(df[numeric].isna().any(axis=1).sum()) if numeric else 0
    missing_value_cells = int(df[numeric].isna().sum().sum()) if numeric else 0
    duplicate_timestamps = int(df.duplicated("timestamp", keep="last").sum())
    df = df.sort_values("timestamp").drop_duplicates("timestamp", keep="last")
    valid_count = len(df)
    df = df.set_index("timestamp")
    if "Global_active_power" in df:
        df["Global_active_power"] = df["Global_active_power"].interpolate(limit=5, limit_area="inside")
    ts = df.index
    df["hour"] = ts.hour
    df["day"] = ts.day
    df["month"] = ts.month
    df["year"] = ts.year
    df["day_of_week"] = ts.dayofweek
    df["week_of_year"] = ts.isocalendar().week.astype(int).to_numpy()
    df["is_weekend"] = (ts.dayofweek >= 5)
    df["is_night"] = (ts.hour < 6) | (ts.hour >= 22)
    df["is_peak_hour"] = ts.hour.isin(range(17, 22))
    return df, {"input_records": input_count, "valid_records": valid_count,
                "invalid_timestamp_records": invalid_timestamps,
                "missing_value_records": missing_value_records,
                "missing_value_cells": missing_value_cells,
                "duplicate_timestamp_records": duplicate_timestamps}
