import { useMemo } from "react";

import { heatColor } from "@/charts/theme";
import { num } from "@/lib/format";
import type { HeatmapCell } from "@/types/api";

interface Props {
  cells: HeatmapCell[];
  days: string[];
  min: number | null;
  max: number | null;
  unit?: string;
}

/**
 * Hour by day-of-week surface.
 *
 * Drawn as a CSS grid rather than pulling in a plotting library: the shape is
 * fixed at 7 x 24 and this keeps the chart bundle small and fully responsive.
 */
export function Heatmap({ cells, days, min, max, unit = "kWh/h" }: Props) {
  const lookup = useMemo(() => {
    const map = new Map<string, number | null>();
    for (const cell of cells) map.set(`${cell.day}:${cell.hour}`, cell.value);
    return map;
  }, [cells]);

  const lo = min ?? 0;
  const hi = max ?? 1;
  const span = hi - lo || 1;
  const hours = Array.from({ length: 24 }, (_, i) => i);

  return (
    <div className="overflow-x-auto">
      <div className="min-w-[640px]">
        <div className="grid grid-cols-[3rem_repeat(24,minmax(0,1fr))] gap-[2px]">
          <div />
          {hours.map((hour) => (
            <div key={hour} className="text-center text-2xs text-muted">
              {hour % 3 === 0 ? hour : ""}
            </div>
          ))}

          {days.map((day, dayIndex) => (
            <div key={day} className="contents">
              <div className="flex items-center pr-2 text-2xs text-muted">{day}</div>
              {hours.map((hour) => {
                const value = lookup.get(`${dayIndex}:${hour}`) ?? null;
                const t = value === null ? 0 : (value - lo) / span;
                return (
                  <div
                    key={`${day}-${hour}`}
                    title={
                      value === null
                        ? `${day} ${hour}:00 — no data`
                        : `${day} ${hour}:00 — ${num(value, 2)} ${unit}`
                    }
                    className="aspect-square rounded-[3px] transition-transform hover:scale-110 hover:ring-1 hover:ring-signal/50"
                    style={{
                      background: value === null ? "rgba(17,24,39,.04)" : heatColor(t),
                    }}
                  />
                );
              })}
            </div>
          ))}
        </div>

        <div className="mt-4 flex items-center gap-3 text-2xs text-muted">
          <span className="tnum">{num(lo, 1)}</span>
          <span
            className="h-2 flex-1 rounded-full"
            style={{
              background: `linear-gradient(90deg, ${heatColor(0)}, ${heatColor(0.35)}, ${heatColor(0.7)}, ${heatColor(1)})`,
            }}
          />
          <span className="tnum">
            {num(hi, 1)} {unit}
          </span>
        </div>
      </div>
    </div>
  );
}
