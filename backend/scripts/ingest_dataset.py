"""Ingest UCI household data from a local semicolon-delimited file."""
import argparse
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from app.core.database import db, ensure_indexes
from app.ml.anomaly_detection import detect
from app.ml.preprocessing import preprocess_with_report


def ingest(path: Path, chunk_size=100_000):
    ensure_indexes()
    stage_energy = db.energy_data_staging
    stage_energy.drop()
    stage_energy.create_index("timestamp", unique=True)
    report = {"input_records": 0, "valid_records": 0, "invalid_timestamp_records": 0,
              "missing_value_records": 0, "missing_value_cells": 0,
              "duplicate_timestamp_records": 0, "inserted_records": 0}
    previous_timestamp = None
    for raw in pd.read_csv(path, sep=";", na_values=["?"], low_memory=False, chunksize=chunk_size):
        clean, chunk_report = preprocess_with_report(raw)
        for key, value in chunk_report.items():
            report[key] += value
        if not clean.empty and previous_timestamp is not None:
            if clean.index.min() < previous_timestamp:
                raise ValueError("Dataset timestamps are out of order across ingestion chunks; existing collections were left untouched.")
            if clean.index.min() == previous_timestamp:
                clean = clean.loc[clean.index > previous_timestamp]
                report["duplicate_timestamp_records"] += 1
                report["valid_records"] -= 1
        # MongoDB accepts IEEE NaN, but strict JSON responses do not. Persist
        # missing measurements as BSON null so aggregates and API output stay finite.
        serializable = clean.astype(object).where(pd.notna(clean), None)
        docs = serializable.reset_index().to_dict("records")
        if docs:
            stage_energy.insert_many(docs, ordered=False)
            report["inserted_records"] += len(docs)
            previous_timestamp = clean.index.max()
    if report["inserted_records"] == 0:
        raise ValueError("No valid timestamped energy readings were found; existing collections were left untouched.")
    # Materialize compact collections for common dashboard periods.
    hourly = list(stage_energy.aggregate([
        {"$group": {"_id": {"$dateTrunc": {"date": "$timestamp", "unit": "hour"}},
                    "demand": {"$avg": "$Global_active_power"}, "samples": {"$sum": 1},
                    "valid_samples": {"$sum": {"$cond": [{"$isNumber": "$Global_active_power"}, 1, 0]}},
                    "active_power_sum": {"$sum": {"$cond": [{"$isNumber": "$Global_active_power"}, "$Global_active_power", 0]}}}},
        {"$project": {"_id": 0, "timestamp": "$_id", "demand": 1, "samples": 1, "valid_samples": 1, "active_power_sum": 1}},
        {"$sort": {"timestamp": 1}}
    ]))
    daily = list(stage_energy.aggregate([
        {"$group": {"_id": {"$dateTrunc": {"date": "$timestamp", "unit": "day"}},
                    "demand": {"$avg": "$Global_active_power"}, "samples": {"$sum": 1},
                    "valid_samples": {"$sum": {"$cond": [{"$isNumber": "$Global_active_power"}, 1, 0]}},
                    "active_power_sum": {"$sum": {"$cond": [{"$isNumber": "$Global_active_power"}, "$Global_active_power", 0]}}}},
        {"$project": {"_id": 0, "date": "$_id", "demand": 1, "samples": 1, "valid_samples": 1, "active_power_sum": 1}},
        {"$sort": {"date": 1}}
    ]))
    stage_hourly = db.hourly_energy_staging
    stage_hourly.drop()
    stage_hourly.create_index("timestamp")
    if hourly:
        stage_hourly.insert_many(hourly)
    stage_daily = db.daily_energy_staging
    stage_daily.drop()
    stage_daily.create_index("date")
    if daily:
        stage_daily.insert_many(daily)
    stage_anomalies = db.anomalies_staging
    stage_anomalies.drop()
    stage_anomalies.create_index("timestamp")
    if hourly:
        hourly_frame = pd.DataFrame(hourly).set_index("timestamp").sort_index()
        hourly_frame = hourly_frame.rename(columns={"demand": "Global_active_power"})
        anomaly_docs = detect(hourly_frame, window=24)
        if anomaly_docs:
            stage_anomalies.insert_many(anomaly_docs)
    # Publish complete collections only after parsing and materialization succeed.
    stage_energy.rename("energy_data", dropTarget=True)
    stage_hourly.rename("hourly_energy", dropTarget=True)
    stage_daily.rename("daily_energy", dropTarget=True)
    stage_anomalies.rename("anomalies", dropTarget=True)
    ensure_indexes()
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", nargs="?", default=str(Path(__file__).resolve().parents[2] / "data" / "household_power_consumption.txt"))
    args = parser.parse_args()
    source = Path(args.dataset).resolve()
    if not source.exists():
        raise SystemExit(f"Dataset file not found: {source}")
    result = ingest(source)
    print("Ingestion report:")
    for key, value in result.items():
        print(f"  {key.replace('_', ' ').title()}: {value:,}")
