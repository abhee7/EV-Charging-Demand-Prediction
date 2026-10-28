import os
import warnings

import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

warnings.filterwarnings("ignore")


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "data/processed/model_data_arrival_hour.csv"

RESULTS_DIR = "results/arrival_hour"
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

LOCAL_TZ = "America/Los_Angeles"

TARGET = "demand_kWh"

FEATURES = [
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
    "hour",
    "day_of_week",
    "day_of_month",
    "month",
    "week_of_year",
    "is_weekend",
    "is_business_hour",
]


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("ARRIVAL-HOUR ROBUSTNESS EXPERIMENT")
print("=" * 70)

print("\nLoading model dataset...")

df = pd.read_csv(INPUT_FILE)

df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    utc=True
)

df = (
    df.sort_values("timestamp")
    .reset_index(drop=True)
)

print(f"Total observations: {len(df):,}")

print(
    f"Date range: "
    f"{df['timestamp'].min()} "
    f"to {df['timestamp'].max()}"
)


# ============================================================
# CHRONOLOGICAL 70 / 15 / 15 SPLIT
# ============================================================

n = len(df)

train_end = int(n * 0.70)
validation_end = int(n * 0.85)

train_df = df.iloc[
    :train_end
].copy()

validation_df = df.iloc[
    train_end:validation_end
].copy()

test_df = df.iloc[
    validation_end:
].copy()

print("\n" + "=" * 70)
print("CHRONOLOGICAL SPLIT")
print("=" * 70)

print(
    f"\nTraining:   {len(train_df):,}"
)

print(
    f"  {train_df['timestamp'].min()} "
    f"to {train_df['timestamp'].max()}"
)

print(
    f"\nValidation: {len(validation_df):,}"
)

print(
    f"  {validation_df['timestamp'].min()} "
    f"to {validation_df['timestamp'].max()}"
)

print(
    f"\nTest:       {len(test_df):,}"
)

print(
    f"  {test_df['timestamp'].min()} "
    f"to {test_df['timestamp'].max()}"
)


# ============================================================
# METRICS
# ============================================================

def calculate_mae(
    y_true,
    y_pred
):

    return np.mean(
        np.abs(
            y_true - y_pred
        )
    )


def calculate_rmse(
    y_true,
    y_pred
):

    return np.sqrt(
        np.mean(
            (y_true - y_pred) ** 2
        )
    )


def calculate_r2(
    y_true,
    y_pred
):

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


def calculate_smape(
    y_true,
    y_pred
):

    denominator = (
        np.abs(y_true)
        + np.abs(y_pred)
    )

    mask = denominator != 0

    if mask.sum() == 0:
        return np.nan

    return np.mean(
        2
        * np.abs(
            y_pred[mask]
            - y_true[mask]
        )
        / denominator[mask]
    ) * 100


def calculate_mase(
    y_true,
    y_pred,
    training_series,
    seasonality=168
):

    training_series = np.asarray(
        training_series,
        dtype=float
    )

    if len(training_series) <= seasonality:
        return np.nan

    naive_errors = np.abs(
        training_series[seasonality:]
        - training_series[:-seasonality]
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
        "MAE": calculate_mae(
            y_true,
            y_pred
        ),

        "RMSE": calculate_rmse(
            y_true,
            y_pred
        ),

        "R2": calculate_r2(
            y_true,
            y_pred
        ),

        "sMAPE_percent":
            calculate_smape(
                y_true,
                y_pred
            ),

        "MASE":
            calculate_mase(
                y_true,
                y_pred,
                training_series
            ),
    }


# ============================================================
# FEATURE GENERATION
# ============================================================

def make_features(
    history,
    timestamp
):

    history = np.asarray(
        history,
        dtype=float
    )

    ts = pd.Timestamp(
        timestamp
    )

    if ts.tzinfo is None:

        ts = ts.tz_localize(
            "UTC"
        )

    local_timestamp = (
        ts.tz_convert(
            LOCAL_TZ
        )
    )

    features = {

        "lag_1":
            history[-1],

        "lag_2":
            history[-2],

        "lag_24":
            history[-24],

        "lag_48":
            history[-48],

        "lag_168":
            history[-168],

        "lag_336":
            history[-336],

        "rolling_mean_24":
            np.mean(
                history[-24:]
            ),

        "rolling_std_24":
            np.std(
                history[-24:],
                ddof=1
            ),

        "rolling_mean_168":
            np.mean(
                history[-168:]
            ),

        "rolling_std_168":
            np.std(
                history[-168:],
                ddof=1
            ),

        "hour":
            local_timestamp.hour,

        "day_of_week":
            local_timestamp.dayofweek,

        "day_of_month":
            local_timestamp.day,

        "month":
            local_timestamp.month,

        "week_of_year":
            int(
                local_timestamp
                .isocalendar()
                .week
            ),

        "is_weekend":
            int(
                local_timestamp.dayofweek >= 5
            ),

        "is_business_hour":
            int(
                8 <= local_timestamp.hour < 18
            ),
    }

    return pd.DataFrame(
        [[
            features[col]
            for col in FEATURES
        ]],
        columns=FEATURES
    )


