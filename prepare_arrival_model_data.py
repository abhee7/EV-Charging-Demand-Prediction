import pandas as pd
import numpy as np
import os

INPUT_FILE = "data/processed/hourly_demand_arrival_hour.csv"
OUTPUT_FILE = "data/processed/model_data_arrival_hour.csv"

LOCAL_TZ = "America/Los_Angeles"
TARGET = "demand_kWh"

print("=" * 70)
print("ARRIVAL-HOUR MODEL DATA PREPARATION")
print("=" * 70)

print("\nLoading arrival-hour dataset...")

df = pd.read_csv(INPUT_FILE)

df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    utc=True
)

df = df.sort_values("timestamp").reset_index(drop=True)

print(f"Rows: {len(df):,}")

# ------------------------------------------------------------
# REGULAR HOURLY GRID
# ------------------------------------------------------------

full_index = pd.date_range(
    start=df["timestamp"].min(),
    end=df["timestamp"].max(),
    freq="h",
    tz="UTC"
)

df = (
    df.set_index("timestamp")
    .reindex(full_index)
)

df.index.name = "timestamp"

df[TARGET] = df[TARGET].fillna(0.0)

# ------------------------------------------------------------
# LOCAL CALENDAR FEATURES
# ------------------------------------------------------------

local_index = df.index.tz_convert(LOCAL_TZ)

df["hour"] = local_index.hour

df["day_of_week"] = local_index.dayofweek

df["day_of_month"] = local_index.day

df["month"] = local_index.month

df["week_of_year"] = (
    local_index.isocalendar()
    .week
    .astype(int)
)

df["is_weekend"] = (
    local_index.dayofweek >= 5
).astype(int)

df["is_business_hour"] = (
    (local_index.hour >= 8)
    &
    (local_index.hour < 18)
).astype(int)

# ------------------------------------------------------------
# LAG FEATURES
# ------------------------------------------------------------

for lag in [1, 2, 24, 48, 168, 336]:

    df[f"lag_{lag}"] = (
        df[TARGET].shift(lag)
    )

# ------------------------------------------------------------
# LEAKAGE-SAFE ROLLING FEATURES
# ------------------------------------------------------------

shifted = df[TARGET].shift(1)

df["rolling_mean_24"] = (
    shifted
    .rolling(window=24)
    .mean()
)

df["rolling_std_24"] = (
    shifted
    .rolling(window=24)
    .std()
)

df["rolling_mean_168"] = (
    shifted
    .rolling(window=168)
    .mean()
)

df["rolling_std_168"] = (
    shifted
    .rolling(window=168)
    .std()
)

# ------------------------------------------------------------
# RESET INDEX
# ------------------------------------------------------------

df = df.reset_index()

# ------------------------------------------------------------
# VALIDATION
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("VALIDATION")
print("=" * 70)

print(f"\nRows: {len(df):,}")

print(
    f"Date range:\n"
    f"  {df['timestamp'].min()}\n"
    f"  {df['timestamp'].max()}"
)

total_energy = df[TARGET].sum()

print(
    f"\nTotal energy: "
    f"{total_energy:,.3f} kWh"
)

timestamp_diff = (
    df["timestamp"].diff().dropna()
)

print(
    f"Maximum timestamp gap: "
    f"{timestamp_diff.max()}"
)

print(
    f"Non-1-hour gaps: "
    f"{(timestamp_diff != pd.Timedelta(hours=1)).sum()}"
)

print("\nMissing values:")

feature_columns = [
    "lag_1",
    "lag_2",
    "lag_24",
    "lag_48",
    "lag_168",
    "lag_336",
    "rolling_mean_24",
    "rolling_std_24",
    "rolling_mean_168",
    "rolling_std_168",
]

print(
    df[feature_columns]
    .isna()
    .sum()
    .to_string()
)

# ------------------------------------------------------------
# SAVE
# ------------------------------------------------------------

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n" + "=" * 70)
print("MODEL DATA CREATED")
print("=" * 70)

print(
    f"\nSaved to:\n"
    f"  {OUTPUT_FILE}"
)
