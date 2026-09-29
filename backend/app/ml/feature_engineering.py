import pandas as pd


def add_time_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    idx = result.index
    result["hour"] = idx.hour
    result["day_of_week"] = idx.dayofweek
    result["month"] = idx.month
    result["is_weekend"] = idx.dayofweek >= 5
    result["is_peak_hour"] = idx.hour.isin(range(17, 22))
    return result