# ============================================================
# RECURSIVE FORECAST
# ============================================================

def recursive_forecast(
    model,
    history_values,
    start_timestamp
):

    history = list(
        np.asarray(
            history_values,
            dtype=float
        )
    )

    predictions = []

    timestamp = pd.Timestamp(
        start_timestamp
    )

    for step in range(24):

        X_future = make_features(
            history,
            timestamp
        )

        prediction = float(
            model.predict(
                X_future
            )[0]
        )

        prediction = max(
            0.0,
            prediction
        )

        predictions.append(
            prediction
        )

        history.append(
            prediction
        )

        timestamp = (
            timestamp
            + pd.Timedelta(
                hours=1
            )
        )

    return np.array(
        predictions
    )


# ============================================================
# SEASONAL NAIVE
# ============================================================

def seasonal_naive_forecast(
    history_values
):

    history = np.asarray(
        history_values,
        dtype=float
    )

    return history[-168:-144]


# ============================================================
# FORECAST WINDOWS
# ============================================================

def create_forecast_windows(
    start_index,
    end_index
):

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


validation_windows = (
    create_forecast_windows(
        train_end,
        validation_end
    )
)

test_windows = (
    create_forecast_windows(
        validation_end,
        len(df)
    )
)

print("\n" + "=" * 70)
print("FORECAST WINDOWS")
print("=" * 70)

print(
    f"\nValidation windows: "
    f"{len(validation_windows)}"
)

print(
    f"Validation hours evaluated: "
    f"{len(validation_windows) * 24}"
)

print(
    f"\nTest windows: "
    f"{len(test_windows)}"
)

print(
    f"Test hours evaluated: "
    f"{len(test_windows) * 24}"
)

print(
    f"Test hours not included: "
    f"{len(test_df) - len(test_windows) * 24}"
)


# ============================================================
# TRAINING DATA
# ============================================================

train_model = (
    train_df
    .dropna(
        subset=FEATURES
    )
    .copy()
)

X_train = train_model[
    FEATURES
]

y_train = train_model[
    TARGET
]

print(
    "\nTraining rows with "
    "complete features:"
)

print(
    f"{len(train_model):,}"
)


# ============================================================
# MODEL CANDIDATES
# ============================================================

model_candidates = {

    "Linear Regression": [

        LinearRegression()

    ],

    "Random Forest": [

        RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        ),

        RandomForestRegressor(
            n_estimators=300,
            max_depth=20,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        ),

        RandomForestRegressor(
            n_estimators=300,
            max_depth=None,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        ),

    ],

    "XGBoost": [

        XGBRegressor(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="reg:squarederror",
            random_state=42,
            n_jobs=-1
        ),

        XGBRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="reg:squarederror",
            random_state=42,
            n_jobs=-1
        ),

        XGBRegressor(
            n_estimators=400,
            max_depth=4,
            learning_rate=0.03,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="reg:squarederror",
            random_state=42,
            n_jobs=-1
        ),

    ],
}


# ============================================================
# EVALUATE MODEL ON WINDOWS
# ============================================================

def evaluate_model_on_windows(
    model,
    windows
):

    predictions = []

    for window_number, (
        target_start,
        target_end
    ) in enumerate(
        windows,
        start=1
    ):

        history = df.loc[
            :target_start - 1,
            TARGET
        ].values

        target_timestamps = df.loc[
            target_start:target_end - 1,
            "timestamp"
        ].values

        actual = df.loc[
            target_start:target_end - 1,
            TARGET
        ].values

        forecast = recursive_forecast(
            model,
            history,
            pd.Timestamp(
                target_timestamps[0]
            )
        )

        for horizon, (
            timestamp,
            y_actual,
            y_prediction
        ) in enumerate(
            zip(
                target_timestamps,
                actual,
                forecast
            ),
            start=1
        ):

            predictions.append({

                "window":
                    window_number,

                "timestamp":
                    timestamp,

                "horizon":
                    horizon,

                "actual":
                    y_actual,

                "prediction":
                    y_prediction,
            })

    return pd.DataFrame(
        predictions
    )


