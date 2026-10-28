import os
import pandas as pd
import numpy as np

INPUT_FILE = "data/processed/hourly_demand.csv"
OUTPUT_FILE = "data/processed/model_data.csv"

print("Loading hourly demand data...")

df = pd.read_csv(INPUT_FILE)

df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    utc=True
)

df = df.sort_values("timestamp").copy()

print("Creating regular UTC hourly timeline...")

full_index = pd.date_range(
    start=df["timestamp"].min().floor("h"),
    end=df["timestamp"].max().floor("h"),
    freq="h",
    tz="UTC"
)

df = (
    df.set_index("timestamp")
      .reindex(full_index)
      .rename_axis("timestamp")
      .reset_index()
)

# Missing hourly observations represent no recorded charging demand.
df["demand_kWh"] = df["demand_kWh"].fillna(0)

LOCAL_TZ = "America/Los_Angeles"

local_time = df["timestamp"].dt.tz_convert(LOCAL_TZ)

df["hour"] = local_time.dt.hour
df["day_of_week"] = local_time.dt.dayofweek
df["day_of_month"] = local_time.dt.day
df["month"] = local_time.dt.month
df["week_of_year"] = local_time.dt.isocalendar().week.astype(int)

df["is_weekend"] = (
    df["day_of_week"] >= 5
).astype(int)

df["is_business_hour"] = (
    (df["hour"] >= 8)
    & (df["hour"] < 18)
).astype(int)

print("Creating lag features...")

df["lag_1"] = df["demand_kWh"].shift(1)
df["lag_2"] = df["demand_kWh"].shift(2)
df["lag_24"] = df["demand_kWh"].shift(24)
df["lag_48"] = df["demand_kWh"].shift(48)
df["lag_168"] = df["demand_kWh"].shift(168)
df["lag_336"] = df["demand_kWh"].shift(336)

print("Creating leakage-safe rolling features...")

# Shift first so the current target is NEVER included.
past_demand = df["demand_kWh"].shift(1)

df["rolling_mean_24"] = (
    past_demand
    .rolling(window=24, min_periods=24)
    .mean()
)

df["rolling_std_24"] = (
    past_demand
    .rolling(window=24, min_periods=24)
    .std()
)

df["rolling_mean_168"] = (
    past_demand
    .rolling(window=168, min_periods=168)
    .mean()
)

df["rolling_std_168"] = (
    past_demand
    .rolling(window=168, min_periods=168)
    .std()
)

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n" + "=" * 60)
print("MODEL DATASET CREATED")
print("=" * 60)

print(f"Output: {OUTPUT_FILE}")
print(f"Rows: {len(df):,}")
print(f"Columns: {len(df.columns)}")

print("\nColumns:")
print(df.columns.tolist())

print("\nDate range:")
print(df["timestamp"].min())
print("to")
print(df["timestamp"].max())

print("\nMissing values:")
print(df.isna().sum())

print("\nEnergy validation:")
hourly_total = pd.read_csv(INPUT_FILE)["demand_kWh"].sum()
model_total = df["demand_kWh"].sum()

print(f"Hourly dataset total: {hourly_total:.6f} kWh")
print(f"Model dataset total:  {model_total:.6f} kWh")
print(f"Difference:           {model_total - hourly_total:.6f} kWh")

print("\nTimeline validation:")

diffs = df["timestamp"].diff().dropna()

print(f"Maximum time gap: {diffs.max()}")
print(
    f"Non-1-hour gaps: "
    f"{(diffs != pd.Timedelta(hours=1)).sum()}"
)

print("\nDone.")