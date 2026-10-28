import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# CONFIGURATION
# ============================================================

DEMAND_FILE = (
    "data/processed/hourly_demand.csv"
)

TEST_PREDICTIONS_FILE = (
    "results/predictions/"
    "test_predictions_corrected.csv"
)

SARIMAX_PREDICTIONS_FILE = (
    "results/predictions/"
    "sarimax_fourier_test_predictions.csv"
)

TEST_METRICS_FILE = (
    "results/metrics/"
    "test_metrics_corrected.csv"
)

SARIMAX_METRICS_FILE = (
    "results/metrics/"
    "sarimax_fourier_test_metrics.csv"
)

HORIZON_METRICS_FILE = (
    "results/metrics/"
    "horizon_metrics.csv"
)

SHAP_FILE = (
    "results/explainability/"
    "combined_shap_importance.csv"
)

ARRIVAL_METRICS_FILE = (
    "results/arrival_hour/"
    "metrics/"
    "test_metrics_arrival_hour.csv"
)

PEAK_PROFILE_FILE = (
    "results/peak_analysis/"
    "hourly_demand_profile.csv"
)

PEAK_DETECTION_FILE = (
    "results/peak_analysis/"
    "model_peak_detection.csv"
)

OUTPUT_DIR = (
    "results/figures"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def save_figure(filename):

    path = os.path.join(
        OUTPUT_DIR,
        filename
    )

    plt.savefig(
        path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    print(
        f"Created: {path}"
    )


def setup_plot(
    title,
    xlabel=None,
    ylabel=None
):

    plt.figure(
        figsize=(12, 6)
    )

    plt.title(
        title,
        fontsize=15,
        fontweight="bold"
    )

    if xlabel:
        plt.xlabel(xlabel)

    if ylabel:
        plt.ylabel(ylabel)

    plt.grid(
        alpha=0.25
    )


# ============================================================
# START
# ============================================================

print("=" * 70)
print("RESEARCH FIGURE GENERATION")
print("=" * 70)


# ============================================================
# LOAD PRIMARY DEMAND DATA
# ============================================================

print("\nLoading demand data...")

demand = pd.read_csv(
    DEMAND_FILE
)

demand["timestamp"] = pd.to_datetime(
    demand["timestamp"],
    utc=True
)

demand = (
    demand
    .sort_values("timestamp")
    .reset_index(drop=True)
)

demand["local_timestamp"] = (
    demand["timestamp"]
    .dt.tz_convert(
        "America/Los_Angeles"
    )
)

demand["hour"] = (
    demand["local_timestamp"].dt.hour
)

demand["day_of_week"] = (
    demand["local_timestamp"].dt.dayofweek
)

demand["day_name"] = (
    demand["local_timestamp"].dt.day_name()
)

demand["month"] = (
    demand["local_timestamp"].dt.month
)

demand["month_name"] = (
    demand["local_timestamp"].dt.month_name()
)

print(
    f"Demand observations: "
    f"{len(demand):,}"
)


# ============================================================
# FIGURE 1
# OVERALL HOURLY DEMAND TIME SERIES
# ============================================================

print("\nGenerating Figure 1...")

setup_plot(
    "Hourly EV Charging Demand Over the Study Period",
    "Time",
    "Charging Demand (kWh/hour)"
)

plt.plot(
    demand["timestamp"],
    demand["demand_kWh"],
    linewidth=0.8
)

plt.axhline(
    demand["demand_kWh"].mean(),
    linestyle="--",
    linewidth=1.5,
    label="Mean demand"
)

plt.legend()

save_figure(
    "01_hourly_demand_timeseries.png"
)


# ============================================================
# FIGURE 2
# HOURLY DEMAND PROFILE
# ============================================================

print("Generating Figure 2...")

hourly = (
    demand
    .groupby("hour")["demand_kWh"]
    .agg(
        mean="mean",
        median="median",
        max="max"
    )
    .reset_index()
)

setup_plot(
    "Average EV Charging Demand by Hour of Day",
    "Local Hour of Day",
    "Demand (kWh/hour)"
)

plt.plot(
    hourly["hour"],
    hourly["mean"],
    marker="o",
    label="Mean"
)

plt.plot(
    hourly["hour"],
    hourly["median"],
    marker="s",
    linestyle="--",
    label="Median"
)

plt.xticks(
    range(0, 24)
)

plt.legend()

save_figure(
    "02_hourly_demand_profile.png"
)


# ============================================================
# FIGURE 3
# WEEKDAY VS WEEKEND
# ============================================================

print("Generating Figure 3...")

demand["period"] = np.where(
    demand["day_of_week"] >= 5,
    "Weekend",
    "Weekday"
)

weekday_hourly = (
    demand
    .groupby(
        [
            "period",
            "hour"
        ]
    )["demand_kWh"]
    .mean()
    .reset_index()
)

setup_plot(
    "Weekday vs Weekend Hourly Charging Demand",
    "Local Hour of Day",
    "Mean Demand (kWh/hour)"
)

for period in [
    "Weekday",
    "Weekend"
]:

    subset = weekday_hourly[
        weekday_hourly["period"]
        == period
    ]

    plt.plot(
        subset["hour"],
        subset["demand_kWh"],
        marker="o",
        label=period
    )

plt.xticks(
    range(0, 24)
)

plt.legend()

save_figure(
    "03_weekday_vs_weekend.png"
)


# ============================================================
# FIGURE 4
# MONTHLY DEMAND
# ============================================================

print("Generating Figure 4...")

monthly = (
    demand
    .groupby(
        [
            "month",
            "month_name"
        ]
    )["demand_kWh"]
    .agg(
        mean="mean",
        max="max"
    )
    .reset_index()
    .sort_values("month")
)

setup_plot(
    "Monthly EV Charging Demand",
    "Month",
    "Demand (kWh/hour)"
)

plt.plot(
    monthly["month_name"],
    monthly["mean"],
    marker="o",
    label="Mean demand"
)

plt.plot(
    monthly["month_name"],
    monthly["max"],
    marker="s",
    linestyle="--",
    label="Maximum demand"
)

plt.xticks(
    rotation=45
)

plt.legend()

save_figure(
    "04_monthly_demand.png"
)


# ============================================================
# LOAD ML PREDICTIONS
# ============================================================

print("\nLoading prediction results...")

ml_predictions = pd.read_csv(
    TEST_PREDICTIONS_FILE
)

ml_predictions["timestamp"] = pd.to_datetime(
    ml_predictions["timestamp"],
    utc=True
)


# ============================================================
# LOAD SARIMAX PREDICTIONS
# ============================================================

sarimax = pd.read_csv(
    SARIMAX_PREDICTIONS_FILE
)

if "window" in sarimax.columns:

    sarimax = sarimax.rename(
        columns={
            "window":
                "forecast_window"
        }
    )

sarimax["model"] = (
    "SARIMAX + Fourier"
)

sarimax["timestamp"] = pd.to_datetime(
    sarimax["timestamp"],
    utc=True
)


# ============================================================
# COMBINE PREDICTIONS
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
    ]
    .copy()
)