# ============================================================
# VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("VALIDATION PHASE")
print("=" * 70)

validation_results = []

selected_models = {}


for model_name, candidates in (
    model_candidates.items()
):

    print(
        f"\nEvaluating {model_name} "
        f"candidate(s)..."
    )

    best_rmse = np.inf
    best_model = None
    best_candidate_number = None

    for candidate_number, model in enumerate(
        candidates,
        start=1
    ):

        print(
            f"  Candidate "
            f"{candidate_number}/"
            f"{len(candidates)}..."
        )

        model.fit(
            X_train,
            y_train
        )

        validation_predictions = (
            evaluate_model_on_windows(
                model,
                validation_windows
            )
        )

        y_true = (
            validation_predictions[
                "actual"
            ].values
        )

        y_pred = (
            validation_predictions[
                "prediction"
            ].values
        )

        metrics = calculate_metrics(
            y_true,
            y_pred,
            y_train.values
        )

        validation_results.append({

            "Model":
                model_name,

            "Candidate":
                candidate_number,

            **metrics,

        })

        print(
            f"    Validation RMSE: "
            f"{metrics['RMSE']:.4f}"
        )

        if metrics["RMSE"] < best_rmse:

            best_rmse = (
                metrics["RMSE"]
            )

            best_model = model

            best_candidate_number = (
                candidate_number
            )

    selected_models[
        model_name
    ] = best_model

    print(
        f"  Selected candidate: "
        f"{best_candidate_number}"
    )


# ============================================================
# SEASONAL NAIVE VALIDATION
# ============================================================

print(
    "\nEvaluating Seasonal Naive "
    "on validation..."
)

validation_naive_actual = []
validation_naive_pred = []

for target_start, target_end in (
    validation_windows
):

    history = df.loc[
        :target_start - 1,
        TARGET
    ].values

    actual = df.loc[
        target_start:target_end - 1,
        TARGET
    ].values

    prediction = seasonal_naive_forecast(
        history
    )

    validation_naive_actual.extend(
        actual
    )

    validation_naive_pred.extend(
        prediction
    )


validation_naive_actual = np.asarray(
    validation_naive_actual
)

validation_naive_pred = np.asarray(
    validation_naive_pred
)

naive_validation_metrics = (
    calculate_metrics(
        validation_naive_actual,
        validation_naive_pred,
        train_model[TARGET].values
    )
)

validation_results.append({

    "Model":
        "Seasonal Naive",

    "Candidate":
        1,

    **naive_validation_metrics,

})


validation_metrics_df = (
    pd.DataFrame(
        validation_results
    )
)

validation_metrics_file = os.path.join(
    METRICS_DIR,
    "validation_metrics_arrival_hour.csv"
)

validation_metrics_df.to_csv(
    validation_metrics_file,
    index=False
)

print("\n" + "=" * 70)
print("VALIDATION RESULTS")
print("=" * 70)

print(
    validation_metrics_df[
        [
            "Model",
            "Candidate",
            "MAE",
            "RMSE",
            "R2",
            "sMAPE_percent",
            "MASE",
        ]
    ].to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)


# ============================================================
# REFIT ON TRAIN + VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("FINAL MODEL FITTING")
print("=" * 70)

train_validation_df = (
    df.iloc[
        :validation_end
    ].copy()
)

train_validation_model = (
    train_validation_df
    .dropna(
        subset=FEATURES
    )
    .copy()
)

X_train_validation = (
    train_validation_model[
        FEATURES
    ]
)

y_train_validation = (
    train_validation_model[
        TARGET
    ]
)

final_models = {}

for model_name, model in (
    selected_models.items()
):

    print(
        f"\nRefitting {model_name} "
        f"on training + validation..."
    )

    model.fit(
        X_train_validation,
        y_train_validation
    )

    final_models[
        model_name
    ] = model


# ============================================================
# FINAL TEST
# ============================================================

print("\n" + "=" * 70)
print("FINAL TEST EVALUATION")
print("=" * 70)

test_predictions = []


