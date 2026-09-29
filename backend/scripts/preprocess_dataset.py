from pathlib import Path
import sys
import pandas as pd

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ml.preprocessing import preprocess

source = Path(__file__).resolve().parents[2] / "data" / "household_power_consumption.txt"
raw = pd.read_csv(source, sep=";", na_values=["?"], low_memory=False)
clean = preprocess(raw)
target = Path(__file__).resolve().parents[2] / "data" / "household_power_clean.csv"
clean.to_csv(target, index_label="timestamp")
print(f"Wrote {len(clean):,} cleaned rows to {target.resolve()}")
