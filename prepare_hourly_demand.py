import os
import pandas as pd
import numpy as np

# ============================================================
# EV Charging Demand Prediction
# Stage 3: Prepare Hourly Charging Demand
# Dataset: ACN-Data Caltech
# ============================================================

RAW_FILE = "data/raw/acndata_caltech.csv"
OUTPUT_FILE = "data/processed/hourly_demand.csv"

# ------------------------------------------------------------
# 1. Load raw data
# ------------------------------------------------------------

print("Loading raw dataset...")

df = pd.read_csv(RAW_FILE)

print(f"Raw sessions: {len(df):,}")

# ------------------------------------------------------------
# 2. Parse timestamps
# ------------------------------------------------------------

time_columns = [
    "connectionTime",
    "doneChargingTime",
    "disconnectTime"
]

for col in time_columns:
    df[col] = pd.to_datetime(df[col], utc=True, errors="coerce")

# ------------------------------------------------------------
# 3. Basic structural filtering
# ------------------------------------------------------------

initial_count = len(df)

# Remove sessions without charging completion time
df = df.dropna(subset=["doneChargingTime"]).copy()

# Remove sessions where charging completion is not after connection
df["duration_seconds"] = (
    df["doneChargingTime"] - df["connectionTime"]
).dt.total_seconds()

df = df[df["duration_seconds"] > 0].copy()

# Remove invalid/non-positive energy
df = df[df["kWhDelivered"] > 0].copy()

print(f"Removed sessions: {initial_count - len(df):,}")
print(f"Usable sessions: {len(df):,}")

# ------------------------------------------------------------
# 4. Convert timestamps to local timezone
# ------------------------------------------------------------

# Caltech ACN data uses America/Los_Angeles.
LOCAL_TZ = "America/Los_Angeles"

df["connection_local"] = df["connectionTime"].dt.tz_convert(LOCAL_TZ)
df["done_local"] = df["doneChargingTime"].dt.tz_convert(LOCAL_TZ)

# ------------------------------------------------------------
# 5. Calculate charging duration and average charging rate
# ------------------------------------------------------------

df["duration_hours"] = df["duration_seconds"] / 3600.0

df["avg_power_kw"] = (
    df["kWhDelivered"] / df["duration_hours"]
)

# ------------------------------------------------------------
# 6. Allocate session energy across hourly intervals
# ------------------------------------------------------------

print("Allocating session energy across hourly intervals...")

hourly_energy = {}

for idx, row in df.iterrows():

    start = row["connection_local"]
    end = row["done_local"]
    energy = float(row["kWhDelivered"])
    power = float(row["avg_power_kw"])

    # Start of first hour
    current_hour = start.floor("h")

    while current_hour < end:

        next_hour = current_hour + pd.Timedelta(hours=1)

        # Actual overlap between charging interval and this hour
        overlap_start = max(start, current_hour)
        overlap_end = min(end, next_hour)

        overlap_seconds = (
            overlap_end - overlap_start
        ).total_seconds()

        if overlap_seconds > 0:

            allocated_energy = (
                power * overlap_seconds / 3600.0
            )

            hourly_energy[current_hour] = (
                hourly_energy.get(current_hour, 0.0)
                + allocated_energy
            )

        current_hour = next_hour

# ------------------------------------------------------------
# 7. Create continuous hourly time index
# ------------------------------------------------------------

if not hourly_energy:
    raise RuntimeError("No hourly energy was generated.")

start_hour = min(hourly_energy.keys())
end_hour = max(hourly_energy.keys())

hour_index = pd.date_range(
    start=start_hour,
    end=end_hour,
    freq="h",
    tz=LOCAL_TZ
)

hourly_df = pd.DataFrame(
    index=hour_index
)

hourly_df.index.name = "timestamp"

hourly_df["demand_kWh"] = [
    hourly_energy.get(ts, 0.0)
    for ts in hour_index
]

# ------------------------------------------------------------
# 8. Add calendar features
# ------------------------------------------------------------

hourly_df["hour"] = hourly_df.index.hour
hourly_df["day_of_week"] = hourly_df.index.dayofweek
hourly_df["day_of_month"] = hourly_df.index.day
hourly_df["month"] = hourly_df.index.month
hourly_df["week_of_year"] = hourly_df.index.isocalendar().week.astype(int)

hourly_df["is_weekend"] = (
    hourly_df["day_of_week"] >= 5
).astype(int)

hourly_df["is_business_hour"] = (
    (hourly_df["hour"] >= 8)
    & (hourly_df["hour"] < 18)
).astype(int)

# ------------------------------------------------------------
# 9. Save processed dataset
# ------------------------------------------------------------

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)

hourly_df.reset_index().to_csv(
    OUTPUT_FILE,
    index=False
)

# ------------------------------------------------------------
# 10. Print summary
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("HOURLY DATASET CREATED")
print("=" * 60)

print(f"Output file: {OUTPUT_FILE}")
print(f"Hourly observations: {len(hourly_df):,}")
print(f"Start: {hourly_df.index.min()}")
print(f"End:   {hourly_df.index.max()}")

print("\nDemand statistics:")
print(
    hourly_df["demand_kWh"]
    .describe()
    .round(3)
)

print("\nZero-demand hours:")
print(
    int((hourly_df["demand_kWh"] == 0).sum())
)

print("\nTotal reconstructed energy:")
print(
    round(hourly_df["demand_kWh"].sum(), 3),
    "kWh"
)

print("\nTop 10 demand hours:")
print(
    hourly_df
    .nlargest(10, "demand_kWh")[
        ["demand_kWh"]
    ]
    .round(3)
)

print("\nDone.")