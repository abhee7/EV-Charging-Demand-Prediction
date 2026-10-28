import os
import warnings

import numpy as np
import pandas as pd
from scipy.stats import norm

warnings.filterwarnings("ignore")


# ============================================================
# CONFIGURATION
# ============================================================

PREDICTIONS_FILE = (
    "results/predictions/test_predictions_corrected.csv"
)

SARIMAX_FILE = (
    "results/predictions/"
    "sarimax_fourier_test_predictions.csv"
)

OUTPUT_DIR = "results/metrics"

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "diebold_mariano_tests.csv"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# SETTINGS
# ============================================================

# Squared-error loss.
# This is appropriate when comparing RMSE-oriented forecast
# accuracy.

LOSS_FUNCTION = "squared_error"

# Newey-West / HAC lag.
#
# Forecasts are generated in non-overlapping 24-hour windows.
# A lag of 23 captures dependence within a 24-hour forecast
# block while avoiding unnecessary long-range dependence.

HAC_LAG = 23


# ============================================================
# LOAD ML PREDICTIONS
# ============================================================

print("=" * 70)
print("DIEBOLD-MARIANO FORECAST ACCURACY TESTS")
print("=" * 70)

print("\nLoading ML predictions...")

ml_df = pd.read_csv(
    PREDICTIONS_FILE
)

print(
    f"ML prediction rows: "
    f"{len(ml_df):,}"
)

print(
    "Models found:"
)

for model in sorted(
    ml_df["model"].unique()
):

    print(
        f"  - {model}"
    )


# ============================================================
# LOAD SARIMAX PREDICTIONS
# ============================================================

print("\nLoading SARIMAX + Fourier predictions...")

sarimax_df = pd.read_csv(
    SARIMAX_FILE
)

sarimax_df["model"] = (
    "SARIMAX + Fourier"
)

print(
    f"SARIMAX prediction rows: "
    f"{len(sarimax_df):,}"
)


# ============================================================
# STANDARDIZE COLUMNS
# ============================================================

# The ML prediction file already contains:
#
# model
# forecast_window
# origin
# timestamp
# horizon
# actual
# prediction

# The SARIMAX file contains:
#
# model
# window
# timestamp
# horizon
# actual
# prediction

# Rename SARIMAX window field so that both datasets
# use the same forecast-window identifier.

if "window" in sarimax_df.columns:

    sarimax_df = sarimax_df.rename(
        columns={
            "window":
                "forecast_window"
        }
    )


# ============================================================
# COMBINE PREDICTIONS
# ============================================================

required_columns = [
    "model",
    "forecast_window",
    "timestamp",
    "horizon",
    "actual",
    "prediction"
]

ml_df = ml_df[
    required_columns
].copy()

sarimax_df = sarimax_df[
    [
        "model",
        "forecast_window",
        "timestamp",
        "horizon",
        "actual",
        "prediction"
    ]
].copy()

all_predictions = pd.concat(
    [
        ml_df,
        sarimax_df
    ],
    ignore_index=True
)


# ============================================================
# NORMALIZE TYPES
# ============================================================

all_predictions[
    "timestamp"
] = pd.to_datetime(
    all_predictions["timestamp"],
    utc=True
)

all_predictions[
    "forecast_window"
] = (
    all_predictions[
        "forecast_window"
    ]
    .astype(int)
)

all_predictions[
    "horizon"
] = (
    all_predictions[
        "horizon"
    ]
    .astype(int)
)


# ============================================================
# VALIDATE DATA
# ============================================================

print("\n" + "=" * 70)
print("PREDICTION DATA VALIDATION")
print("=" * 70)

print(
    f"\nTotal rows: "
    f"{len(all_predictions):,}"
)

print(
    f"Models: "
    f"{all_predictions['model'].nunique()}"
)

for model in sorted(
    all_predictions["model"].unique()
):

    count = (
        all_predictions[
            all_predictions["model"] == model
        ]
        .shape[0]
    )

    print(
        f"  {model}: {count:,} rows"
    )


# ============================================================
# DIEBOLD-MARIANO IMPLEMENTATION
# ============================================================

def newey_west_variance(
    loss_differential,
    lag
):

    d = np.asarray(
        loss_differential,
        dtype=float
    )

    n = len(d)

    if n < 2:

        return np.nan

    d_centered = (
        d - np.mean(d)
    )

    gamma_0 = (
        np.sum(
            d_centered ** 2
        )
        / n
    )

    variance = gamma_0

    max_lag = min(
        lag,
        n - 1
    )

    for j in range(
        1,
        max_lag + 1
    ):

        gamma_j = (
            np.sum(
                d_centered[j:]
                *
                d_centered[:-j]
            )
            / n
        )

        # Bartlett / Newey-West weight
        weight = (
            1
            -
            j / (max_lag + 1)
        )

        variance += (
            2
            * weight
            * gamma_j
        )

    return variance


