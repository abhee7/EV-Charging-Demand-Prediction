import os
import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

DEMAND_FILE = "data/processed/hourly_demand.csv"

PREDICTIONS_FILE = (
    "results/predictions/test_predictions_corrected.csv"
)

SARIMAX_FILE = (
    "results/predictions/"
    "sarimax_fourier_test_predictions.csv"
)

OUTPUT_DIR = "results/peak_analysis"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# LOAD HOURLY DEMAND
# ============================================================

print("=" * 70)
print("EV CHARGING DEMAND PEAK ANALYSIS")
print("=" * 70)

print("\nLoading hourly demand...")

df = pd.read_csv(DEMAND_FILE)

# IMPORTANT:
# utc=True handles the mixed timezone offsets caused by
# daylight-saving time in the California timestamps.
df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    utc=True
)

df = (
    df
    .sort_values("timestamp")
    .reset_index(drop=True)
)

print(
    f"Hourly observations: "
    f"{len(df):,}"
)

print(
    f"Date range: "
    f"{df['timestamp'].min()} "
    f"to "
    f"{df['timestamp'].max()}"
)


# ============================================================
# BASIC DEMAND STATISTICS
# ============================================================

print("\n" + "=" * 70)
print("OVERALL DEMAND STATISTICS")
print("=" * 70)

mean_demand = df["demand_kWh"].mean()
median_demand = df["demand_kWh"].median()
std_demand = df["demand_kWh"].std()
peak_demand = df["demand_kWh"].max()
minimum_demand = df["demand_kWh"].min()

zero_hours = (
    df["demand_kWh"] == 0
).sum()

total_energy = (
    df["demand_kWh"].sum()
)

peak_to_average = (
    peak_demand / mean_demand
)

summary = pd.DataFrame([{

    "observations":
        len(df),

    "mean_hourly_demand_kWh":
        mean_demand,

    "median_hourly_demand_kWh":
        median_demand,

    "std_hourly_demand_kWh":
        std_demand,

    "minimum_hourly_demand_kWh":
        minimum_demand,

    "peak_hourly_demand_kWh":
        peak_demand,

    "total_reconstructed_energy_kWh":
        total_energy,

    "zero_demand_hours":
        zero_hours,

    "peak_to_average_ratio":
        peak_to_average,

}])


summary_file = os.path.join(
    OUTPUT_DIR,
    "overall_demand_summary.csv"
)

summary.to_csv(
    summary_file,
    index=False
)

print(
    summary.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)


# ============================================================
# TOP 10 PEAK HOURS
# ============================================================

print("\n" + "=" * 70)
print("TOP 10 PEAK DEMAND HOURS")
print("=" * 70)

top_peaks = (
    df[
        [
            "timestamp",
            "demand_kWh"
        ]
    ]
    .sort_values(
        "demand_kWh",
        ascending=False
    )
    .head(10)
    .reset_index(drop=True)
)

top_peaks.insert(
    0,
    "rank",
    np.arange(
        1,
        len(top_peaks) + 1
    )
)

top_peaks_file = os.path.join(
    OUTPUT_DIR,
    "top_10_peak_hours.csv"
)

top_peaks.to_csv(
    top_peaks_file,
    index=False
)

print(
    top_peaks.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)


# ============================================================
# HOURLY PROFILE
# ============================================================

print("\n" + "=" * 70)
print("HOURLY DEMAND PROFILE")
print("=" * 70)

# Convert UTC timestamps back to California local time
# for local hour-of-day analysis.
local_timestamp = (
    df["timestamp"]
    .dt.tz_convert(
        "America/Los_Angeles"
    )
)

hourly_profile = (
    df.assign(
        local_timestamp=local_timestamp,
        hour=local_timestamp.dt.hour
    )
    .groupby("hour")[
        "demand_kWh"
    ]
    .agg(
        mean_demand_kWh="mean",
        median_demand_kWh="median",
        max_demand_kWh="max",
        std_demand_kWh="std",
        observations="count"
    )
    .reset_index()
)

