import { heatColor } from "@/charts/theme";
import { int } from "@/lib/format";

interface Props {
  truePositive: number;
  falsePositive: number;
  falseNegative: number;
  trueNegative: number;
  title?: string;
}

/** 2x2 peak-classification counts. Drawn directly; no plotting library needed. */
export function ConfusionMatrix({
  truePositive,
  falsePositive,
  falseNegative,
  trueNegative,
  title,
}: Props) {
  const cells = [
    { label: "Observed: not peak", forecast: "not peak", value: trueNegative },
    { label: "Observed: not peak", forecast: "peak", value: falsePositive },
    { label: "Observed: peak", forecast: "not peak", value: falseNegative },
    { label: "Observed: peak", forecast: "peak", value: truePositive },
  ];
  const max = Math.max(...cells.map((c) => c.value), 1);

  return (
    <div>
      {title && <p className="mb-3 text-sm text-muted">{title}</p>}
      <div className="grid grid-cols-[auto_1fr_1fr] gap-2 text-2xs">
        <div />
        <div className="pb-1 text-center text-muted">Forecast: not peak</div>
        <div className="pb-1 text-center text-muted">Forecast: peak</div>

        {["Observed: not peak", "Observed: peak"].map((row, rowIndex) => (
          <div key={row} className="contents">
            <div className="flex items-center pr-2 text-right text-muted">{row}</div>
            {["not peak", "peak"].map((forecast) => {
              const cell = cells[rowIndex * 2 + (forecast === "peak" ? 1 : 0)];
              return (
                <div
                  key={`${row}-${forecast}`}
                  className="flex h-20 items-center justify-center rounded-lg border border-black/[0.08]"
                  style={{ background: heatColor(cell.value / max) }}
                >
                  <span className="tnum font-display text-lg font-semibold text-ink">
                    {int(cell.value)}
                  </span>
                </div>
              );
            })}
          </div>
        ))}
      </div>
      <p className="mt-3 text-2xs text-muted">Counts are hours in the test period.</p>
    </div>
  );
}
