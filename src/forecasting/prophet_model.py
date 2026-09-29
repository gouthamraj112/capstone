import pandas as pd
try:
    from prophet import Prophet
except Exception:
    Prophet = None


def fit_prophet(series: pd.Series, periods: int = 24):
    if Prophet is None:
        raise RuntimeError('Prophet not installed')
    df = series.reset_index()
    df.columns = ['ds', 'y']
    m = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=True)
    m.fit(df)
    future = m.make_future_dataframe(periods=periods, freq='H')
    forecast = m.predict(future)
    return m, forecast


def forecast_metrics(actual: pd.Series, forecast_df: pd.DataFrame) -> dict:
    # align on ds
    f = forecast_df.set_index('ds')
    common = actual.index.intersection(f.index)
    y_true = actual.loc[common]
    y_pred = f.loc[common]['yhat']
    mae = (y_true - y_pred).abs().mean()
    rmse = ((y_true - y_pred) ** 2).mean() ** 0.5
    mape = ((y_true - y_pred).abs() / (y_true.replace(0, 1))).mean()
    return {'mae': mae, 'rmse': rmse, 'mape': mape}


def fit_sarimax(series: pd.Series, periods: int = 24):
    # lightweight fallback using statsmodels SARIMAX
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX
    except Exception as e:
        raise RuntimeError('statsmodels not available') from e

    # simple weekly-seasonal SARIMA as fallback
    s = series.asfreq('H').fillna(method='ffill')
    model = SARIMAX(s, order=(1, 0, 1), seasonal_order=(1, 1, 1, 24))
    res = model.fit(disp=False)
    future_idx = pd.date_range(start=s.index[-1] + pd.Timedelta(hours=1), periods=periods, freq='H')
    pred = res.get_forecast(steps=periods)
    pred_df = pred.summary_frame()
    pred_df = pred_df.rename(columns={'mean': 'yhat'})
    pred_df['ds'] = future_idx
    pred_df = pred_df.reset_index(drop=True)
    return res, pred_df

