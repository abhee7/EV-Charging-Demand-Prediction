/** Response types for the ChargeCast API. */

export interface Unavailable {
  available: false;
  reason: string;
  path?: string;
  label?: string;
  producedBy?: string;
  detail?: string;
  expectedColumns?: string[];
  detectedColumns?: string[];
  missingColumns?: string[];
}

export type Maybe<T> = (T & { available: true }) | Unavailable;

export function isAvailable<T>(value: Maybe<T> | undefined | null): value is T & { available: true } {
  return !!value && (value as { available?: boolean }).available === true;
}

export interface Health {
  status: "ok";
  service: string;
  version: string;
  repositoryRoot: string;
  repositoryExists: boolean;
  artifactsAvailable: number;
  artifactsTotal: number;
  readOnly: boolean;
}

export interface DemandSummary {
  available: boolean;
  observations?: number;
  totalKwh?: number;
  mean?: number;
  median?: number;
  maximum?: number;
  minimum?: number;
  zeroHours?: number;
  p75?: number;
  p90?: number;
  p95?: number;
  p99?: number;
  peakOverAverage?: number | null;
  unit?: string;
  coverageStart?: string;
  coverageEnd?: string;
  source?: string;
  reason?: string;
  path?: string;
}

export interface Overview {
  dataset: string;
  unit: string;
  demand: DemandSummary;
  temporalSignals: { lag: number; label: string; value: number }[];
  forecast: {
    available: boolean;
    models?: string[];
    windowCount?: number;
    latestWindow?: ForecastWindowMeta | null;
    horizonHours?: number;
  };
  targetLimitation: string;
}

export interface DemandPoint { t: string; v: number | null }

export interface HourlyDemand {
  available: true;
  unit: string;
  downsample: number;
  points: DemandPoint[];
  peakThreshold: number | null;
  maximum: number | null;
  totalPoints: number;
  source: string;
}

export interface ProfilePoint { hour: number; mean: number; q1: number; q3: number }
export interface DemandProfile {
  available: true;
  unit: string;
  points: ProfilePoint[];
  source: string;
}

export interface WeekdayPoint { hour: number; weekday: number | null; weekend: number | null }
export interface WeekdaySplit {
  available: true;
  unit: string;
  points: WeekdayPoint[];
  weekdayMean: number | null;
  weekendMean: number | null;
  source: string;
}

export interface MonthlyPoint { month: number; label: string; total: number; mean: number }
export interface MonthlyDemand {
  available: true;
  points: MonthlyPoint[];
  note: string;
  source: string;
}

export interface HeatmapCell { day: number; hour: number; value: number | null }
export interface DemandHeatmap {
  available: true;
  unit: string;
  days: string[];
  cells: HeatmapCell[];
  min: number | null;
  max: number | null;
  source: string;
}

export interface DistributionBin { start: number; end: number; mid: number; count: number }
export interface DemandDistribution {
  available: true;
  unit: string;
  bins: DistributionBin[];
  percentiles: { p75: number; p90: number; p95: number; p99: number };
  source: string;
}

export interface AcfPoint { lag: number; value: number }
export interface AcfHighlight { lag: number; value: number; meaning: string }
export interface Autocorrelation {
  available: true;
  points: AcfPoint[];
  confidence: number | null;
  observations: number;
  highlights: AcfHighlight[];
  selected: AcfHighlight | null;
  source: string;
}

export interface ScenarioResult {
  available: true;
  unit: string;
  changePercent: number;
  baseline: DemandSummary;
  scenario: DemandSummary;
  note: string;
  source: string;
}

export interface CapacityResult {
  available: true;
  unit: string;
  capacityKw: number;
  historicalPeak: number;
  peakOverCapacity: number | null;
  hoursAbove: number;
  shareAbove: number;
  observations: number;
  note: string;
  source: string;
}

export interface ForecastWindowMeta {
  id: number;
  origin: string | null;
  label: string;
  horizons: number | null;
}

export interface ForecastWindows {
  available: true;
  predictionSet: string;
  model: string | null;
  windows: ForecastWindowMeta[];
  count: number;
  source: string;
}

export interface PredictionSetMeta {
  key: string;
  label: string;
  available: boolean;
  path: string;
}

export interface ForecastModels {
  available: true;
  predictionSet: string;
  models: string[];
  sets: PredictionSetMeta[];
  source: string;
}

export interface ForecastPoint {
  horizon: number;
  timestamp: string | null;
  localHour: number | null;
  actual: number | null;
  prediction: number | null;
  absoluteError: number | null;
}

export interface WindowStats {
  mae: number;
  rmse: number;
  r2: number | null;
  observedTotal: number;
  predictedTotal: number;
  observedPeak: number;
  predictedPeak: number;
  observations: number;
}

export interface ForecastWindowDetail {
  available: true;
  predictionSet: string;
  windowId: number;
  model: string;
  origin: string | null;
  unit: string;
  points: ForecastPoint[];
  stats: WindowStats;
  note: string;
  source: string;
}

export type MetricKey = "mae" | "rmse" | "r2" | "smape" | "mase";

export interface ModelMetric {
  model: string;
  mae?: number | null;
  rmse?: number | null;
  r2?: number | null;
  smape?: number | null;
  mase?: number | null;
}

export interface MetricDescriptor {
  key: MetricKey;
  label: string;
  unit: string;
  lowerIsBetter: boolean;
}

