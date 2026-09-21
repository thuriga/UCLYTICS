from pathlib import Path

import pandas as pd


def load_matches(path=None):
    """Load and normalize match data into an analytics-ready DataFrame."""
    csv_path = Path(path) if path else Path(__file__).resolve().parents[1] / "data.csv"
    data = pd.read_csv(csv_path, skipinitialspace=True)
    data.columns = [column.strip() for column in data.columns]
    data = data.rename(columns={"Home Score": "Home Goals", "Away Score": "Away Goals"})

    required = {"Date", "Home Team", "Away Team", "Home Goals", "Away Goals"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    data["Date"] = pd.to_datetime(data["Date"], dayfirst=True, errors="coerce")
    for column in ["Home Goals", "Away Goals"]:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data = data.dropna(subset=["Date", "Home Goals", "Away Goals"]).copy()
    data["Home Goals"] = data["Home Goals"].astype(int)
    data["Away Goals"] = data["Away Goals"].astype(int)
    data["Score"] = data["Home Goals"].astype(str) + " - " + data["Away Goals"].astype(str)

    return data.sort_values("Date").reset_index(drop=True)
