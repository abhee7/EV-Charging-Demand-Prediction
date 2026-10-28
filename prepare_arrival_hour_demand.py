import os
import pandas as pd

INPUT_FILE = "data/raw/acndata_caltech.csv"
OUTPUT_FILE = "data/processed/hourly_demand_arrival_hour.csv"
LOCAL_TZ = "America/Los_Angeles"

print("=" * 70)
print("ARRIVAL-HOUR EV CHARGING DEMAND RECONSTRUCTION")
print("=" * 70)

df = pd.read_csv(INPUT_FILE)

print(f"Raw sessions: {len(df):,}")

df["connectionTime"] = pd.to_datetime(
    df["connectionTime"],
    utc=True,
    errors="coerce"
)

df["kWhDelivered"] = pd.to_numeric(
    df["kWhDelivered"],
    errors="coerce"
)

df = df.dropna(
    subset=["connectionTime", "kWhDelivered"]
).copy()

df = df[df["kWhDelivered"] > 0].copy()

print(f"Usable sessions: {len(df):,}")

df["connectionTime_local"] = (
    df["connectionTime"].dt.tz_convert(LOCAL_TZ)
)

df["hour_timestamp"] = (
    df["connectionTime_local"].dt.floor("h")
)

hourly_energy = (
    df.groupby("hour_timestamp")["kWhDelivered"]
    .sum()
    .sort_index()
)

start = hourly_energy.index.min()
end = hourly_energy.index.max()

full_index = pd.date_range(
    start=start,
    end=end,
    freq="h",
    tz=LOCAL_TZ
)

hourly = (
    hourly_energy
    .reindex(full_index, fill_value=0.0)
    .rename("demand_kWh")
    .to_frame()
)

hourly.index.name = "timestamp"

hourly["hour"] = hourly.index.hour
hourly["day_of_week"] = hourly.index.dayofweek
hourly["day_of_month"] = hourly.index.day
hourly["month"] = hourly.index.month
hourly["week_of_year"] = hourly.index.isocalendar().week.astype(int)
hourly["is_weekend"] = (
    hourly.index.dayofweek >= 5
).astype(int)
hourly["is_business_hour"] = (
    (hourly.index.hour >= 8)
    & (hourly.index.hour < 18)
).astype(int)

hourly = hourly.reset_index()

raw_total = df["kWhDelivered"].sum()
hourly_total = hourly["demand_kWh"].sum()

print("=" * 70)
print("VALIDATION")
print("=" * 70)

print(f"Hourly observations: {len(hourly):,}")
print(f"Date range: {hourly['timestamp'].min()} to {hourly['timestamp'].max()}")
print(f"Raw total energy: {raw_total:,.3f} kWh")
print(f"Hourly total energy: {hourly_total:,.3f} kWh")
print(f"Difference: {hourly_total - raw_total:.12f} kWh")
print(f"Mean hourly demand: {hourly['demand_kWh'].mean():.3f} kWh")
print(f"Median hourly demand: {hourly['demand_kWh'].median():.3f} kWh")
print(f"Maximum hourly demand: {hourly['demand_kWh'].max():.3f} kWh")
print(f"Zero-demand hours: {(hourly['demand_kWh'] == 0).sum():,}")

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

hourly.to_csv(OUTPUT_FILE, index=False)

print("=" * 70)
print("SAVED")
print("=" * 70)
print(OUTPUT_FILE)
