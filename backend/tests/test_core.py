import numpy as np
import pandas as pd

from app.analytics.consumption import consumption_summary
from app.analytics.peaks import peak_periods
from app.ml.anomaly_detection import detect
from app.ml.evaluation import evaluate_controlled_anomalies, evaluate_seasonal_forecast, forecast_metrics
from app.ml.forecasting import forecast
from app.ml.preprocessing import preprocess, preprocess_with_report
from app.services.energy_service import format_timestamp, json_records
from app.services.llm_service import explain, numbers_are_evidence_backed
from app.core.config import settings
from app.api.routes.query import classify
from app.agents.energy_data_agent import run


def test_preprocessing_parses_deduplicates_sorts_and_builds_features():
    raw = pd.DataFrame({"Date": ["16/12/2006", "16/12/2006", "bad"],
                        "Time": ["17:24:00", "17:24:00", "00:00:00"],
                        "Global_active_power": ["?", "2.5", "4"]})
    result = preprocess(raw)
    assert len(result) == 1
    assert result.index[0] == pd.Timestamp("2006-12-16 17:24:00")
    assert result.iloc[0]["Global_active_power"] == 2.5
    assert result.iloc[0]["is_peak_hour"]


def test_preprocessing_report_counts_invalid_missing_and_duplicate_rows():
    raw = pd.DataFrame({"Date": ["16/12/2006", "16/12/2006", "not-a-date"],
                        "Time": ["17:24:00", "17:24:00", "00:00:00"],
                        "Global_active_power": ["?", "2.5", "3"]})
    result, report = preprocess_with_report(raw)
    assert len(result) == 1
    assert report == {"input_records": 3, "valid_records": 1, "invalid_timestamp_records": 1,
                      "missing_value_records": 1, "missing_value_cells": 1,
                      "duplicate_timestamp_records": 1}


def test_summary_and_peak_periods_use_observed_values():
    idx = pd.date_range("2024-01-01", periods=3, freq="h")
    df = pd.DataFrame({"Global_active_power": [1., 2., 7.]}, index=idx)
    assert consumption_summary(df)["average_demand"] == 3.333
    assert peak_periods(df, 1)[0]["demand"] == 7


def test_anomaly_detector_finds_controlled_spike():
    idx = pd.date_range("2024-01-01", periods=48 * 60, freq="min")
    values = np.ones(len(idx))
    values[-1] = 15
    found = detect(pd.DataFrame({"Global_active_power": values}, index=idx))
    assert found and found[-1]["severity"] == "high"


def test_anomaly_detector_finds_controlled_high_and_low_events():
    idx = pd.date_range("2024-01-01", periods=48 * 60, freq="min")
    values = np.ones(len(idx))
    values[-2] = 12
    values[-1] = 0
    found = detect(pd.DataFrame({"Global_active_power": values}, index=idx))
    assert {item["timestamp"] for item in found} == {idx[-2].to_pydatetime(), idx[-1].to_pydatetime()}
    assert found[0]["deviation"] > 0
    assert found[1]["deviation"] < 0
    assert "exceeded" in found[0]["reason"]
    assert "fell below" in found[1]["reason"]
    assert all(0 <= item["anomaly_score"] <= 1 for item in found)


def test_seasonal_forecast_and_error_metrics():
    idx = pd.date_range("2024-01-01", periods=48, freq="h")
    series = pd.Series(np.arange(48, dtype=float), index=idx)
    result = forecast(series, 6)
    assert len(result) == 6
    assert result[0]["predicted_demand"] == 24
    assert forecast_metrics([1, 2], [2, 2])["mae"] == .5


def test_api_timestamp_serialization_preserves_source_wall_clock():
    assert format_timestamp(pd.Timestamp("2006-12-16 17:24:00")) == "2006-12-16T17:24:00"
    assert format_timestamp(pd.Timestamp("2006-12-16 17:24:00", tz="UTC")) == "2006-12-16T17:24:00"


def test_json_series_converts_missing_and_nonfinite_values_to_null():
    idx = pd.date_range("2024-01-01", periods=3, freq="h")
    result = json_records(pd.Series([1.0, np.nan, np.inf], index=idx), "demand")
    assert [row["demand"] for row in result] == [1.0, None, None]


def test_llm_numeric_claims_must_match_supplied_evidence():
    evidence = [{"label": "Evening change", "value": 40.6, "unit": "%"}]
    assert numbers_are_evidence_backed("Demand changed by 40.6%.", evidence)
    assert not numbers_are_evidence_backed("Demand changed by 99%.", evidence)


def test_missing_llm_key_uses_analytics_fallback(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "")
    assert explain("Explain this", [], "Evidence-based result") == ("Evidence-based result", "analytics_fallback")


def test_semantic_reasoning_for_peak_hour_questions():
    intents = [
        classify("Why are peak hours using more electricity during the evening?")[0],
        classify("Why are peak hours using more electricity?")[0],
        classify("Why do peak hours consume more electricity?" )[0],
    ]
    assert intents == ["evening_increase", "evening_increase", "evening_increase"]


def test_evening_explanation_uses_submeter_evidence():
    idx = pd.date_range("2024-01-01 17:00", periods=8, freq="min")
    df = pd.DataFrame({
        "Global_active_power": [2.0, 2.1, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0],
        "Sub_metering_1": [0.0, 0.0, 0.5, 1.0, 1.0, 1.5, 1.5, 1.2],
        "Sub_metering_2": [1.0, 1.1, 1.5, 2.0, 2.0, 2.5, 2.8, 2.4],
        "Sub_metering_3": [1.0, 1.2, 1.8, 3.5, 6.0, 7.1, 8.5, 9.2],
    }, index=idx)
    result = run(df=df)
    sub = result["data"].get("submetering_evening_average", {})
    assert sub
    assert sub["Sub_metering_3"] > sub["Sub_metering_1"]
    assert sub["Sub_metering_3"] > sub["Sub_metering_2"]


def test_openrouter_model_fallback_uses_supported_model_list(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_model", "google/gemini-2.0-flash-001")
    models = __import__("app.services.llm_service", fromlist=["_openrouter_model_candidates"])._openrouter_model_candidates()
    assert models[0] == "google/gemini-2.0-flash-001"
    assert "openai/gpt-4o-mini" in models
    assert "google/gemini-2.5-flash" in models


def test_forecast_evaluation_uses_chronological_holdout():
    idx = pd.date_range("2024-01-01", periods=96, freq="h")
    series = pd.Series(np.tile(np.arange(24, dtype=float) + 1, 4), index=idx)
    result = evaluate_seasonal_forecast(series, holdout_hours=24)
    assert result["training_observations"] == 72
    assert result["mae"] == result["rmse"] == result["mape"] == 0


def test_controlled_anomaly_validation_labels_only_injected_events():
    idx = pd.date_range("2024-01-01", periods=96, freq="h")
    series = pd.Series(np.tile(np.arange(24, dtype=float) + 1, 4), index=idx)
    result = evaluate_controlled_anomalies(series)
    assert result["injected_anomalies"] == 2
    assert result["precision"] == result["recall"] == result["f1"] == 1
    assert "not accuracy against labeled real events" in result["methodology"]
