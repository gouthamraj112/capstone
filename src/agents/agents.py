from typing import Any, Dict
import pandas as pd

class BaseAgent:
    def __init__(self, name: str):
        self.name = name

    def run(self, *args, **kwargs) -> Any:
        raise NotImplementedError()


class EnergyDataAgent(BaseAgent):
    def __init__(self, df: pd.DataFrame):
        super().__init__('EnergyDataAgent')
        self.df = df

    def run(self) -> Dict:
        return {'rows': len(self.df), 'start': self.df.index.min(), 'end': self.df.index.max()}


class AnomalyAgent(BaseAgent):
    def __init__(self, detector):
        super().__init__('AnomalyAgent')
        self.detector = detector

    def run(self, series: pd.Series) -> pd.DataFrame:
        return self.detector.fit_predict(series)


class ForecastAgent(BaseAgent):
    def __init__(self, model_fn):
        super().__init__('ForecastAgent')
        self.model_fn = model_fn

    def run(self, series: pd.Series, periods=24):
        return self.model_fn(series, periods=periods)


class InsightAgent(BaseAgent):
    def __init__(self):
        super().__init__('InsightAgent')

    def run(self, analyses: Dict) -> Dict:
        # combine results into simple natural language messages
        msg = {}
        msg['summary'] = f"Data from {analyses['start']} to {analyses['end']} ({analyses['rows']} rows)"
        return msg
