import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useMemo } from "react";

import { COLORS, axis, tooltipStyle } from "@/charts/theme";
import { num } from "@/lib/format";
import type { ForecastPoint } from "@/types/api";

interface Props {
  points: ForecastPoint[];
  unit?: string;
  height?: number;
  showDayparts?: boolean;
}

const DAYPARTS: [number, number, string, string][] = [
  [6, 12, "Morning", "rgba(79,70,229,0.05)"],
  [12, 18, "Afternoon", "rgba(234,88,12,0.05)"],
  [18, 23, "Evening", "rgba(124,108,242,0.05)"],
];

/** Observed against forecast for one stored 24-hour window. */
export function ForecastChart({
  points,
  unit = "kWh/h",
  height = 360,
  showDayparts = true,
}: Props) {
  const bands = useMemo(() => {
    if (!showDayparts) return [];
    return DAYPARTS.flatMap(([from, to, label, fill]) => {
      const inside = points.filter(
        (p) => p.localHour != null && p.localHour >= from && p.localHour < to,
      );
      if (inside.length === 0) return [];
      return [
        {
          x1: inside[0].horizon - 0.5,
          x2: inside[inside.length - 1].horizon + 0.5,
          label,
          fill,
        },
      ];
    });
  }, [points, showDayparts]);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={points} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
        <CartesianGrid stroke={axis.stroke} vertical={false} />
        {bands.map((band) => (
          <ReferenceArea
            key={band.label}
            x1={band.x1}
            x2={band.x2}
            fill={band.fill}
            stroke="none"
            label={{ value: band.label, fill: COLORS.muted, fontSize: 10, position: "insideTop" }}
          />
        ))}
        <XAxis
          dataKey="horizon"
          stroke={axis.stroke}
          tick={axis.tick}
          label={{
            value: "Hours ahead of forecast origin",
            position: "insideBottom",
            offset: -2,
            fill: COLORS.muted,
            fontSize: 11,
          }}
          height={42}
        />
        <YAxis stroke={axis.stroke} tick={axis.tick} width={54} />
        <Tooltip
          {...tooltipStyle}
          labelFormatter={(h) => `Horizon +${h} h`}
          formatter={(value: number | string, name: string) => [
            `${num(Number(value), 2)} ${unit}`,
            name,
          ]}
        />
        <Legend
          wrapperStyle={{ fontSize: 11, color: COLORS.muted, paddingTop: 6 }}
          iconType="plainline"
        />
        <Bar
          dataKey="actual"
          name="Observed"
          fill="rgba(79,70,229,0.26)"
          stroke={COLORS.signal}
          strokeWidth={1}
          isAnimationActive={false}
        />
        <Line
          type="monotone"
          dataKey="prediction"
          name="Forecast"
          stroke={COLORS.prediction}
          strokeWidth={2.2}
          dot={{ r: 3, fill: COLORS.prediction, strokeWidth: 0 }}
          isAnimationActive={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