export interface MetricsResponse {
  available: boolean;
  models: ModelMetric[];
  metrics: MetricDescriptor[];
  defaultOrder?: string;
  orderingNote?: string;
  selectedMetric?: MetricKey | null;
  sources?: string[];
  reason?: string;
  path?: string;
}

export interface HorizonSeries {
  model: string;
  points: { horizon: number; value: number }[];
}

export interface HorizonResponse {
  available: boolean;
  metric?: MetricKey;
  label?: string;
  unit?: string;
  availableMetrics?: MetricKey[];
  series?: HorizonSeries[];
  note?: string;
  reason?: string;
  path?: string;
}

export interface DmComparison {
  raw: Record<string, string | number | null>;
  modelA: string | null;
  modelB: string | null;
  statistic: number | null;
  pValue: number | null;
  observations: number | null;
  hacLag: number | null;
  loss: string | null;
  significant?: string | null;
  significantAt5Pct?: boolean;
}

export interface DmAudited {
  available: true;
  source: string;
  columns: string[];
  resolvedFields: Record<string, string>;
  absentFields: string[];
  comparisons: DmComparison[];
  rows: Record<string, unknown>[];
  note: string;
  provenance: string;
}

export interface DmInteractive {
  available: boolean;
  modelA?: string;
  modelB?: string;
  statistic?: number;
  pValue?: number;
  observations?: number;
  hacLag?: number;
  loss?: string;
  significantAt5Pct?: boolean;
  availableModels?: string[];
  note?: string;
  provenance?: string;
  reason?: string;
  path?: string;
}

export interface PeakModelRow {
  model: string;
  precision: number | null;
  recall: number | null;
  f1: number | null;
  truePositive?: number | null;
  falsePositive?: number | null;
  falseNegative?: number | null;
  trueNegative?: number | null;
  observedPeakHours?: number | null;
  forecastPeakHours?: number | null;
}

export interface PeakAudited {
  available: true;
  source: string;
  columns: string[];
  resolvedFields: Record<string, string>;
  absentFields: string[];
  hasConfusionMatrix: boolean;
  models: PeakModelRow[];
  rows: Record<string, unknown>[];
  note: string;
  provenance: string;
  caveat: string;
}

export interface PeakThresholds {
  available: true;
  source: string;
  columns: string[];
  entries: { percentile: number | null; threshold: number | null }[];
  rows: Record<string, unknown>[];
  unit: string;
  note: string;
}

export interface PeakInteractive {
  available: boolean;
  percentile?: number;
  auditedPercentile?: number;
  differsFromAudited?: boolean;
  thresholdNotice?: string;
  threshold?: number;
  unit?: string;
  models?: PeakModelRow[];
  selected?: PeakModelRow | null;
  availableModels?: string[];
  note?: string;
  provenance?: string;
  caveat?: string;
  reason?: string;
  path?: string;
}

export interface FeatureAttribution {
  feature: string;
  value: number;
  share?: number;
  description?: string | null;
}

export interface ImportanceResponse {
  available: boolean;
  model?: string;
  source?: string;
  source_kind?: string;
  featureColumn?: string;
  valueColumn?: string;
  features?: FeatureAttribution[];
  note?: string;
  reason?: string;
  path?: string;
  detectedColumns?: string[];
}

export interface CombinedShap {
  available: boolean;
  source?: string;
  groups?: { model: string; features: FeatureAttribution[] }[];
  note?: string;
  interpretation?: string;
  reason?: string;
  path?: string;
}

export interface RobustnessTarget extends DemandSummary {
  target: string;
  label: string;
  construction?: string;
  definition?: string;
}

export interface RobustnessSummary {
  targets: RobustnessTarget[];
  warning: string;
  question: string;
  limitation: string;
}

export interface RobustnessMetricTarget {
  available: boolean;
  target: string;
  label: string;
  models?: ModelMetric[];
  source?: string;
  reason?: string;
  path?: string;
}

export interface RobustnessMetrics {
  targets: RobustnessMetricTarget[];
  warning: string;
}

export interface RobustnessHorizonTarget {
  available: boolean;
  target: string;
  label: string;
  series?: HorizonSeries[];
  reason?: string;
  path?: string;
}

export interface RobustnessHorizon {
  metric: string;
  targets: RobustnessHorizonTarget[];
  warning: string;
}

export type ArtifactStatus = "available" | "optional" | "missing";

export interface ArtifactRow {
  key: string;
  label: string;
  group: string;
  path: string;
  status: ArtifactStatus;
  rows: number | null;
  producedBy: string;
  reason: string | null;
  expectedColumns: string[];
  detectedColumns: string[];
}

export interface ArtifactDirectory {
  key: string;
  label: string;
  path: string;
  pattern: string;
  fileCount: number;
  status: ArtifactStatus;
  files: string[];
}

export interface ArtifactsResponse {
  artifacts: ArtifactRow[];
  directories: ArtifactDirectory[];
  repositoryRoot: string;
}

export interface ProvenanceRow {
  result: string;
  path: string;
  status: "available" | "missing" | "quarantined" | "absent";
  role: string;
}

export interface ProvenanceResponse {
  rows: ProvenanceRow[];
  statements: Record<string, string>;
  study: {
    title: string;
    dataset: string;
    split: string;
    forecasting: string;
    models: string[];
    statisticalTesting: string;
    explainability: string;
    robustness: string;
  };
  limitations: { title: string; body: string }[];
}
