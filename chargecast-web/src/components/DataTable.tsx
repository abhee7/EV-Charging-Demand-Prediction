import { cn } from "@/lib/utils";

interface Props {
  columns: string[];
  rows: Record<string, unknown>[];
  className?: string;
  maxRows?: number;
  caption?: string;
}

function renderCell(value: unknown): string {
  if (value === null || value === undefined) return "\u2014";
  if (typeof value === "number") {
    return Number.isInteger(value)
      ? value.toLocaleString()
      : value.toLocaleString(undefined, { maximumFractionDigits: 6 });
  }
  return String(value);
}

/** Renders a stored table exactly as supplied. No column is reordered or hidden. */
export function DataTable({ columns, rows, className, maxRows, caption }: Props) {
  const visible = maxRows ? rows.slice(0, maxRows) : rows;

  return (
    <div className={cn("overflow-x-auto rounded-xl border border-black/[0.08]", className)}>
      <table className="w-full min-w-[520px] border-collapse text-sm">
        <thead>
          <tr className="border-b border-black/[0.08] bg-black/[0.02]">
            {columns.map((column) => (
              <th
                key={column}
                scope="col"
                className="whitespace-nowrap px-3 py-2.5 text-left text-2xs font-medium uppercase tracking-wider text-muted"
              >
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {visible.map((row, index) => (
            <tr
              key={index}
              className="border-b border-black/[0.06] transition-colors last:border-0 hover:bg-black/[0.02]"
            >
              {columns.map((column) => (
                <td key={column} className="tnum whitespace-nowrap px-3 py-2.5">
                  {renderCell(row[column])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {caption && <p className="px-3 py-2 text-2xs text-muted">{caption}</p>}
    </div>
  );
}