hourly_profile_file = os.path.join(
    OUTPUT_DIR,
    "hourly_demand_profile.csv"
)

hourly_profile.to_csv(
    hourly_profile_file,
    index=False
)

print(
    hourly_profile.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)


# ============================================================
# DAY-OF-WEEK PROFILE
# ============================================================

weekday_names = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]

day_of_week_local = (
    local_timestamp.dt.dayofweek
)

weekday_profile = (
    df.assign(
        day_of_week=day_of_week_local
    )
    .groupby(
        "day_of_week"
    )[
        "demand_kWh"
    ]
    .agg(
        mean_demand_kWh="mean",
        median_demand_kWh="median",
        max_demand_kWh="max",
        std_demand_kWh="std",
        observations="count"
    )
    .reset_index()
)

weekday_profile["day_name"] = (
    weekday_profile[
        "day_of_week"
    ].map(
        dict(
            enumerate(
                weekday_names
            )
        )
    )
)

weekday_profile = (
    weekday_profile[
        [
            "day_of_week",
            "day_name",
            "mean_demand_kWh",
            "median_demand_kWh",
            "max_demand_kWh",
            "std_demand_kWh",
            "observations"
        ]
    ]
)

weekday_file = os.path.join(
    OUTPUT_DIR,
    "day_of_week_profile.csv"
)

weekday_profile.to_csv(
    weekday_file,
    index=False
)


# ============================================================
# WEEKDAY VS WEEKEND
# ============================================================

is_weekend = (
    local_timestamp.dt.dayofweek >= 5
)

weekend_profile = (
    df.assign(
        is_weekend=is_weekend
    )
    .groupby("is_weekend")[
        "demand_kWh"
    ]
    .agg(
        mean_demand_kWh="mean",
        median_demand_kWh="median",
        max_demand_kWh="max",
        std_demand_kWh="std",
        observations="count"
    )
    .reset_index()
)

weekend_profile["period"] = np.where(
    weekend_profile["is_weekend"],
    "Weekend",
    "Weekday"
)

weekend_profile = (
    weekend_profile[
        [
            "period",
            "mean_demand_kWh",
            "median_demand_kWh",
            "max_demand_kWh",
            "std_demand_kWh",
            "observations"
        ]
    ]
)

weekend_file = os.path.join(
    OUTPUT_DIR,
    "weekday_weekend_profile.csv"
)

weekend_profile.to_csv(
    weekend_file,
    index=False
)


# ============================================================
# MONTHLY PROFILE
# ============================================================

local_month = (
    local_timestamp.dt.month
)

local_month_name = (
    local_timestamp.dt.month_name()
)

monthly_profile = (
    df.assign(
        month=local_month,
        month_name=local_month_name
    )
    .groupby(
        [
            "month",
            "month_name"
        ]
    )[
        "demand_kWh"
    ]
    .agg(
        mean_demand_kWh="mean",
        median_demand_kWh="median",
        max_demand_kWh="max",
        std_demand_kWh="std",
        total_energy_kWh="sum",
        observations="count"
    )
    .reset_index()
    .sort_values("month")
)

monthly_file = os.path.join(
    OUTPUT_DIR,
    "monthly_demand_profile.csv"
)

monthly_profile.to_csv(
    monthly_file,
    index=False
)


# ============================================================
# HIGH-DEMAND THRESHOLDS
# ============================================================

print("\n" + "=" * 70)
print("HIGH-DEMAND ANALYSIS")
print("=" * 70)

# Percentile-based thresholds avoid arbitrary kWh thresholds.

percentiles = {
    "P75": 0.75,
    "P90": 0.90,
    "P95": 0.95,
    "P99": 0.99,
}

threshold_rows = []

for label, percentile in percentiles.items():

    threshold = (
        df["demand_kWh"]
        .quantile(percentile)
    )

    hours = (
        df["demand_kWh"]
        >= threshold
    ).sum()

    percentage = (
        hours
        / len(df)
        * 100
    )

    threshold_rows.append({

        "threshold":
            label,

        "percentile":
            percentile,

        "demand_threshold_kWh":
            threshold,

        "hours_above_threshold":
            hours,

        "percentage_of_hours":
            percentage,

    })


