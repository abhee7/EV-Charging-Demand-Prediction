import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { COLORS, axis, tooltipStyle } from "@/charts/theme";
import { num } from "@/lib/format";
import type { AcfPoint } from "@/types/api";

interface Props {
  points: AcfPoint[];
  selectedLag?: number | null;
  confidence?: number | null;
  height?: number;
}

const KEY_LAGS = new Set([1, 24, 168]);

export function AcfChart({ points, selectedLag, confidence, height = 320 }: Props) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={points} margin={{ top: 8, right: 8, bottom: 8, left: -12 }}>
        <CartesianGrid stroke={axis.stroke} vertical={false} />
        <XAxis
          dataKey="lag"
          stroke={axis.stroke}
          tick={axis.tick}
          minTickGap={24}
          label={{
            value: "Lag (hours)",
            position: "insideBottom",
            offset: -4,
            fill: COLORS.muted,
            fontSize: 11,
          }}
          height={40}
        />
        <YAxis stroke={axis.stroke} tick={axis.tick} width={54} domain={[-1, 1]} />
        <Tooltip
          {...tooltipStyle}
          cursor={{ fill: "rgba(17,24,39,0.04)" }}
          labelFormatter={(lag) => `Lag ${lag} h`}
          formatter={(value: number | string) => [num(Number(value), 4), "ACF"]}
        />
        {confidence != null && (
          <>
            <ReferenceLine y={confidence} stroke={COLORS.muted} strokeDasharray="3 3" />
            <ReferenceLine y={-confidence} stroke={COLORS.muted} strokeDasharray="3 3" />
          </>
        )}
        <Bar dataKey="value" isAnimationActive={false}>
          {points.map((point) => (
            <Cell
              key={point.lag}
              fill={
                point.lag === selectedLag
                  ? COLORS.prediction
                  : KEY_LAGS.has(point.lag)
                    ? COLORS.signal
                    : "rgba(17,24,39,0.18)"
              }
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
