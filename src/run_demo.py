"""Legacy command adapter: ingest the real local UCI file into MongoDB."""
import os
import sys

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from scripts.ingest_dataset import ingest  # noqa: E402


def main():
    data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "household_power_consumption.txt"))
    if not os.path.exists(data_path):
        raise SystemExit(f"Dataset not found: {data_path}. Add the UCI dataset and retry.")
    report = ingest(data_path)
    print(f"Ingested {report['inserted_records']:,} cleaned observations into local MongoDB.")


if __name__ == "__main__":
    main()