sarimax = (
    sarimax[
        prediction_columns
    ]
    .copy()
)

predictions = pd.concat(
    [
        ml_predictions,
        sarimax
    ],
    ignore_index=True
)


# ============================================================
# FIGURE 5
# ACTUAL VS PREDICTED 24-HOUR FORECAST
# ============================================================

print("Generating Figure 5...")

first_window = (
    predictions[
        "forecast_window"
    ]
    .min()
)

window_data = predictions[
    predictions["forecast_window"]
    == first_window
].copy()

actual_window = (
    window_data[
        [
            "timestamp",
            "actual"
        ]
    ]
    .drop_duplicates(
        subset=["timestamp"]
    )
    .sort_values("timestamp")
)

setup_plot(
    "24-Hour Actual vs Forecasted Charging Demand",
    "Forecast Horizon (hours)",
    "Demand (kWh/hour)"
)

plt.plot(
    range(
        1,
        len(actual_window) + 1
    ),
    actual_window["actual"],
    marker="o",
    linewidth=2,
    label="Actual"
)

for model in sorted(
    predictions["model"].unique()
):

    subset = (
        window_data[
            window_data["model"]
            == model
        ]
        .sort_values("horizon")
    )

    plt.plot(
        subset["horizon"],
        subset["prediction"],
        marker=".",
        linewidth=1.3,
        label=model
    )

plt.xticks(
    range(1, 25)
)

plt.legend()

save_figure(
    "05_actual_vs_predicted_24h.png"
)


# ============================================================
# FIGURE 6
# MODEL METRIC COMPARISON
# ============================================================

print("Generating Figure 6...")

metrics = pd.read_csv(
    TEST_METRICS_FILE
)

if os.path.exists(
    SARIMAX_METRICS_FILE
):

    sarimax_metrics = pd.read_csv(
        SARIMAX_METRICS_FILE
    )

    metrics = pd.concat(
        [
            metrics,
            sarimax_metrics
        ],
        ignore_index=True
    )

metrics = metrics.sort_values(
    "Model"
)

fig, axes = plt.subplots(
    1,
    2,
    figsize=(14, 6)
)

axes[0].bar(
    metrics["Model"],
    metrics["MAE"]
)

axes[0].set_title(
    "MAE"
)

axes[0].set_ylabel(
    "MAE (kWh)"
)

