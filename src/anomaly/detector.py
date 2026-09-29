import numpy as np
import pandas as pd


class SimpleZScoreAnomalyDetector:
    def __init__(self, window=1440, z_thresh=3.0):
        self.window = window
        self.z_thresh = z_thresh

    def fit_predict(self, series: pd.Series) -> pd.DataFrame:
        s = series.fillna(method='ffill')
        rolling_mean = s.rolling(self.window, min_periods=1).mean()
        rolling_std = s.rolling(self.window, min_periods=1).std().fillna(0.0)
        z = (s - rolling_mean) / (rolling_std.replace(0, np.nan))
        anomalies = z.abs() > self.z_thresh
        return pd.DataFrame({'value': s, 'z': z, 'anomaly': anomalies})
