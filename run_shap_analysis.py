import os
import warnings

import numpy as np
import pandas as pd
import shap

from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

warnings.filterwarnings("ignore")


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "data/processed/model_data.csv"

OUTPUT_DIR = "results/explainability"

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

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
print("SHAP EXPLAINABILITY ANALYSIS")
print("=" * 70)

print("\nLoading model data...")

df = pd.read_csv(
    INPUT_FILE
)

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
    f"Total observations: "
    f"{len(df):,}"
)


# ============================================================
# CHRONOLOGICAL SPLIT
# ============================================================

n = len(df)

train_end = int(
    n * 0.70
)

validation_end = int(
    n * 0.85
)

train_validation_df = (
    df.iloc[:validation_end]
    .copy()
)

test_df = (
    df.iloc[validation_end:]
    .copy()
)


print("\n" + "=" * 70)
print("DATA SPLIT")
print("=" * 70)

print(
    f"\nTrain + validation rows: "
    f"{len(train_validation_df):,}"
)

print(
    f"Test rows: "
    f"{len(test_df):,}"
)


# ============================================================
# REMOVE INCOMPLETE FEATURE ROWS
# ============================================================

train_validation_model = (
    train_validation_df
    .dropna(
        subset=FEATURES
    )
    .copy()
)

test_model = (
    test_df
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

X_test = (
    test_model[
        FEATURES
    ]
)

y_test = (
    test_model[
        TARGET
    ]
)


print(
    f"\nTraining rows with "
    f"complete features: "
    f"{len(X_train_validation):,}"
)

print(
    f"Test rows with "
    f"complete features: "
    f"{len(X_test):,}"
)


# ============================================================
# FINAL RANDOM FOREST
# ============================================================

print("\n" + "=" * 70)
print("FITTING FINAL RANDOM FOREST")
print("=" * 70)

random_forest = RandomForestRegressor(
    n_estimators=300,
    max_depth=20,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)

random_forest.fit(
    X_train_validation,
    y_train_validation
)

print(
    "Random Forest fitted successfully."
)


# ============================================================
# FINAL XGBOOST
# ============================================================

print("\n" + "=" * 70)
print("FITTING FINAL XGBOOST")
print("=" * 70)

xgboost_model = XGBRegressor(
    n_estimators=200,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="reg:squarederror",
    random_state=42,
    n_jobs=-1
)

xgboost_model.fit(
    X_train_validation,
    y_train_validation
)

print(
    "XGBoost fitted successfully."
)


# ============================================================
# VERIFY MODELS
# ============================================================

print("\n" + "=" * 70)
print("MODEL VERIFICATION")
print("=" * 70)

rf_test_predictions = (
    random_forest.predict(
        X_test
    )
)

xgb_test_predictions = (
    xgboost_model.predict(
        X_test
    )
)

print(
    f"\nRandom Forest test predictions: "
    f"{len(rf_test_predictions):,}"
)

print(
    f"XGBoost test predictions: "
    f"{len(xgb_test_predictions):,}"
)


# ============================================================
# FEATURE IMPORTANCE — RANDOM FOREST
# ============================================================

print("\n" + "=" * 70)
print("RANDOM FOREST FEATURE IMPORTANCE")
print("=" * 70)

rf_importance = pd.DataFrame({

    "feature":
        FEATURES,

    "importance":
        random_forest.feature_importances_

})

rf_importance = (
    rf_importance
    .sort_values(
        "importance",
        ascending=False
    )
    .reset_index(drop=True)
)

rf_importance[
    "importance_percent"
] = (
    rf_importance[
        "importance"
    ]
    * 100
)

rf_importance_file = os.path.join(
    OUTPUT_DIR,
    "random_forest_feature_importance.csv"
)

rf_importance.to_csv(
    rf_importance_file,
    index=False
)

print(
    rf_importance.to_string(
        index=False,
        float_format=lambda x: f"{x:.6f}"
    )
)


# ============================================================
# FEATURE IMPORTANCE — XGBOOST
# ============================================================

print("\n" + "=" * 70)
print("XGBOOST FEATURE IMPORTANCE")
print("=" * 70)

xgb_importance = pd.DataFrame({

    "feature":
        FEATURES,

    "importance":
        xgboost_model.feature_importances_

})

xgb_importance = (
    xgb_importance
    .sort_values(
        "importance",
        ascending=False
    )
    .reset_index(drop=True)
)

xgb_importance[
    "importance_percent"
] = (
    xgb_importance[
        "importance"
    ]
    * 100
)

xgb_importance_file = os.path.join(
    OUTPUT_DIR,
    "xgboost_feature_importance.csv"
)

xgb_importance.to_csv(
    xgb_importance_file,
    index=False
)

print(
    xgb_importance.to_string(
        index=False,
        float_format=lambda x: f"{x:.6f}"
    )
)


# ============================================================
# SHAP — RANDOM FOREST
# ============================================================

print("\n" + "=" * 70)
print("CALCULATING RANDOM FOREST SHAP VALUES")
print("=" * 70)

rf_explainer = shap.TreeExplainer(
    random_forest
)

rf_shap_values = (
    rf_explainer.shap_values(
        X_test
    )
)

rf_shap_values = np.asarray(
    rf_shap_values
)

if rf_shap_values.ndim == 3:
    rf_shap_values = (
        rf_shap_values[:, :, 0]
    )


# Mean absolute SHAP importance
rf_shap_importance = pd.DataFrame({

    "feature":
        FEATURES,

    "mean_abs_shap":
        np.mean(
            np.abs(
                rf_shap_values
            ),
            axis=0
        )

})

rf_shap_importance = (
    rf_shap_importance
    .sort_values(
        "mean_abs_shap",
        ascending=False
    )
    .reset_index(drop=True)
)

rf_shap_importance_file = os.path.join(
    OUTPUT_DIR,
    "random_forest_shap_importance.csv"
)

rf_shap_importance.to_csv(
    rf_shap_importance_file,
    index=False
)


# Save individual SHAP values
rf_shap_df = pd.DataFrame(
    rf_shap_values,
    columns=FEATURES
)

rf_shap_df.insert(
    0,
    "timestamp",
    test_model[
        "timestamp"
    ].values
)

rf_shap_df.insert(
    1,
    "actual_demand_kWh",
    y_test.values
)

rf_shap_df.insert(
    2,
    "model_prediction_kWh",
    rf_test_predictions
)

rf_shap_values_file = os.path.join(
    OUTPUT_DIR,
    "random_forest_shap_values.csv"
)

rf_shap_df.to_csv(
    rf_shap_values_file,
    index=False
)

print(
    "Random Forest SHAP calculation complete."
)


# ============================================================
# SHAP — XGBOOST
# ============================================================

print("\n" + "=" * 70)
print("CALCULATING XGBOOST SHAP VALUES")
print("=" * 70)

xgb_explainer = shap.TreeExplainer(
    xgboost_model
)

xgb_shap_values = (
    xgb_explainer.shap_values(
        X_test
    )
)

xgb_shap_values = np.asarray(
    xgb_shap_values
)

if xgb_shap_values.ndim == 3:
    xgb_shap_values = (
        xgb_shap_values[:, :, 0]
    )


# Mean absolute SHAP importance
xgb_shap_importance = pd.DataFrame({

    "feature":
        FEATURES,

    "mean_abs_shap":
        np.mean(
            np.abs(
                xgb_shap_values
            ),
            axis=0
        )

})

xgb_shap_importance = (
    xgb_shap_importance
    .sort_values(
        "mean_abs_shap",
        ascending=False
    )
    .reset_index(drop=True)
)

xgb_shap_importance_file = os.path.join(
    OUTPUT_DIR,
    "xgboost_shap_importance.csv"
)

xgb_shap_importance.to_csv(
    xgb_shap_importance_file,
    index=False
)


# Save individual SHAP values
xgb_shap_df = pd.DataFrame(
    xgb_shap_values,
    columns=FEATURES
)

xgb_shap_df.insert(
    0,
    "timestamp",
    test_model[
        "timestamp"
    ].values
)

xgb_shap_df.insert(
    1,
    "actual_demand_kWh",
    y_test.values
)

xgb_shap_df.insert(
    2,
    "model_prediction_kWh",
    xgb_test_predictions
)

xgb_shap_values_file = os.path.join(
    OUTPUT_DIR,
    "xgboost_shap_values.csv"
)

xgb_shap_df.to_csv(
    xgb_shap_values_file,
    index=False
)

print(
    "XGBoost SHAP calculation complete."
)


# ============================================================
# COMBINED IMPORTANCE
# ============================================================

print("\n" + "=" * 70)
print("COMBINING SHAP IMPORTANCE")
print("=" * 70)

combined_importance = (
    rf_shap_importance[
        [
            "feature",
            "mean_abs_shap"
        ]
    ]
    .rename(
        columns={
            "mean_abs_shap":
                "Random_Forest_mean_abs_SHAP"
        }
    )
    .merge(
        xgb_shap_importance[
            [
                "feature",
                "mean_abs_shap"
            ]
        ].rename(
            columns={
                "mean_abs_shap":
                    "XGBoost_mean_abs_SHAP"
            }
        ),
        on="feature",
        how="outer"
    )
)

combined_importance[
    "Average_mean_abs_SHAP"
] = (
    combined_importance[
        [
            "Random_Forest_mean_abs_SHAP",
            "XGBoost_mean_abs_SHAP"
        ]
    ]
    .mean(axis=1)
)

combined_importance = (
    combined_importance
    .sort_values(
        "Average_mean_abs_SHAP",
        ascending=False
    )
    .reset_index(drop=True)
)

combined_file = os.path.join(
    OUTPUT_DIR,
    "combined_shap_importance.csv"
)

combined_importance.to_csv(
    combined_file,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("TOP SHAP FEATURES")
print("=" * 70)

print(
    combined_importance.head(
        10
    ).to_string(
        index=False,
        float_format=lambda x: f"{x:.6f}"
    )
)


print("\n" + "=" * 70)
print("SHAP ANALYSIS COMPLETE")
print("=" * 70)

print("\nFiles created:")

print(
    f"\nRandom Forest feature importance:"
    f"\n  {rf_importance_file}"
)

print(
    f"\nXGBoost feature importance:"
    f"\n  {xgb_importance_file}"
)

print(
    f"\nRandom Forest SHAP importance:"
    f"\n  {rf_shap_importance_file}"
)

print(
    f"\nXGBoost SHAP importance:"
    f"\n  {xgb_shap_importance_file}"
)

print(
    f"\nRandom Forest SHAP values:"
    f"\n  {rf_shap_values_file}"
)

print(
    f"\nXGBoost SHAP values:"
    f"\n  {xgb_shap_values_file}"
)

print(
    f"\nCombined SHAP importance:"
    f"\n  {combined_file}"
)

print("\nDone.")