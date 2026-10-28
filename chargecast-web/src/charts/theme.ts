/** Shared chart tokens so every chart is styled identically. */

export const COLORS = {
  signal: "#4F46E5",
  prediction: "#EA580C",
  violet: "#7C6CF2",
  rose: "#E11D48",
  lime: "#16A34A",
  muted: "#6B7280",
  grid: "#E5E7EB",
  ink: "#111827",
  base: "#FFFFFF",
  surface: "#FFFFFF",
} as const;

const MODEL_COLORS: Record<string, string> = {
  xgboost: COLORS.signal,
  random_forest: COLORS.prediction,
  linear_regression: COLORS.violet,
  seasonal_naive: COLORS.muted,
  sarimax_fourier: COLORS.rose,
  sarimax: COLORS.rose,
};

const CYCLE = [
  COLORS.signal,
  COLORS.prediction,
  COLORS.violet,
  COLORS.rose,
  COLORS.lime,
  COLORS.muted,
];

function normalise(name: string): string {
  return name.trim().toLowerCase().replace(/\+/g, " ").replace(/[\s-]+/g, "_");
}

/** Stable per-model colour, so a model keeps its hue across every chart. */
export function modelColor(name: string, index = 0): string {
  const key = normalise(name);
  if (MODEL_COLORS[key]) return MODEL_COLORS[key];
  for (const [known, colour] of Object.entries(MODEL_COLORS)) {
    if (key.includes(known) || known.includes(key)) return colour;
  }
  return CYCLE[index % CYCLE.length];
}

export const axis = {
  stroke: COLORS.grid,
  tick: { fill: COLORS.muted, fontSize: 11 },
};

export const tooltipStyle = {
  contentStyle: {
    background: COLORS.surface,
    border: `1px solid ${COLORS.signal}33`,
    borderRadius: 10,
    fontSize: 12,
    color: COLORS.ink,
    boxShadow: "0 12px 28px -16px rgba(17,24,39,.25)",
  },
  labelStyle: { color: COLORS.muted, fontSize: 11, marginBottom: 4 },
  itemStyle: { color: COLORS.ink },
} as const;

/** Sequential scale from near-white to the deep indigo accent. */
export function heatColor(t: number): string {
  const stops: [number, [number, number, number]][] = [
    [0, [243, 244, 255]],
    [0.25, [199, 200, 252]],
    [0.55, [138, 125, 255]],
    [0.8, [99, 102, 241]],
    [1, [67, 56, 202]],
  ];
  const x = Math.max(0, Math.min(1, Number.isFinite(t) ? t : 0));
  for (let i = 1; i < stops.length; i += 1) {
    const [p0, c0] = stops[i - 1];
    const [p1, c1] = stops[i];
    if (x <= p1) {
      const f = (x - p0) / (p1 - p0 || 1);
      const c = c0.map((v, j) => Math.round(v + (c1[j] - v) * f));
      return `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
    }
  }
  return "rgb(67, 56, 202)";
}
