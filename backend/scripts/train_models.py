"""The baseline models are fit on demand; this script reports available MongoDB coverage."""
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import db
from app.services.energy_service import anomaly_count, dashboard_stats

stats = dashboard_stats()
obs = stats.get("observations", 0) or db.energy_data.estimated_document_count()
anomalies = anomaly_count()
print(f"Stored energy observations available: {obs:,}")
print(f"Detected anomalies: {anomalies:,}")
print(f"Average demand: {stats.get('average_demand')} kW | Peak demand: {stats.get('peak_demand')} kW")
print("Forecasting uses a seasonal-naive 24-hour baseline; fitted on demand.")