for window_number, (
    target_start,
    target_end
) in enumerate(
    test_windows,
    start=1
):

    if window_number % 5 == 0:

        print(
            f"Processing test window "
            f"{window_number}/"
            f"{len(test_windows)}..."
        )

    history = df.loc[
        :target_start - 1,
        TARGET
    ].values

    timestamps = df.loc[
        target_start:target_end - 1,
        "timestamp"
    ].values

    actual = df.loc[
        target_start:target_end - 1,
        TARGET
    ].values

    origin = df.loc[
        target_start - 1,
        "timestamp"
    ]


    # --------------------------------------------------------
    # SEASONAL NAIVE
    # --------------------------------------------------------

    naive_prediction = (
        seasonal_naive_forecast(
            history
        )
    )

    for horizon, (
        timestamp,
        y_actual,
        prediction
    ) in enumerate(
        zip(
            timestamps,
            actual,
            naive_prediction
        ),
        start=1
    ):

        test_predictions.append({

            "model":
                "Seasonal Naive",

            "forecast_window":
                window_number,

            "origin":
                origin,

            "timestamp":
                timestamp,

            "horizon":
                horizon,

            "actual":
                y_actual,

            "prediction":
                max(
                    0.0,
                    prediction
                ),
        })


    # --------------------------------------------------------
    # ML MODELS
    # --------------------------------------------------------

    for model_name, model in (
        final_models.items()
    ):

        forecast = recursive_forecast(
            model,
            history,
            pd.Timestamp(
                timestamps[0]
            )
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
                    model_name,

                "forecast_window":
                    window_number,

                "origin":
                    origin,

                "timestamp":
                    timestamp,

                "horizon":
                    horizon,

                "actual":
                    y_actual,

                "prediction":
                    prediction,
            })


# ============================================================
# SAVE PREDICTIONS
# ============================================================

test_predictions_df = (
    pd.DataFrame(
        test_predictions
    )
)

prediction_file = os.path.join(
    PREDICTIONS_DIR,
    "test_predictions_arrival_hour.csv"
)

test_predictions_df.to_csv(
    prediction_file,
    index=False
)


# ============================================================
# TEST METRICS
# ============================================================

test_metrics = []

for model_name in (
    test_predictions_df[
        "model"
    ].unique()
):

    model_data = (
        test_predictions_df[
            test_predictions_df[
                "model"
            ] == model_name
        ]
    )

    y_true = (
        model_data[
            "actual"
        ].values
    )

    y_pred = (
        model_data[
            "prediction"
        ].values
    )

    metrics = calculate_metrics(
        y_true,
        y_pred,
        y_train_validation.values
    )

    test_metrics.append({

        "Model":
            model_name,

        **metrics,

    })


test_metrics_df = (
    pd.DataFrame(
        test_metrics
    )
)

test_metrics_df = (
    test_metrics_df
    .sort_values("RMSE")
    .reset_index(drop=True)
)

test_metrics_file = os.path.join(
    METRICS_DIR,
    "test_metrics_arrival_hour.csv"
)

test_metrics_df.to_csv(
    test_metrics_file,
    index=False
)


# ============================================================
# HORIZON METRICS
# ============================================================

horizon_results = []

for model_name in (
    test_predictions_df[
        "model"
    ].unique()
):

    for horizon in range(1, 25):

        data = test_predictions_df[
            (
                test_predictions_df[
                    "model"
                ] == model_name
            )
            &
            (
                test_predictions_df[
                    "horizon"
                ] == horizon
            )
        ]

        y_true = data[
            "actual"
        ].values

        y_pred = data[
            "prediction"
        ].values

        horizon_results.append({

            "Model":
                model_name,

            "Horizon":
                horizon,

            "MAE":
                calculate_mae(
                    y_true,
                    y_pred
                ),

            "RMSE":
                calculate_rmse(
                    y_true,
                    y_pred
                ),

        })


horizon_df = pd.DataFrame(
    horizon_results
)

horizon_file = os.path.join(
    METRICS_DIR,
    "horizon_metrics_arrival_hour.csv"
)

horizon_df.to_csv(
    horizon_file,
    index=False
)


# ============================================================
# FINAL OUTPUT
# ============================================================

print("\n" + "=" * 70)
print("FINAL TEST RESULTS")
print("=" * 70)

print(
    test_metrics_df.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)

print("\nFiles created:")

print(
    f"Validation metrics:\n"
    f"  {validation_metrics_file}"
)

print(
    f"\nTest predictions:\n"
    f"  {prediction_file}"
)

print(
    f"\nTest metrics:\n"
    f"  {test_metrics_file}"
)

print(
    f"\nHorizon metrics:\n"
    f"  {horizon_file}"
)

print("\n" + "=" * 70)
print("ARRIVAL-HOUR ROBUSTNESS EXPERIMENT COMPLETE")
print("=" * 70)
