import os
import warnings

import numpy as np
import pandas as pd

from statsmodels.tsa.statespace.sarimax import SARIMAX

warnings.filterwarnings("ignore")


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "data/processed/model_data.csv"

RESULTS_DIR = "results"
PREDICTIONS_DIR = os.path.join(
    RESULTS_DIR,
    "predictions"
)
METRICS_DIR = os.path.join(
    RESULTS_DIR,
    "metrics"
)

os.makedirs(PREDICTIONS_DIR, exist_ok=True)
os.makedirs(METRICS_DIR, exist_ok=True)

TARGET = "demand_kWh"

# Daily and weekly seasonal periods
DAILY_PERIOD = 24
WEEKLY_PERIOD = 168

# Fourier orders
# Small values keep the model computationally practical.
DAILY_K = 3
WEEKLY_K = 3

# SARIMAX component
ORDER = (1, 0, 1)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("SARIMAX + FOURIER EV CHARGING DEMAND FORECASTING")
print("=" * 70)

print("\nLoading dataset...")

df = pd.read_csv(INPUT_FILE)

df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    utc=True
)

df = (
    df
    .sort_values("timestamp")
    .reset_index(drop=True)
)

print(f"Total observations: {len(df):,}")

print(
    f"Date range: "
    f"{df['timestamp'].min()} "
    f"to "
    f"{df['timestamp'].max()}"
)


# ============================================================
# CHRONOLOGICAL SPLIT
# ============================================================

n = len(df)

train_end = int(n * 0.70)
validation_end = int(n * 0.85)

train_df = df.iloc[:train_end].copy()
validation_df = df.iloc[
    train_end:validation_end
].copy()
test_df = df.iloc[
    validation_end:
].copy()


print("\n" + "=" * 70)
print("CHRONOLOGICAL SPLIT")
print("=" * 70)

print(f"\nTraining: {len(train_df):,}")
print(f"Validation: {len(validation_df):,}")
print(f"Test: {len(test_df):,}")


# ============================================================
# FORECAST WINDOWS
# ============================================================

def create_windows(start_index, end_index):

    windows = []

    current = start_index

    while current + 24 <= end_index:

        windows.append(
            (
                current,
                current + 24
            )
        )

        current += 24

    return windows


validation_windows = create_windows(
    train_end,
    validation_end
)

test_windows = create_windows(
    validation_end,
    len(df)
)


print("\n" + "=" * 70)
print("FORECAST WINDOWS")
print("=" * 70)

print(
    f"\nValidation windows: "
    f"{len(validation_windows)}"
)

print(
    f"Validation hours: "
    f"{len(validation_windows) * 24}"
)

print(
    f"\nTest windows: "
    f"{len(test_windows)}"
)

print(
    f"Test hours: "
    f"{len(test_windows) * 24}"
)


# ============================================================
# METRICS
# ============================================================

def mae(y_true, y_pred):

    return np.mean(
        np.abs(
            y_true - y_pred
        )
    )


def rmse(y_true, y_pred):

    return np.sqrt(
        np.mean(
            (y_true - y_pred) ** 2
        )
    )


def r2(y_true, y_pred):

    ss_res = np.sum(
        (y_true - y_pred) ** 2
    )

    ss_tot = np.sum(
        (y_true - np.mean(y_true)) ** 2
    )

    if ss_tot == 0:
        return np.nan

    return 1 - (
        ss_res / ss_tot
    )


def smape(y_true, y_pred):

    denominator = (
        np.abs(y_true)
        +
        np.abs(y_pred)
    )

    mask = denominator != 0

    if mask.sum() == 0:
        return np.nan

    return np.mean(
        2
        * np.abs(
            y_pred[mask]
            -
            y_true[mask]
        )
        /
        denominator[mask]
    ) * 100


def mase(
    y_true,
    y_pred,
    training_series,
    seasonality=168
):

    training_series = np.asarray(
        training_series,
        dtype=float
    )

    naive_errors = np.abs(
        training_series[seasonality:]
        -
        training_series[:-seasonality]
    )

    scale = np.mean(
        naive_errors
    )

    if scale == 0:
        return np.nan

    return np.mean(
        np.abs(
            y_true - y_pred
        )
    ) / scale


def calculate_metrics(
    y_true,
    y_pred,
    training_series
):

    return {

        "MAE":
            mae(
                y_true,
                y_pred
            ),

        "RMSE":
            rmse(
                y_true,
                y_pred
            ),

        "R2":
            r2(
                y_true,
                y_pred
            ),

        "sMAPE_percent":
            smape(
                y_true,
                y_pred
            ),

        "MASE":
            mase(
                y_true,
                y_pred,
                training_series
            ),
    }


# ============================================================
# FOURIER FEATURES
# ============================================================