threshold_df = pd.DataFrame(
    threshold_rows
)

threshold_file = os.path.join(
    OUTPUT_DIR,
    "high_demand_thresholds.csv"
)

threshold_df.to_csv(
    threshold_file,
    index=False
)

print(
    threshold_df.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)


# ============================================================
# LOAD ML TEST PREDICTIONS
# ============================================================

print("\n" + "=" * 70)
print("MODEL PEAK ANALYSIS")
print("=" * 70)

ml_predictions = pd.read_csv(
    PREDICTIONS_FILE
)

sarimax_predictions = pd.read_csv(
    SARIMAX_FILE
)


# ============================================================
# STANDARDIZE SARIMAX COLUMN NAMES
# ============================================================

sarimax_predictions["model"] = (
    "SARIMAX + Fourier"
)

if "window" in sarimax_predictions.columns:

    sarimax_predictions = (
        sarimax_predictions
        .rename(
            columns={
                "window":
                    "forecast_window"
            }
        )
    )


# ============================================================
# STANDARDIZE PREDICTION DATA
# ============================================================

prediction_columns = [
    "model",
    "forecast_window",
    "timestamp",
    "horizon",
    "actual",
    "prediction"
]

ml_predictions = (
    ml_predictions[
        prediction_columns
    ].copy()
)

sarimax_predictions = (
    sarimax_predictions[
        prediction_columns
    ].copy()
)

predictions = pd.concat(
    [
        ml_predictions,
        sarimax_predictions
    ],
    ignore_index=True
)


# IMPORTANT:
# Normalize all prediction timestamps to UTC.
predictions["timestamp"] = (
    pd.to_datetime(
        predictions["timestamp"],
        utc=True
    )
)


# ============================================================
# REMOVE DUPLICATE ACTUALS FOR THRESHOLD CALCULATION
# ============================================================

actual_test = (
    predictions[
        [
            "timestamp",
            "actual"
        ]
    ]
    .drop_duplicates(
        subset=["timestamp"]
    )
)

peak_threshold = (
    actual_test["actual"]
    .quantile(0.90)
)

print(
    f"\nTest-period P90 demand threshold: "
    f"{peak_threshold:.4f} kWh"
)


# ============================================================
# PEAK DETECTION METRICS
# ============================================================

model_peak_results = []

for model_name in sorted(
    predictions["model"].unique()
):

    model_data = predictions[
        predictions["model"]
        == model_name
    ].copy()

    actual = (
        model_data["actual"]
        .values
    )

    predicted = (
        model_data["prediction"]
        .values
    )

    actual_peak = (
        actual
        >= peak_threshold
    )

    predicted_peak = (
        predicted
        >= peak_threshold
    )

    true_positive = np.sum(
        actual_peak
        &
        predicted_peak
    )

    false_positive = np.sum(
        ~actual_peak
        &
        predicted_peak
    )

    false_negative = np.sum(
        actual_peak
        &
        ~predicted_peak
    )

    true_negative = np.sum(
        ~actual_peak
        &
        ~predicted_peak
    )

    precision = (
        true_positive
        /
        (
            true_positive
            +
            false_positive
        )
        if (
            true_positive
            +
            false_positive
        ) > 0
        else np.nan
    )

    recall = (
        true_positive
        /
        (
            true_positive
            +
            false_negative
        )
        if (
            true_positive
            +
            false_negative
        ) > 0
        else np.nan
    )

    if (
        np.isfinite(precision)
        and np.isfinite(recall)
        and (
            precision + recall
        ) > 0
    ):

        f1 = (
            2
            * precision
            * recall
            /
            (
                precision
                +
                recall
            )
        )

    else:

        f1 = np.nan

    model_peak_results.append({

        "model":
            model_name,

        "threshold_kWh":
            peak_threshold,

        "actual_peak_hours":
            int(
                actual_peak.sum()
            ),

        "predicted_peak_hours":
            int(
                predicted_peak.sum()
            ),

        "true_positive":
            int(true_positive),

        "false_positive":
            int(false_positive),

        "false_negative":
            int(false_negative),

        "true_negative":
            int(true_negative),

        "precision":
            precision,

        "recall":
            recall,

        "F1":
            f1,

    })


