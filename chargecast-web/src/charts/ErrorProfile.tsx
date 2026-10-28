import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { COLORS, axis, tooltipStyle } from "@/charts/theme";
import { num } from "@/lib/format";
import type { ForecastPoint } from "@/types/api";

interface Props {
  points: ForecastPoint[];
  unit?: string;
  height?: number;
}

/** Absolute error by horizon for one window. No uncertainty is implied. */
export function ErrorProfile({ points, unit = "kWh/h", height = 260 }: Props) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={points} margin={{ top: 8, right: 8, bottom: 8, left: -12 }}>
        <CartesianGrid stroke={axis.stroke} vertical={false} />
        <XAxis
          dataKey="horizon"
          stroke={axis.stroke}
          tick={axis.tick}
          label={{
            value: "Hours ahead",
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
          labelFormatter={(h) => `Horizon +${h} h`}
          formatter={(value: number | string) => [
            `${num(Number(value), 3)} ${unit}`,
            "Absolute error",
          ]}
        />
        <Bar
          dataKey="absoluteError"
          fill="rgba(234,88,12,0.55)"
          stroke={COLORS.prediction}
          strokeWidth={0.5}
          radius={[3, 3, 0, 0]}
          isAnimationActive={false}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
