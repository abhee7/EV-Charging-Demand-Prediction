import os
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

DEMAND_FILE = (
    "data/processed/hourly_demand.csv"
)

MODEL_DATA_FILE = (
    "data/processed/model_data.csv"
)

ARRIVAL_DEMAND_FILE = (
    "data/processed/"
    "hourly_demand_arrival_hour.csv"
)

ARRIVAL_MODEL_DATA_FILE = (
    "data/processed/model_data_arrival_hour.csv"
)

TEST_METRICS_FILE = (
    "results/metrics/"
    "test_metrics_corrected.csv"
)

VALIDATION_METRICS_FILE = (
    "results/metrics/"
    "validation_metrics_corrected.csv"
)

HORIZON_FILE = (
    "results/metrics/"
    "horizon_metrics.csv"
)

SARIMAX_TEST_FILE = (
    "results/metrics/"
    "sarimax_fourier_test_metrics.csv"
)

SARIMAX_VALIDATION_FILE = (
    "results/metrics/"
    "sarimax_fourier_validation_metrics.csv"
)

SARIMAX_HORIZON_FILE = (
    "results/metrics/"
    "sarimax_fourier_horizon_metrics.csv"
)

DM_FILE = (
    "results/metrics/"
    "diebold_mariano_tests.csv"
)

TEST_PREDICTIONS_FILE = (
    "results/predictions/"
    "test_predictions_corrected.csv"
)

SARIMAX_PREDICTIONS_FILE = (
    "results/predictions/"
    "sarimax_fourier_test_predictions.csv"
)

ARRIVAL_TEST_METRICS_FILE = (
    "results/arrival_hour/"
    "metrics/"
    "test_metrics_arrival_hour.csv"
)

ARRIVAL_VALIDATION_METRICS_FILE = (
    "results/arrival_hour/"
    "metrics/"
    "validation_metrics_arrival_hour.csv"
)

ARRIVAL_HORIZON_FILE = (
    "results/arrival_hour/"
    "metrics/"
    "horizon_metrics_arrival_hour.csv"
)

ARRIVAL_PREDICTIONS_FILE = (
    "results/arrival_hour/"
    "predictions/"
    "test_predictions_arrival_hour.csv"
)

SHAP_FILE = (
    "results/explainability/"
    "combined_shap_importance.csv"
)

PEAK_SUMMARY_FILE = (
    "results/peak_analysis/"
    "overall_demand_summary.csv"
)

PEAK_DETECTION_FILE = (
    "results/peak_analysis/"
    "model_peak_detection.csv"
)

FIGURES_DIR = (
    "results/figures"
)


# ============================================================
# AUDIT COUNTERS
# ============================================================

checks_passed = 0
checks_failed = 0


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def check(
    name,
    condition,
    detail=""
):

    global checks_passed
    global checks_failed

    if condition:

        print(
            f"[PASS] {name}"
        )

        if detail:
            print(
                f"       {detail}"
            )

        checks_passed += 1

    else:

        print(
            f"[FAIL] {name}"
        )

        if detail:
            print(
                f"       {detail}"
            )

        checks_failed += 1


def section(title):

    print(
        "\n"
        + "=" * 70
    )

    print(title)

    print(
        "=" * 70
    )


def load_csv(path):

    if not os.path.exists(path):

        print(
            f"[MISSING] {path}"
        )

        return None

    return pd.read_csv(path)


# ============================================================
# START
# ============================================================

print("=" * 70)
print("FINAL RESULTS AUDIT")
print("=" * 70)


# ============================================================
# 1. PRIMARY DATASET
# ============================================================

section(
    "1. PRIMARY DATASET"
)

demand = load_csv(
    DEMAND_FILE
)

if demand is not None:

    check(
        "Primary hourly dataset exists",
        len(demand) > 0,
        f"Rows: {len(demand):,}"
    )

    check(
        "Expected primary hourly rows",
        len(demand) == 7288,
        f"Observed: {len(demand):,}"
    )

    check(
        "Required demand column exists",
        "demand_kWh" in demand.columns
    )

    if "timestamp" in demand.columns:

        timestamps = pd.to_datetime(
            demand["timestamp"],
            utc=True
        )

        sorted_timestamps = (
            timestamps
            .sort_values()
        )

        gaps = (
            sorted_timestamps
            .diff()
            .dropna()
        )

        max_gap = (
            gaps.max()
            if len(gaps)
            else None
        )

        check(
            "Hourly timestamps are continuous",
            (
                len(gaps) == 0
                or max_gap
                == pd.Timedelta(hours=1)
            ),
            f"Maximum gap: {max_gap}"
        )

        check(
            "No duplicate timestamps",
            timestamps.nunique()
            == len(timestamps),
            (
                f"Unique: "
                f"{timestamps.nunique():,}; "
                f"Rows: {len(timestamps):,}"
            )
        )


