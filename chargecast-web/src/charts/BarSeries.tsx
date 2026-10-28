import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { COLORS, axis, tooltipStyle } from "@/charts/theme";
import { num } from "@/lib/format";

export interface BarSeriesSpec {
  key: string;
  name: string;
  color: string;
}

interface Props {
  data: Record<string, number | string | null>[];
  xKey: string;
  series: BarSeriesSpec[];
  unit?: string;
  height?: number;
  xLabel?: string;
}

/** Generic grouped bar chart used for weekday, monthly and paired comparisons. */
export function BarSeries({
  data,
  xKey,
  series,
  unit,
  height = 300,
  xLabel,
}: Props) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: -12 }}>
        <CartesianGrid stroke={axis.stroke} vertical={false} />
        <XAxis
          dataKey={xKey}
          stroke={axis.stroke}
          tick={axis.tick}
          height={xLabel ? 42 : 30}
          label={
            xLabel
              ? {
                  value: xLabel,
                  position: "insideBottom",
                  offset: -4,
                  fill: COLORS.muted,
                  fontSize: 11,
                }
              : undefined
          }
        />
        <YAxis stroke={axis.stroke} tick={axis.tick} width={54} />
        <Tooltip
          {...tooltipStyle}
          cursor={{ fill: "rgba(17,24,39,0.04)" }}
          formatter={(value: number | string, name: string) => [
            unit ? `${num(Number(value), 2)} ${unit}` : num(Number(value), 4),
            name,
          ]}
        />
        {series.length > 1 && (
          <Legend wrapperStyle={{ fontSize: 11, color: COLORS.muted }} />
        )}
        {series.map((s) => (
          <Bar
            key={s.key}
            dataKey={s.key}
            name={s.name}
            fill={s.color}
            radius={[3, 3, 0, 0]}
            isAnimationActive={false}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
