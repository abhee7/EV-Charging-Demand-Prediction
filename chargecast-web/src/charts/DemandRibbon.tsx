import {
  Area,
  AreaChart,
  Brush,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useMemo } from "react";

import { COLORS, axis, tooltipStyle } from "@/charts/theme";
import { dateTimeLabel, num } from "@/lib/format";
import type { DemandPoint } from "@/types/api";

interface Props {
  points: DemandPoint[];
  peakThreshold?: number | null;
  unit?: string;
  height?: number;
}

/** The signature visualisation: reconstructed demand over the full series. */
export function DemandRibbon({
  points,
  peakThreshold,
  unit = "kWh/h",
  height = 340,
}: Props) {
  const data = useMemo(
    () => points.map((p) => ({ t: p.t, value: p.v, ms: Date.parse(p.t) })),
    [points],
  );

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
        <defs>
          <linearGradient id="ribbonFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={COLORS.signal} stopOpacity={0.34} />
            <stop offset="100%" stopColor={COLORS.signal} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={axis.stroke} vertical={false} />
        <XAxis
          dataKey="ms"
          type="number"
          scale="time"
          domain={["dataMin", "dataMax"]}
          tickFormatter={(ms: number) =>
            new Date(ms).toLocaleDateString(undefined, {
              month: "short",
              year: "2-digit",
            })
          }
          stroke={axis.stroke}
          tick={axis.tick}
          minTickGap={48}
        />
        <YAxis
          stroke={axis.stroke}
          tick={axis.tick}
          width={54}
          label={{
            value: unit,
            angle: -90,
            position: "insideLeft",
            fill: COLORS.muted,
            fontSize: 11,
            dy: 24,
          }}
        />
        <Tooltip
          {...tooltipStyle}
          labelFormatter={(ms) => dateTimeLabel(new Date(Number(ms)).toISOString())}
          formatter={(value: number | string) => [
            `${num(Number(value), 2)} ${unit}`,
            "Observed",
          ]}
        />
        {peakThreshold != null && (
          <ReferenceLine
            y={peakThreshold}
            stroke={COLORS.prediction}
            strokeDasharray="4 4"
            strokeWidth={1}
            label={{
              value: `P90 ${num(peakThreshold, 1)}`,
              fill: COLORS.prediction,
              fontSize: 10,
              position: "right",
            }}
          />
        )}
        <Area
          type="monotone"
          dataKey="value"
          stroke={COLORS.signal}
          strokeWidth={1.3}
          fill="url(#ribbonFill)"
          isAnimationActive={false}
          connectNulls={false}
        />
        <Brush
          dataKey="ms"
          height={26}
          travellerWidth={8}
          stroke={COLORS.signal}
          fill="rgba(79,70,229,0.06)"
          tickFormatter={() => ""}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
