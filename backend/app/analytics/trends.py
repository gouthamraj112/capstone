import pandas as pd


def patterns(df: pd.DataFrame) -> dict:
    if df.empty or "Global_active_power" not in df:
        return {"hourly": [], "weekday_weekend": [], "monthly": []}
    s = df["Global_active_power"].dropna()
    return {
        "hourly": [{"hour": int(k), "average": round(float(v), 3)} for k, v in s.groupby(s.index.hour).mean().items()],
        "weekday_weekend": [{"period": "Weekend" if bool(k) else "Weekday", "average": round(float(v), 3)} for k, v in s.groupby(s.index.dayofweek >= 5).mean().items()],
        "monthly": [{"month": int(k), "average": round(float(v), 3)} for k, v in s.groupby(s.index.month).mean().items()],
        "yearly": [{"year": int(k), "average": round(float(v), 3)} for k, v in s.groupby(s.index.year).mean().items()],
    }
