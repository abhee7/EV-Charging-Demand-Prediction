import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useMemo } from "react";

import { COLORS, axis, tooltipStyle } from "@/charts/theme";
import { num } from "@/lib/format";
import type { ProfilePoint } from "@/types/api";

interface Props {
  points: ProfilePoint[];
  unit?: string;
  height?: number;
}

/** Mean demand by hour of day with an interquartile band. */
export function ProfileChart({ points, unit = "kWh/h", height = 300 }: Props) {
  const data = useMemo(
    () => points.map((p) => ({ ...p, band: [p.q1, p.q3] as [number, number] })),
    [points],
  );

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: -12 }}>
        <CartesianGrid stroke={axis.stroke} vertical={false} />
        <XAxis
          dataKey="hour"
          stroke={axis.stroke}
          tick={axis.tick}
          interval={1}
          label={{
            value: "Hour of day (America/Los_Angeles)",
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
          labelFormatter={(h) => `${String(h).padStart(2, "0")}:00`}
          formatter={(value: number | string | number[], name: string) => {
            if (Array.isArray(value)) {
              return [`${num(value[0], 2)} \u2013 ${num(value[1], 2)} ${unit}`, "IQR"];
            }
            return [`${num(Number(value), 2)} ${unit}`, name];
          }}
        />
        <Area
          dataKey="band"
          name="IQR"
          stroke="none"
          fill="rgba(79,70,229,0.12)"
          isAnimationActive={false}
        />
        <Line
          type="monotone"
          dataKey="mean"
          name="Mean"
          stroke={COLORS.signal}
          strokeWidth={2}
          dot={{ r: 2.5, fill: COLORS.signal, strokeWidth: 0 }}
          isAnimationActive={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
