import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { axis, modelColor, tooltipStyle } from "@/charts/theme";
import { num } from "@/lib/format";
import type { ModelMetric, MetricKey } from "@/types/api";

interface Props {
  models: ModelMetric[];
  metric: MetricKey;
  label: string;
  unit?: string;
  height?: number;
}

/**
 * Lollipop comparison. Models keep alphabetical order so the chart shape
 * carries no implied ranking.
 */
export function MetricDots({ models, metric, label, unit, height = 300 }: Props) {
  const data = models
    .filter((m) => typeof m[metric] === "number")
    .map((m, i) => ({
      model: m.model,
      value: m[metric] as number,
      fill: modelColor(m.model, i),
    }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ScatterChart margin={{ top: 8, right: 24, bottom: 16, left: 8 }}>
        <CartesianGrid stroke={axis.stroke} horizontal={false} />
        <XAxis
          type="number"
          dataKey="value"
          stroke={axis.stroke}
          tick={axis.tick}
          label={{
            value: unit ? `${label} (${unit})` : label,
            position: "insideBottom",
            offset: -8,
            fill: "#6B7280",
            fontSize: 11,
          }}
        />
        <YAxis
          type="category"
          dataKey="model"
          stroke={axis.stroke}
          tick={axis.tick}
          width={132}
        />
        <Tooltip
          {...tooltipStyle}
          cursor={{ stroke: "rgba(17,24,39,0.14)" }}
          formatter={(value: number | string) => [num(Number(value), 4), label]}
        />
        <Scatter data={data} isAnimationActive={false} shape="circle" r={7} />
      </ScatterChart>
    </ResponsiveContainer>
  );
}