# ============================================================
# 2. PRIMARY ENERGY CONSERVATION
# ============================================================

section(
    "2. PRIMARY ENERGY CONSERVATION"
)

if demand is not None:

    hourly_total = (
        demand["demand_kWh"]
        .sum()
    )

    expected_total = (
        155616.209300
    )

    check(
        "Primary reconstructed energy total",
        np.isclose(
            hourly_total,
            expected_total,
            atol=0.01
        ),
        (
            f"Observed: "
            f"{hourly_total:.6f} kWh; "
            f"Expected: "
            f"{expected_total:.6f} kWh"
        )
    )

    check(
        "No negative hourly demand",
        (
            demand["demand_kWh"]
            >= 0
        ).all()
    )


# ============================================================
# 3. MODEL DATA
# ============================================================

section(
    "3. MODEL DATA"
)

model_data = load_csv(
    MODEL_DATA_FILE
)

if model_data is not None:

    check(
        "Model dataset exists",
        len(model_data) == 7288,
        f"Rows: {len(model_data):,}"
    )

    required_features = [

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

    missing_features = [
        feature
        for feature in required_features
        if feature not in model_data.columns
    ]

    check(
        "All model features present",
        len(missing_features) == 0,
        (
            "Missing: "
            + str(missing_features)
            if missing_features
            else
            "All 17 features present"
        )
    )


# ============================================================
# 4. PRIMARY TEST METRICS
# ============================================================

section(
    "4. PRIMARY TEST METRICS"
)

test_metrics = load_csv(
    TEST_METRICS_FILE
)

if test_metrics is not None:

    expected_models = {
        "Linear Regression",
        "Random Forest",
        "XGBoost",
        "Seasonal Naive"
    }

    observed_models = set(
        test_metrics["Model"]
    )

    check(
        "Expected primary ML models present",
        expected_models
        .issubset(
            observed_models
        ),
        f"Models: {sorted(observed_models)}"
    )

    metric_columns = [
        "MAE",
        "RMSE",
        "R2",
        "sMAPE_percent",
        "MASE"
    ]

    check(
        "Primary metrics contain no missing values",
        not test_metrics[
            metric_columns
        ]
        .isna()
        .any()
        .any()
    )

    print(
        "\nPrimary test metrics:"
    )

    print(
        test_metrics.to_string(
            index=False
        )
    )


# ============================================================
# 5. SARIMAX + FOURIER
# ============================================================

section(
    "5. SARIMAX + FOURIER"
)

sarimax_test = load_csv(
    SARIMAX_TEST_FILE
)

sarimax_validation = load_csv(
    SARIMAX_VALIDATION_FILE
)

sarimax_horizon = load_csv(
    SARIMAX_HORIZON_FILE
)

check(
    "SARIMAX test metrics exist",
    sarimax_test is not None
)

check(
    "SARIMAX validation metrics exist",
    sarimax_validation is not None
)

check(
    "SARIMAX horizon metrics exist",
    sarimax_horizon is not None
)

if sarimax_test is not None:

    print(
        "\nSARIMAX test metrics:"
    )

    print(
        sarimax_test.to_string(
            index=False
        )
    )


# ============================================================
# 6. PRIMARY TEST PREDICTIONS
# ============================================================

section(
    "6. PRIMARY TEST PREDICTIONS"
)

test_predictions = load_csv(
    TEST_PREDICTIONS_FILE
)

sarimax_predictions = load_csv(
    SARIMAX_PREDICTIONS_FILE
)

if test_predictions is not None:

    check(
        "ML test predictions have 4,320 rows",
        len(test_predictions) == 4320,
        f"Rows: {len(test_predictions):,}"
    )

    check(
        "ML test predictions have 4 models",
        test_predictions[
            "model"
        ].nunique() == 4
    )

    check(
        "ML test predictions have 45 forecast windows",
        test_predictions[
            "forecast_window"
        ].nunique() == 45,
        (
            f"Windows: "
            f"{test_predictions['forecast_window'].nunique()}"
        )
    )

    check(
        "ML test predictions have 24 horizons",
        test_predictions[
            "horizon"
        ].nunique() == 24
    )

    check(
        "No missing ML predictions",
        not test_predictions[
            "prediction"
        ].isna().any()
    )

if sarimax_predictions is not None:

    check(
        "SARIMAX predictions have 1,080 rows",
        len(sarimax_predictions) == 1080,
        f"Rows: {len(sarimax_predictions):,}"
    )

    check(
        "SARIMAX predictions have 24 horizons",
        sarimax_predictions[
            "horizon"
        ].nunique() == 24
    )


# ============================================================
# 7. HORIZON METRICS
# ============================================================

section(
    "7. PRIMARY HORIZON METRICS"
)

horizon = load_csv(
    HORIZON_FILE
)

if horizon is not None:

    check(
        "Primary horizon metrics have 96 rows",
        len(horizon) == 96,
        f"Rows: {len(horizon)}"
    )

    check(
        "Primary horizon metrics contain 4 models",
        horizon[
            "Model"
        ].nunique() == 4
    )

    check(
        "Primary horizon metrics contain 24 horizons",
        horizon[
            "Horizon"
        ].nunique() == 24
    )


# ============================================================
# 8. DIEBOLD-MARIANO TESTS
# ============================================================

section(
    "8. DIEBOLD-MARIANO TESTS"
)

dm = load_csv(
    DM_FILE
)

if dm is not None:

    print(
        "\nDM test results:"
    )

    print(
        dm.to_string(
            index=False
        )
    )

    check(
        "DM results file exists",
        len(dm) > 0,
        f"Comparisons: {len(dm)}"
    )

    if "p_value" in dm.columns:

        check(
            "DM p-values are valid",
            (
                dm["p_value"]
                >= 0
            ).all()
            &
            (
                dm["p_value"]
                <= 1
            ).all()
        )

    if "Observations" in dm.columns:

        check(
            "DM tests use 1,080 observations",
            (
                dm["Observations"]
                == 1080
            ).all()
        )

    if "HAC_lag" in dm.columns:

        check(
            "DM tests use HAC lag 23",
            (
                dm["HAC_lag"]
                == 23
            ).all()
        )


# ============================================================
# 9. ROBUSTNESS TARGET
# ============================================================

section(
    "9. ROBUSTNESS TARGET"
)

arrival_demand = load_csv(
    ARRIVAL_DEMAND_FILE
)

arrival_model_data = load_csv(
    ARRIVAL_MODEL_DATA_FILE
)

arrival_test = load_csv(
    ARRIVAL_TEST_METRICS_FILE
)

arrival_validation = load_csv(
    ARRIVAL_VALIDATION_METRICS_FILE
)

arrival_horizon = load_csv(
    ARRIVAL_HORIZON_FILE
)

arrival_predictions = load_csv(
    ARRIVAL_PREDICTIONS_FILE
)

if arrival_demand is not None:

    check(
        "Arrival-hour demand exists",
        len(arrival_demand) == 7287,
        f"Rows: {len(arrival_demand):,}"
    )

    arrival_total = (
        arrival_demand[
            "demand_kWh"
        ].sum()
    )

    expected_arrival_total = (
        155710.578
    )

    check(
        "Arrival-hour total energy",
        np.isclose(
            arrival_total,
            expected_arrival_total,
            atol=0.01
        ),
        (
            f"Observed: "
            f"{arrival_total:.6f} kWh; "
            f"Expected: "
            f"{expected_arrival_total:.6f} kWh"
        )
    )


if arrival_model_data is not None:

    check(
        "Arrival-hour model data exists",
        len(arrival_model_data) == 7287,
        f"Rows: {len(arrival_model_data):,}"
    )


if arrival_test is not None:

    check(
        "Arrival-hour test metrics contain 4 models",
        arrival_test[
            "Model"
        ].nunique() == 4
    )

    print(
        "\nArrival-hour test metrics:"
    )

    print(
        arrival_test.to_string(
            index=False
        )
    )


if arrival_validation is not None:

    check(
        "Arrival-hour validation metrics exist",
        len(arrival_validation) > 0
    )


if arrival_horizon is not None:

    check(
        "Arrival horizon metrics have 96 rows",
        len(arrival_horizon) == 96,
        f"Rows: {len(arrival_horizon)}"
    )

    check(
        "Arrival horizon metrics contain 4 models",
        arrival_horizon[
            "Model"
        ].nunique() == 4
    )

    check(
        "Arrival horizon metrics contain 24 horizons",
        arrival_horizon[
            "Horizon"
        ].nunique() == 24
    )


if arrival_predictions is not None:

    # 4 models × 45 forecast windows × 24 horizons
    expected_arrival_predictions = (
        4 * 45 * 24
    )

    check(
        "Arrival test predictions have 4,320 rows",
        len(arrival_predictions)
        == expected_arrival_predictions,
        (
            f"Rows: "
            f"{len(arrival_predictions):,}; "
            f"Expected: "
            f"{expected_arrival_predictions:,}"
        )
    )

    check(
        "Arrival predictions have 4 models",
        arrival_predictions[
            "model"
        ].nunique() == 4
    )

    check(
        "Arrival predictions have 45 forecast windows",
        arrival_predictions[
            "forecast_window"
        ].nunique() == 45
    )

    check(
        "Arrival predictions have 24 horizons",
        arrival_predictions[
            "horizon"
        ].nunique() == 24
    )

    check(
        "No missing arrival predictions",
        not arrival_predictions[
            "prediction"
        ].isna().any()
    )


# ============================================================
# 10. SHAP EXPLAINABILITY
# ============================================================

section(
    "10. SHAP EXPLAINABILITY"
)

shap = load_csv(
    SHAP_FILE
)

if shap is not None:

    check(
        "Combined SHAP importance exists",
        len(shap) > 0,
        f"Features: {len(shap)}"
    )

    check(
        "SHAP analysis contains 17 features",
        len(shap) == 17,
        f"Features: {len(shap)}"
    )

    print(
        "\nSHAP importance preview:"
    )

    print(
        shap.head(10).to_string(
            index=False
        )
    )


# ============================================================
# 11. PEAK ANALYSIS
# ============================================================

section(
    "11. PEAK ANALYSIS"
)

peak_summary = load_csv(
    PEAK_SUMMARY_FILE
)

peak_detection = load_csv(
    PEAK_DETECTION_FILE
)

if peak_summary is not None:

    check(
        "Peak summary exists",
        len(peak_summary) == 1
    )

    if (
        "peak_hourly_demand_kWh"
        in peak_summary.columns
    ):

        peak = (
            peak_summary[
                "peak_hourly_demand_kWh"
            ].iloc[0]
        )

        check(
            "Peak demand matches expected value",
            np.isclose(
                peak,
                136.3581,
                atol=0.01
            ),
            f"Peak: {peak:.4f} kWh"
        )


if peak_detection is not None:

    check(
        "Peak detection contains 5 models",
        peak_detection[
            "model"
        ].nunique() == 5
    )


# ============================================================
# 12. FIGURE OUTPUTS
# ============================================================

section(
    "12. FIGURE OUTPUTS"
)

if os.path.exists(
    FIGURES_DIR
):

    figures = [
        filename
        for filename
        in os.listdir(
            FIGURES_DIR
        )
        if filename.endswith(
            ".png"
        )
    ]

    check(
        "All 12 research figures exist",
        len(figures) == 12,
        f"PNG files: {len(figures)}"
    )

    for filename in sorted(
        figures
    ):

        print(
            f"  {filename}"
        )

else:

    check(
        "Figures directory exists",
        False
    )


# ============================================================
# 13. LEGACY FILE CHECK
# ============================================================

section(
    "13. LEGACY FILE CHECK"
)

legacy_file = (
    "results/metrics/"
    "sarima_validation_metrics.csv"
)

if os.path.exists(
    legacy_file
):

    print(
        "[INFO] Legacy SARIMA file exists:"
    )

    print(
        f"       {legacy_file}"
    )

    print(
        "       Do NOT use this file in the final report."
    )

else:

    print(
        "[INFO] Legacy SARIMA file not present."
    )


# ============================================================
# FINAL AUDIT SUMMARY
# ============================================================

section(
    "AUDIT SUMMARY"
)

print(
    f"Checks passed: "
    f"{checks_passed}"
)

print(
    f"Checks failed: "
    f"{checks_failed}"
)

if checks_failed == 0:

    print(
        "\nRESULT: ALL AUTOMATED CHECKS PASSED"
    )

else:

    print(
        "\nRESULT: REVIEW FAILED CHECKS BEFORE REPORT WRITING"
    )

print(
    "\nAudit complete."
)