import pandas as pd


def basic_quality_checks(df: pd.DataFrame) -> dict:
    report = {}
    report['rows'] = len(df)
    report['columns'] = list(df.columns)
    report['missing_per_column'] = df.isna().sum().to_dict()
    report['start'] = df.index.min()
    report['end'] = df.index.max()
    return report


def resample_minute(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure regular minute frequency and forward-fill small gaps
    df = df.sort_index()
    df = df.resample('1T').mean()
    df = df.ffill(limit=5)
    return df


def cast_numeric(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


def feature_engineer(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['hour'] = df.index.hour
    df['dayofweek'] = df.index.dayofweek
    df['month'] = df.index.month
    df['is_weekend'] = df['dayofweek'] >= 5
    # rolling features
    df['global_active_power_60min_mean'] = df['Global_active_power'].rolling(60, min_periods=1).mean()
    return df
