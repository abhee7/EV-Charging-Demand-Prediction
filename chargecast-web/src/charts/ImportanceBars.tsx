import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { COLORS, axis, tooltipStyle } from "@/charts/theme";
import { num } from "@/lib/format";
import type { FeatureAttribution } from "@/types/api";

interface Props {
  features: FeatureAttribution[];
  color?: string;
  valueLabel?: string;
  topN?: number;
  selected?: string | null;
  onSelect?: (feature: string) => void;
  height?: number;
}

export function ImportanceBars({
  features,
  color = COLORS.signal,
  valueLabel = "Mean |SHAP|",
  topN = 17,
  selected,
  onSelect,
  height,
}: Props) {
  const data = features.slice(0, topN).slice().reverse();
  const chartHeight = height ?? Math.max(280, data.length * 26);

  return (
    <ResponsiveContainer width="100%" height={chartHeight}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 4, right: 16, bottom: 4, left: 8 }}
      >
        <CartesianGrid stroke={axis.stroke} horizontal={false} />
        <XAxis type="number" stroke={axis.stroke} tick={axis.tick} />
        <YAxis
          type="category"
          dataKey="feature"
          stroke={axis.stroke}
          tick={{ ...axis.tick, fontSize: 11 }}
          width={124}
        />
        <Tooltip
          {...tooltipStyle}
          cursor={{ fill: "rgba(17,24,39,0.04)" }}
          formatter={(value: number | string) => [num(Number(value), 6), valueLabel]}
        />
        <Bar
          dataKey="value"
          radius={[0, 3, 3, 0]}
          isAnimationActive={false}
          onClick={(entry: unknown) => {
            const row = entry as { feature?: string };
            if (row?.feature && onSelect) onSelect(row.feature);
          }}
          cursor={onSelect ? "pointer" : undefined}
        >
          {data.map((row) => (
            <Cell
              key={row.feature}
              fill={row.feature === selected ? COLORS.prediction : color}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