peak_detection_df = pd.DataFrame(
    model_peak_results
)

peak_detection_file = os.path.join(
    OUTPUT_DIR,
    "model_peak_detection.csv"
)

peak_detection_df.to_csv(
    peak_detection_file,
    index=False
)

print(
    peak_detection_df.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)


# ============================================================
# PEAK VS NON-PEAK MODEL ERROR
# ============================================================

error_rows = []

for model_name in sorted(
    predictions["model"].unique()
):

    model_data = predictions[
        predictions["model"]
        == model_name
    ].copy()

    model_data[
        "is_actual_peak"
    ] = (
        model_data["actual"]
        >= peak_threshold
    )

    for period_type, subset in (
        model_data
        .groupby("is_actual_peak")
    ):

        errors = (
            subset["actual"]
            -
            subset["prediction"]
        )

        error_rows.append({

            "model":
                model_name,

            "period":
                (
                    "Peak"
                    if period_type
                    else "Non-peak"
                ),

            "observations":
                len(subset),

            "MAE_kWh":
                np.mean(
                    np.abs(
                        errors
                    )
                ),

            "RMSE_kWh":
                np.sqrt(
                    np.mean(
                        errors ** 2
                    )
                ),

            "mean_error_kWh":
                np.mean(
                    errors
                ),

        })


peak_error_df = pd.DataFrame(
    error_rows
)

peak_error_file = os.path.join(
    OUTPUT_DIR,
    "model_peak_vs_nonpeak_error.csv"
)

peak_error_df.to_csv(
    peak_error_file,
    index=False
)


# ============================================================
# MODEL PEAK VALUES
# ============================================================

model_peak_value_rows = []

for model_name in sorted(
    predictions["model"].unique()
):

    model_data = predictions[
        predictions["model"]
        == model_name
    ].copy()

    actual_peak_value = (
        model_data["actual"]
        .max()
    )

    predicted_peak_value = (
        model_data["prediction"]
        .max()
    )

    actual_peak_timestamp = (
        model_data.loc[
            model_data["actual"].idxmax(),
            "timestamp"
        ]
    )

    predicted_peak_timestamp = (
        model_data.loc[
            model_data["prediction"].idxmax(),
            "timestamp"
        ]
    )

    model_peak_value_rows.append({

        "model":
            model_name,

        "actual_peak_kWh":
            actual_peak_value,

        "predicted_peak_kWh":
            predicted_peak_value,

        "peak_value_error_kWh":
            (
                predicted_peak_value
                -
                actual_peak_value
            ),

        "actual_peak_timestamp":
            actual_peak_timestamp,

        "predicted_peak_timestamp":
            predicted_peak_timestamp,

    })


model_peak_values = pd.DataFrame(
    model_peak_value_rows
)

model_peak_values_file = os.path.join(
    OUTPUT_DIR,
    "model_peak_values.csv"
)

model_peak_values.to_csv(
    model_peak_values_file,
    index=False
)


# ============================================================
# SAVE ALL TEST PREDICTIONS
# ============================================================

predictions_file = os.path.join(
    OUTPUT_DIR,
    "all_test_predictions_for_analysis.csv"
)

predictions.to_csv(
    predictions_file,
    index=False
)


# ============================================================
# FINAL OUTPUT LIST
# ============================================================

print("\n" + "=" * 70)
print("PEAK ANALYSIS COMPLETE")
print("=" * 70)

print("\nFiles created:")

output_files = [

    summary_file,

    top_peaks_file,

    hourly_profile_file,

    weekday_file,

    weekend_file,

    monthly_file,

    threshold_file,

    peak_detection_file,

    peak_error_file,

    model_peak_values_file,

    predictions_file,

]

for filename in output_files:

    print(
        f"  {filename}"
    )

print("\nDone.")