import pandas as pd


def peak_periods(df: pd.DataFrame, limit=10) -> list[dict]:
    if df.empty or "Global_active_power" not in df:
        return []
    peaks = df["Global_active_power"].dropna().nlargest(limit)
    return [{"timestamp": str(ts), "demand": round(float(value), 3)} for ts, value in peaks.items()]
