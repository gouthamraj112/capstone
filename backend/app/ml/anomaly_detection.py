import numpy as np
import pandas as pd


def detect(df: pd.DataFrame, window: int = 1440) -> list[dict]:
    if df.empty or "Global_active_power" not in df:
        return []
    values = df["Global_active_power"].dropna()
    if len(values) < 10:
        return []
    min_periods = min(30, max(2, window // 4))
    rolling_expected = values.rolling(window, min_periods=min_periods).median()
    seasonal_valid = None
    scale_residual = None
    if isinstance(values.index, pd.DatetimeIndex):
        # Compare with earlier readings at the same minute of the day so normal
        # daily demand cycles are not mislabeled as anomalies.
        bucket = values.index.hour * 60 + values.index.minute
        seasonal_expected = values.groupby(bucket, sort=False).transform(
            lambda same_time: same_time.shift(1).rolling(7, min_periods=1).median())
        seasonal_valid = seasonal_expected.notna()
        expected = seasonal_expected.fillna(rolling_expected).fillna(values.median())
        scale_residual = (values - expected).where(seasonal_valid)
    else:
        expected = rolling_expected.fillna(values.median())
    residual = values - expected
    residual_for_scale = scale_residual if scale_residual is not None else residual
    rolling_mad = residual_for_scale.abs().rolling(window, min_periods=min_periods).median()
    if isinstance(values.index, pd.DatetimeIndex):
        seasonal_mad = residual_for_scale.abs().groupby(bucket, sort=False).transform(
            lambda same_time: same_time.shift(1).rolling(7, min_periods=1).median())
        mad = seasonal_mad.fillna(rolling_mad).replace(0, np.nan)
    else:
        mad = rolling_mad.replace(0, np.nan)
    # A flat baseline has zero MAD; use a 5% median scale floor for either direction.
    scale_floor = max(float(values.median()) * 0.05, 1e-6)
    mad = mad.fillna(scale_floor)
    score = residual.abs() / (1.4826 * mad.replace(0, np.nan))
    flagged = score >= 3.5
    if seasonal_valid is not None:
        flagged &= seasonal_valid
    out = []
    for ts in values.index[flagged.fillna(False)]:
        actual, baseline, z = float(values.loc[ts]), float(expected.loc[ts]), float(score.loc[ts])
        deviation = actual - baseline
        out.append({"timestamp": ts.to_pydatetime(), "actual_value": actual, "expected_value": baseline,
                    "deviation": deviation, "anomaly_score": min(1.0, z / 8),
                    "severity": "high" if z >= 6 else "medium" if z >= 4.5 else "low",
                    "reason": ("Consumption exceeded the robust expected range" if deviation > 0
                               else "Consumption fell below the robust expected range")})
    return out
