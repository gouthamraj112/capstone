import numpy as np
import pandas as pd


def forecast(series: pd.Series, hours=24) -> list[dict]:
    """Seasonal naive forecast using the previous day's same hour; requires observed data."""
    series = series.replace([np.inf, -np.inf], np.nan).dropna().resample("h").mean().dropna()
    if len(series) < 24:
        raise ValueError("At least 24 hourly observations are required to forecast")
    history = series.tail(24).to_numpy()
    spread = float(series.tail(min(168, len(series))).std() or 0)
    future = pd.date_range(series.index[-1] + pd.Timedelta(hours=1), periods=max(1, min(hours, 168)), freq="h", tz=series.index.tz)
    return [{"timestamp": ts.to_pydatetime(), "predicted_demand": float(history[i % 24]),
             "lower_bound": float(max(0, history[i % 24] - 1.96 * spread)),
             "upper_bound": float(history[i % 24] + 1.96 * spread)} for i, ts in enumerate(future)]