def create_fourier_features(
    timestamps,
    daily_period=24,
    weekly_period=168,
    daily_k=3,
    weekly_k=3
):

    timestamps = pd.DatetimeIndex(
        timestamps
    )

    # Continuous hourly position.
    # This preserves the actual UTC hourly spacing.
    t = np.arange(
        len(timestamps),
        dtype=float
    )

    features = {}

    # --------------------------------------------------------
    # Daily seasonality
    # --------------------------------------------------------

    for k in range(
        1,
        daily_k + 1
    ):

        features[
            f"daily_sin_{k}"
        ] = np.sin(
            2
            * np.pi
            * k
            * t
            / daily_period
        )

        features[
            f"daily_cos_{k}"
        ] = np.cos(
            2
            * np.pi
            * k
            * t
            / daily_period
        )

    # --------------------------------------------------------
    # Weekly seasonality
    # --------------------------------------------------------

    for k in range(
        1,
        weekly_k + 1
    ):

        features[
            f"weekly_sin_{k}"
        ] = np.sin(
            2
            * np.pi
            * k
            * t
            / weekly_period
        )

        features[
            f"weekly_cos_{k}"
        ] = np.cos(
            2
            * np.pi
            * k
            * t
            / weekly_period
        )

    return pd.DataFrame(
        features,
        index=timestamps
    )


# ============================================================
# FORECAST FUNCTION
# ============================================================

def sarimax_fourier_forecast(
    history,
    steps=24
):

    history = np.asarray(
        history,
        dtype=float
    )

    history_length = len(history)

    # --------------------------------------------------------
    # Historical exogenous variables
    # --------------------------------------------------------

    historical_timestamps = pd.date_range(
        start="2000-01-01 00:00:00",
        periods=history_length,
        freq="h"
    )

    future_timestamps = pd.date_range(
        start=historical_timestamps[-1]
        + pd.Timedelta(hours=1),
        periods=steps,
        freq="h"
    )

    all_timestamps = (
        historical_timestamps
        .append(future_timestamps)
    )

    all_fourier = create_fourier_features(
        all_timestamps,
        daily_period=DAILY_PERIOD,
        weekly_period=WEEKLY_PERIOD,
        daily_k=DAILY_K,
        weekly_k=WEEKLY_K
    )

    exog_history = all_fourier.iloc[
        :history_length
    ]

    exog_future = all_fourier.iloc[
        history_length:
    ]

    # --------------------------------------------------------
    # SARIMAX
    # --------------------------------------------------------

    model = SARIMAX(
        history,
        exog=exog_history,
        order=ORDER,
        seasonal_order=(0, 0, 0, 0),
        trend="c",
        enforce_stationarity=False,
        enforce_invertibility=False
    )

    fitted_model = model.fit(
        disp=False,
        maxiter=100
    )

    forecast = fitted_model.forecast(
        steps=steps,
        exog=exog_future
    )

    forecast = np.asarray(
        forecast,
        dtype=float
    )

    # Demand cannot be negative.
    forecast = np.maximum(
        forecast,
        0
    )

    return forecast


# ============================================================
# CONFIGURATION DISPLAY
# ============================================================

print("\n" + "=" * 70)
print("SARIMAX + FOURIER CONFIGURATION")
print("=" * 70)

print(
    f"\nSARIMAX order: {ORDER}"
)

print(
    f"Daily Fourier period: "
    f"{DAILY_PERIOD}"
)

print(
    f"Daily Fourier K: "
    f"{DAILY_K}"
)

print(
    f"Weekly Fourier period: "
    f"{WEEKLY_PERIOD}"
)

print(
    f"Weekly Fourier K: "
    f"{WEEKLY_K}"
)

print(
    "\nWeekly seasonal ARIMA terms: disabled"
)

print(
    "Daily + weekly seasonality represented "
    "through Fourier terms."
)


# ============================================================
# VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("SARIMAX + FOURIER VALIDATION")
print("=" * 70)

validation_predictions = []

for window_number, (
    target_start,
    target_end
) in enumerate(
    validation_windows,
    start=1
):

    print(
        f"Validation window "
        f"{window_number}/"
        f"{len(validation_windows)}",
        end="\r"
    )

    history = df.loc[
        :target_start - 1,
        TARGET
    ].values

    actual = df.loc[
        target_start:target_end - 1,
        TARGET
    ].values

    timestamps = df.loc[
        target_start:target_end - 1,
        "timestamp"
    ].values

    forecast = sarimax_fourier_forecast(
        history,
        steps=24
    )

    for horizon, (
        timestamp,
        y_actual,
        prediction
    ) in enumerate(
        zip(
            timestamps,
            actual,
            forecast
        ),
        start=1
    ):

        validation_predictions.append({

            "model":
                "SARIMAX_Fourier",

            "window":
                window_number,

            "timestamp":
                timestamp,

            "horizon":
                horizon,

            "actual":
                y_actual,

            "prediction":
                prediction,
        })


print("\n")


