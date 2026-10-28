/** Every API path the frontend may call. Fixed set; no dynamic file paths. */

export const endpoints = {
  health: "/api/health",
  overview: "/api/overview",

  demandSummary: "/api/demand/summary",
  demandHourly: "/api/demand/hourly",
  demandProfile: "/api/demand/profile",
  demandWeekday: "/api/demand/weekday",
  demandMonthly: "/api/demand/monthly",
  demandHeatmap: "/api/demand/heatmap",
  demandDistribution: "/api/demand/distribution",
  demandAcf: "/api/demand/acf",
  demandScenario: "/api/demand/scenario",
  demandCapacity: "/api/demand/capacity",

  forecastModels: "/api/forecast/models",
  forecastWindows: "/api/forecast/windows",
  forecastWindow: (id: number) => `/api/forecast/${id}`,

  modelMetrics: "/api/models/metrics",
  modelValidation: "/api/models/validation",
  modelHorizon: "/api/models/horizon",
  dmAudited: "/api/models/dm/audited",
  dmInteractive: "/api/models/dm/interactive",

  peakAudited: "/api/peak/audited",
  peakThresholds: "/api/peak/thresholds",
  peakSupplementary: "/api/peak/supplementary",
  peakInteractive: "/api/peak/interactive",

  shap: "/api/explainability/shap",
  randomForest: "/api/explainability/random-forest",
  xgboost: "/api/explainability/xgboost",

  robustnessSummary: "/api/robustness/summary",
  robustnessMetrics: "/api/robustness/metrics",
  robustnessHorizon: "/api/robustness/horizon",

  artifacts: "/api/research/artifacts",
  provenance: "/api/research/provenance",
} as const;
