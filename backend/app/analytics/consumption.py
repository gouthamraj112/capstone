import pandas as pd


def consumption_summary(df: pd.DataFrame) -> dict:
    if df.empty or "Global_active_power" not in df:
        return {"total_consumption": None, "average_demand": None, "peak_demand": None, "observations": 0}
    s = df["Global_active_power"].dropna()
    # Source UCI readings are one-minute mean kW values: kWh = sum(kW) / 60.
    return {"total_consumption": round(float(s.sum() / 60), 3), "average_demand": round(float(s.mean()), 3), "peak_demand": round(float(s.max()), 3), "observations": int(s.size)}


def grouped_consumption(df: pd.DataFrame, frequency: str) -> pd.Series:
    if df.empty or "Global_active_power" not in df:
        return pd.Series(dtype=float)
    return df["Global_active_power"].resample(frequency).mean().dropna()