axes[0].tick_params(
    axis="x",
    rotation=45
)

axes[1].bar(
    metrics["Model"],
    metrics["RMSE"]
)

axes[1].set_title(
    "RMSE"
)

axes[1].set_ylabel(
    "RMSE (kWh)"
)

axes[1].tick_params(
    axis="x",
    rotation=45
)

fig.suptitle(
    "Test-Period Forecast Error Comparison",
    fontsize=15,
    fontweight="bold"
)

fig.tight_layout()

fig.savefig(
    os.path.join(
        OUTPUT_DIR,
        "06_model_metric_comparison.png"
    ),
    dpi=300,
    bbox_inches="tight"
)

plt.close(fig)

print(
    "Created: "
    "results/figures/"
    "06_model_metric_comparison.png"
)


# ============================================================
# FIGURE 7
# FORECAST HORIZON ERROR
# ============================================================

print("Generating Figure 7...")

horizon = pd.read_csv(
    HORIZON_METRICS_FILE
)

setup_plot(
    "Forecast Error Across the 24-Hour Horizon",
    "Forecast Horizon (hours ahead)",
    "RMSE (kWh)"
)

for model in sorted(
    horizon["Model"].unique()
):

    subset = horizon[
        horizon["Model"]
        == model
    ]

    plt.plot(
        subset["Horizon"],
        subset["RMSE"],
        marker="o",
        linewidth=1.5,
        label=model
    )

plt.xticks(
    range(1, 25)
)

plt.legend()

save_figure(
    "07_horizon_rmse.png"
)


# ============================================================
# FIGURE 8
# SHAP FEATURE IMPORTANCE
# ============================================================

print("Generating Figure 8...")

if os.path.exists(
    SHAP_FILE
):

    shap = pd.read_csv(
        SHAP_FILE
    )

    # Detect feature column.

    if "Feature" in shap.columns:

        feature_col = "Feature"

    elif "feature" in shap.columns:

        feature_col = "feature"

    else:

        feature_col = shap.columns[0]


    # Detect SHAP importance column.

    possible_importance_columns = [

        "Average_Mean_Abs_SHAP",

        "average_mean_abs_shap",

        "mean_abs_shap",

        "Mean_Abs_SHAP",

    ]

    importance_col = None

    for column in (
        possible_importance_columns
    ):

        if column in shap.columns:

            importance_col = column
            break


    if importance_col is None:

        numeric_columns = (
            shap
            .select_dtypes(
                include=np.number
            )
            .columns
        )

        importance_col = (
            numeric_columns[-1]
        )


    shap_plot = (
        shap[
            [
                feature_col,
                importance_col
            ]
        ]
        .dropna()
        .sort_values(
            importance_col,
            ascending=True
        )
        .tail(12)
    )

    plt.figure(
        figsize=(10, 7)
    )

    plt.barh(
        shap_plot[feature_col],
        shap_plot[importance_col]
    )

    plt.title(
        "Feature Contribution Based on Mean Absolute SHAP Value",
        fontsize=15,
        fontweight="bold"
    )

    plt.xlabel(
        "Mean Absolute SHAP Value"
    )

    plt.tight_layout()

    save_figure(
        "08_shap_feature_importance.png"
    )

else:

    print(
        "SHAP file not found; "
        "Figure 8 skipped."
    )


# ============================================================
# FIGURE 9
# PEAK DEMAND PROFILE
# ============================================================

print("Generating Figure 9...")

if os.path.exists(
    PEAK_PROFILE_FILE
):

    peak_profile = pd.read_csv(
        PEAK_PROFILE_FILE
    )

    setup_plot(
        "Mean and Maximum Charging Demand by Hour",
        "Local Hour of Day",
        "Demand (kWh/hour)"
    )

    plt.plot(
        peak_profile["hour"],
        peak_profile[
            "mean_demand_kWh"
        ],
        marker="o",
        label="Mean"
    )

    plt.plot(
        peak_profile["hour"],
        peak_profile[
            "max_demand_kWh"
        ],
        marker="s",
        linestyle="--",
        label="Maximum"
    )

    plt.xticks(
        range(0, 24)
    )

    plt.legend()

    save_figure(
        "09_peak_demand_profile.png"
    )

else:

    print(
        "Peak profile file not found; "
        "Figure 9 skipped."
    )


# ============================================================
# FIGURE 10
# PEAK DETECTION
# ============================================================

print("Generating Figure 10...")

