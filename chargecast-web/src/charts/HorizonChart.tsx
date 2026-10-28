import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useMemo } from "react";

import { COLORS, axis, modelColor, tooltipStyle } from "@/charts/theme";
import { num } from "@/lib/format";
import type { HorizonSeries } from "@/types/api";

interface Props {
  series: HorizonSeries[];
  label: string;
  unit?: string;
  height?: number;
}

export function HorizonChart({ series, label, unit, height = 320 }: Props) {
  const valueLabel = unit ? `${label} (${unit})` : label;
  const data = useMemo(() => {
    const byHorizon = new Map<number, Record<string, number>>();
    for (const s of series) {
      for (const point of s.points) {
        const row = byHorizon.get(point.horizon) ?? { horizon: point.horizon };
        row[s.model] = point.value;
        byHorizon.set(point.horizon, row);
      }
    }
    return [...byHorizon.values()].sort((a, b) => a.horizon - b.horizon);
  }, [series]);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: -12 }}>
        <CartesianGrid stroke={axis.stroke} vertical={false} />
        <XAxis
          dataKey="horizon"
          stroke={axis.stroke}
          tick={axis.tick}
          label={{
            value: "Forecast horizon (hours ahead)",
            position: "insideBottom",
            offset: -4,
            fill: COLORS.muted,
            fontSize: 11,
          }}
          height={40}
        />
        <YAxis
          stroke={axis.stroke}
          tick={axis.tick}
          width={54}
          label={{
            value: valueLabel,
            angle: -90,
            position: "insideLeft",
            fill: COLORS.muted,
            fontSize: 11,
            dy: 30,
          }}
        />
        <Tooltip
          {...tooltipStyle}
          labelFormatter={(h) => `Horizon +${h} h`}
          formatter={(value: number | string, name: string) => [
            unit ? `${num(Number(value), 4)} ${unit}` : num(Number(value), 4),
            name,
          ]}
        />
        <Legend wrapperStyle={{ fontSize: 11, color: COLORS.muted }} iconType="plainline" />
        {series.map((s, i) => (
          <Line
            key={s.model}
            type="monotone"
            dataKey={s.model}
            name={s.model}
            stroke={modelColor(s.model, i)}
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
