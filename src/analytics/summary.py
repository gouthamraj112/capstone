import pandas as pd


def consumption_trends(df: pd.DataFrame) -> pd.Series:
    # daily aggregated global active power
    daily = df['Global_active_power'].resample('D').sum()
    return daily


def peak_periods(df: pd.DataFrame, top_n=5) -> pd.DataFrame:
    # find top N highest consumption hours
    hourly = df['Global_active_power'].resample('H').sum()
    top = hourly.sort_values(ascending=False).head(top_n)
    return top


def seasonal_profile(df: pd.DataFrame) -> pd.DataFrame:
    # average hourly profile by day of week
    prof = df.groupby([df.index.hour, df.index.dayofweek])['Global_active_power'].mean().unstack()
    return prof