if os.path.exists(
    PEAK_DETECTION_FILE
):

    peak_detection = pd.read_csv(
        PEAK_DETECTION_FILE
    )

    peak_detection = (
        peak_detection
        .sort_values("model")
    )

    setup_plot(
        "High-Demand Peak Detection",
        "Model",
        "Number of Hours"
    )

    x = np.arange(
        len(peak_detection)
    )

    width = 0.35

    plt.bar(
        x - width / 2,
        peak_detection[
            "actual_peak_hours"
        ],
        width,
        label="Actual peak hours"
    )

    plt.bar(
        x + width / 2,
        peak_detection[
            "predicted_peak_hours"
        ],
        width,
        label="Predicted peak hours"
    )

    plt.xticks(
        x,
        peak_detection["model"],
        rotation=45
    )

    plt.legend()

    save_figure(
        "10_peak_detection.png"
    )

else:

    print(
        "Peak detection file not found; "
        "Figure 10 skipped."
    )


# ============================================================
# FIGURE 11
# ROBUSTNESS COMPARISON
# ============================================================

print("Generating Figure 11...")

if (
    os.path.exists(
        ARRIVAL_METRICS_FILE
    )
    and
    os.path.exists(
        TEST_METRICS_FILE
    )
):

    primary_metrics = pd.read_csv(
        TEST_METRICS_FILE
    )

    arrival_metrics = pd.read_csv(
        ARRIVAL_METRICS_FILE
    )

    primary_metrics[
        "Target"
    ] = (
        "Interval allocation"
    )

    arrival_metrics[
        "Target"
    ] = (
        "Arrival-hour"
    )

    robustness = pd.concat(
        [
            primary_metrics,
            arrival_metrics
        ],
        ignore_index=True
    )

    models = sorted(
        robustness[
            "Model"
        ].unique()
    )

    x = np.arange(
        len(models)
    )

    width = 0.35

    primary = []
    arrival = []

    for model in models:

        primary_row = robustness[
            (
                robustness["Model"]
                == model
            )
            &
            (
                robustness["Target"]
                == "Interval allocation"
            )
        ]

        arrival_row = robustness[
            (
                robustness["Model"]
                == model
            )
            &
            (
                robustness["Target"]
                == "Arrival-hour"
            )
        ]

        if len(primary_row):

            primary.append(
                primary_row[
                    "RMSE"
                ].iloc[0]
            )

        else:

            primary.append(
                np.nan
            )

        if len(arrival_row):

            arrival.append(
                arrival_row[
                    "RMSE"
                ].iloc[0]
            )

        else:

            arrival.append(
                np.nan
            )


    plt.figure(
        figsize=(12, 6)
    )

    plt.bar(
        x - width / 2,
        primary,
        width,
        label="Interval allocation"
    )

    plt.bar(
        x + width / 2,
        arrival,
        width,
        label="Arrival-hour"
    )

    plt.xticks(
        x,
        models,
        rotation=45
    )

    plt.ylabel(
        "RMSE (kWh)"
    )

    plt.title(
        "Robustness Comparison Across Demand Reconstruction Methods",
        fontsize=15,
        fontweight="bold"
    )

    plt.legend()

    plt.tight_layout()

    save_figure(
        "11_robustness_rmse.png"
    )

else:

    print(
        "Arrival-hour metrics not found; "
        "Figure 11 skipped."
    )


# ============================================================
# FIGURE 12
# ACTUAL VS PREDICTED TEST PERIOD
# ============================================================

print("Generating Figure 12...")

actual_series = (
    predictions[
        [
            "timestamp",
            "actual"
        ]
    ]
    .drop_duplicates(
        subset=["timestamp"]
    )
    .sort_values("timestamp")
)

plt.figure(
    figsize=(14, 7)
)

plt.plot(
    actual_series["timestamp"],
    actual_series["actual"],
    linewidth=1.5,
    label="Actual"
)

for model in sorted(
    predictions["model"].unique()
):

    model_series = (
        predictions[
            predictions["model"]
            == model
        ]
        .groupby("timestamp")[
            "prediction"
        ]
        .mean()
        .reset_index()
        .sort_values("timestamp")
    )

    plt.plot(
        model_series["timestamp"],
        model_series["prediction"],
        linewidth=1,
        alpha=0.8,
        label=model
    )

plt.title(
    "Actual and Predicted Charging Demand During the Test Period",
    fontsize=15,
    fontweight="bold"
)

plt.xlabel(
    "Time"
)

plt.ylabel(
    "Demand (kWh/hour)"
)

plt.legend()

plt.grid(
    alpha=0.25
)

plt.tight_layout()

save_figure(
    "12_test_period_actual_vs_predicted.png"
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("FIGURE GENERATION COMPLETE")
print("=" * 70)

print(
    "\nFigures are available in:"
)

print(
    f"  {OUTPUT_DIR}"
)

print("\nGenerated files:")

for filename in sorted(
    os.listdir(OUTPUT_DIR)
):

    print(
        f"  {filename}"
    )

print("\nDone.")