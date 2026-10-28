import {
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { COLORS, axis, tooltipStyle } from "@/charts/theme";
import { num } from "@/lib/format";
import type { DistributionBin } from "@/types/api";

interface Props {
  bins: DistributionBin[];
  percentiles: { p75: number; p90: number; p95: number; p99: number };
  unit?: string;
  height?: number;
}

export function DistributionChart({
  bins,
  percentiles,
  unit = "kWh/h",
  height = 320,
}: Props) {
  const marks: [string, number][] = [
    ["P75", percentiles.p75],
    ["P90", percentiles.p90],
    ["P95", percentiles.p95],
    ["P99", percentiles.p99],
  ];

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={bins} margin={{ top: 16, right: 8, bottom: 8, left: -12 }}>
        <CartesianGrid stroke={axis.stroke} vertical={false} />
        <XAxis
          dataKey="mid"
          stroke={axis.stroke}
          tick={axis.tick}
          tickFormatter={(v: number) => num(v, 0)}
          label={{
            value: unit,
            position: "insideBottom",
            offset: -4,
            fill: COLORS.muted,
            fontSize: 11,
          }}
          height={40}
        />
        <YAxis stroke={axis.stroke} tick={axis.tick} width={54} />
        <Tooltip
          {...tooltipStyle}
          cursor={{ fill: "rgba(17,24,39,0.04)" }}
          labelFormatter={(v) => `${num(Number(v), 1)} ${unit}`}
          formatter={(value: number | string) => [`${num(Number(value), 0)}`, "Hours"]}
        />
        {marks.map(([label, value], i) => (
          <ReferenceLine
            key={label}
            x={value}
            stroke={COLORS.prediction}
            strokeDasharray="3 3"
            strokeWidth={1}
            label={{
              value: `${label} ${num(value, 1)}`,
              fill: COLORS.prediction,
              fontSize: 10,
              position: i % 2 === 0 ? "top" : "insideTopRight",
            }}
          />
        ))}
        <Bar
          dataKey="count"
          fill="rgba(79,70,229,0.4)"
          stroke={COLORS.signal}
          strokeWidth={0.5}
          isAnimationActive={false}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