def diebold_mariano_test(
    actual,
    prediction_1,
    prediction_2,
    hac_lag=23
):

    actual = np.asarray(
        actual,
        dtype=float
    )

    prediction_1 = np.asarray(
        prediction_1,
        dtype=float
    )

    prediction_2 = np.asarray(
        prediction_2,
        dtype=float
    )

    error_1 = (
        actual
        -
        prediction_1
    )

    error_2 = (
        actual
        -
        prediction_2
    )

    # Squared-error loss
    loss_1 = (
        error_1 ** 2
    )

    loss_2 = (
        error_2 ** 2
    )

    # Positive differential means
    # model 1 has larger loss.
    differential = (
        loss_1
        -
        loss_2
    )

    n = len(
        differential
    )

    mean_differential = np.mean(
        differential
    )

    hac_variance = (
        newey_west_variance(
            differential,
            hac_lag
        )
    )

    if (
        not np.isfinite(
            hac_variance
        )
        or hac_variance <= 0
    ):

        return {
            "DM_statistic":
                np.nan,

            "p_value":
                np.nan,

            "mean_loss_difference":
                mean_differential,

            "n":
                n,

            "significant_5pct":
                False
        }

    # Variance of sample mean
    standard_error = np.sqrt(
        hac_variance / n
    )

    dm_statistic = (
        mean_differential
        /
        standard_error
    )

    # Two-sided normal approximation
    p_value = (
        2
        *
        (
            1
            -
            norm.cdf(
                abs(
                    dm_statistic
                )
            )
        )
    )

    return {

        "DM_statistic":
            dm_statistic,

        "p_value":
            p_value,

        "mean_loss_difference":
            mean_differential,

        "n":
            n,

        "significant_5pct":
            p_value < 0.05
    }


# ============================================================
# MODEL PAIRS
# ============================================================

models = sorted(
    all_predictions[
        "model"
    ].unique()
)

print("\n" + "=" * 70)
print("MODEL PAIRS")
print("=" * 70)

for i in range(
    len(models)
):

    for j in range(
        i + 1,
        len(models)
    ):

        print(
            f"{models[i]} "
            f"vs "
            f"{models[j]}"
        )


# ============================================================
# CREATE COMMON FORECAST PANEL
# ============================================================

print("\n" + "=" * 70)
print("BUILDING PAIRED FORECAST PANEL")
print("=" * 70)

panel = all_predictions[
    [
        "model",
        "forecast_window",
        "timestamp",
        "horizon",
        "actual",
        "prediction"
    ]
].copy()

# Pivot predictions so every timestamp/horizon has one
# prediction column per model.

prediction_panel = (
    panel
    .pivot_table(
        index=[
            "forecast_window",
            "timestamp",
            "horizon",
            "actual"
        ],
        columns="model",
        values="prediction",
        aggfunc="first"
    )
    .reset_index()
)

print(
    f"\nPaired observations: "
    f"{len(prediction_panel):,}"
)


# ============================================================
# RUN DM TESTS
# ============================================================

results = []

for i in range(
    len(models)
):

    for j in range(
        i + 1,
        len(models)
    ):

        model_1 = models[i]
        model_2 = models[j]

        if (
            model_1
            not in prediction_panel.columns
        ):
            continue

        if (
            model_2
            not in prediction_panel.columns
        ):
            continue

        pair = prediction_panel[
            [
                "actual",
                model_1,
                model_2
            ]
        ].dropna()

        if len(pair) == 0:
            continue

        result = diebold_mariano_test(
            actual=pair[
                "actual"
            ].values,

            prediction_1=pair[
                model_1
            ].values,

            prediction_2=pair[
                model_2
            ].values,

            hac_lag=HAC_LAG
        )

        results.append({

            "Model_1":
                model_1,

            "Model_2":
                model_2,

            "Observations":
                result["n"],

            "DM_statistic":
                result[
                    "DM_statistic"
                ],

            "p_value":
                result[
                    "p_value"
                ],

            "mean_squared_error_difference":
                result[
                    "mean_loss_difference"
                ],

            "HAC_lag":
                HAC_LAG,

            "significant_5pct":
                result[
                    "significant_5pct"
                ],
        })


# ============================================================
# SAVE RESULTS
# ============================================================

dm_results_df = pd.DataFrame(
    results
)

dm_results_df = (
    dm_results_df
    .sort_values(
        [
            "p_value",
            "Model_1",
            "Model_2"
        ]
    )
    .reset_index(drop=True)
)

dm_results_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# DISPLAY
# ============================================================

print("\n" + "=" * 70)
print("DIEBOLD-MARIANO RESULTS")
print("=" * 70)

print()

for _, row in (
    dm_results_df.iterrows()
):

    print(
        f"{row['Model_1']} "
        f"vs "
        f"{row['Model_2']}"
    )

    print(
        f"  Observations: "
        f"{int(row['Observations']):,}"
    )

    print(
        f"  DM statistic: "
        f"{row['DM_statistic']:.4f}"
    )

    print(
        f"  p-value: "
        f"{row['p_value']:.6f}"
    )

    print(
        f"  Mean squared-error "
        f"difference: "
        f"{row['mean_squared_error_difference']:.4f}"
    )

    print(
        f"  Significant at 5%: "
        f"{row['significant_5pct']}"
    )

    print()


# ============================================================
# COMPLETE
# ============================================================

print("=" * 70)
print("DIEBOLD-MARIANO TEST COMPLETE")
print("=" * 70)

print(
    f"\nSaved to:"
)

print(
    f"  {OUTPUT_FILE}"
)

print("\nDone.")