validation_predictions_df = pd.DataFrame(
    validation_predictions
)

validation_metrics = calculate_metrics(
    validation_predictions_df[
        "actual"
    ].values,

    validation_predictions_df[
        "prediction"
    ].values,

    train_df[
        TARGET
    ].values
)


print(
    "Validation metrics:"
)

for key, value in validation_metrics.items():

    print(
        f"{key}: {value:.4f}"
    )


# ============================================================
# SAVE VALIDATION
# ============================================================

validation_file = os.path.join(
    PREDICTIONS_DIR,
    "sarimax_fourier_validation_predictions.csv"
)

validation_predictions_df.to_csv(
    validation_file,
    index=False
)


validation_metrics_df = pd.DataFrame(
    [{
        "Model":
            "SARIMAX_Fourier",

        **validation_metrics
    }]
)

validation_metrics_file = os.path.join(
    METRICS_DIR,
    "sarimax_fourier_validation_metrics.csv"
)

validation_metrics_df.to_csv(
    validation_metrics_file,
    index=False
)


# ============================================================
# FINAL TEST
# ============================================================

print("\n" + "=" * 70)
print("SARIMAX + FOURIER FINAL TEST EVALUATION")
print("=" * 70)

test_predictions = []

for window_number, (
    target_start,
    target_end
) in enumerate(
    test_windows,
    start=1
):

    print(
        f"Test window "
        f"{window_number}/"
        f"{len(test_windows)}",
        end="\r"
    )

    history = df.loc[
        :target_start - 1,
        TARGET
    ].values

    actual = df.loc[
        target_start:target_end - 1,
        TARGET
    ].values

    timestamps = df.loc[
        target_start:target_end - 1,
        "timestamp"
    ].values

    forecast = sarimax_fourier_forecast(
        history,
        steps=24
    )

    for horizon, (
        timestamp,
        y_actual,
        prediction
    ) in enumerate(
        zip(
            timestamps,
            actual,
            forecast
        ),
        start=1
    ):

        test_predictions.append({

            "model":
                "SARIMAX_Fourier",

            "window":
                window_number,

            "timestamp":
                timestamp,

            "horizon":
                horizon,

            "actual":
                y_actual,

            "prediction":
                prediction,
        })


print("\n")


test_predictions_df = pd.DataFrame(
    test_predictions
)


# ============================================================
# TEST METRICS
# ============================================================

test_metrics = calculate_metrics(
    test_predictions_df[
        "actual"
    ].values,

    test_predictions_df[
        "prediction"
    ].values,

    df.iloc[
        :validation_end
    ][TARGET].values
)


print(
    "\nFinal SARIMAX + Fourier test metrics:"
)

for key, value in test_metrics.items():

    print(
        f"{key}: {value:.4f}"
    )


# ============================================================
# SAVE TEST RESULTS
# ============================================================

test_prediction_file = os.path.join(
    PREDICTIONS_DIR,
    "sarimax_fourier_test_predictions.csv"
)

test_predictions_df.to_csv(
    test_prediction_file,
    index=False
)


test_metrics_df = pd.DataFrame(
    [{
        "Model":
            "SARIMAX_Fourier",

        **test_metrics
    }]
)

test_metrics_file = os.path.join(
    METRICS_DIR,
    "sarimax_fourier_test_metrics.csv"
)

test_metrics_df.to_csv(
    test_metrics_file,
    index=False
)


# ============================================================
# HORIZON METRICS
# ============================================================

horizon_results = []

for horizon in range(
    1,
    25
):

    data = test_predictions_df[
        test_predictions_df[
            "horizon"
        ] == horizon
    ]

    y_true = data[
        "actual"
    ].values

    y_pred = data[
        "prediction"
    ].values

    horizon_results.append({

        "Model":
            "SARIMAX_Fourier",

        "Horizon":
            horizon,

        "MAE":
            mae(
                y_true,
                y_pred
            ),

        "RMSE":
            rmse(
                y_true,
                y_pred
            ),
    })


sarimax_horizon_df = pd.DataFrame(
    horizon_results
)

sarimax_horizon_file = os.path.join(
    METRICS_DIR,
    "sarimax_fourier_horizon_metrics.csv"
)

sarimax_horizon_df.to_csv(
    sarimax_horizon_file,
    index=False
)


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 70)
print("SARIMAX + FOURIER PIPELINE COMPLETE")
print("=" * 70)

print(
    "\nValidation predictions:"
)

print(
    f"  {validation_file}"
)

print(
    "\nValidation metrics:"
)

print(
    f"  {validation_metrics_file}"
)

print(
    "\nTest predictions:"
)

print(
    f"  {test_prediction_file}"
)

print(
    "\nTest metrics:"
)

print(
    f"  {test_metrics_file}"
)

print(
    "\nHorizon metrics:"
)

print(
    f"  {sarimax_horizon_file}"
)

print("\nDone.")