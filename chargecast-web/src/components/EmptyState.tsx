import { FileWarning } from "lucide-react";

import type { Unavailable } from "@/types/api";

/** Any payload that may carry the API's unavailable fields. */
export type UnavailableLike = Partial<Omit<Unavailable, "available">> & {
  available?: boolean;
};

interface Props {
  /** The structured unavailable payload from the API, when there is one. */
  payload?: UnavailableLike | null;
  title?: string;
  message?: string;
}

/**
 * Research artefact unavailable.
 *
 * Never a fabricated chart: the panel names the artefact, its expected path
 * and, when the schema did not match, the expected and detected columns.
 */
export function EmptyState({ payload, title, message }: Props) {
  const heading = title ?? payload?.label ?? "Research artifact unavailable";
  const body =
    message ??
    payload?.reason ??
    "This view needs an artefact that is not present in the repository.";

  const rows: [string, string][] = [];
  if (payload?.path) rows.push(["Expected artifact", payload.path]);
  if (payload?.producedBy) rows.push(["Produced by", payload.producedBy]);
  if (payload?.expectedColumns?.length)
    rows.push(["Expected columns", payload.expectedColumns.join(", ")]);
  if (payload?.detectedColumns?.length)
    rows.push(["Detected columns", payload.detectedColumns.join(", ")]);
  if (payload?.missingColumns?.length)
    rows.push(["Missing", payload.missingColumns.join(", ")]);

  return (
    <div className="rounded-2xl border border-dashed border-signal/20 bg-signal/[0.02] p-6">
      <div className="mb-2 flex items-center gap-2">
        <FileWarning className="h-4 w-4 text-prediction" aria-hidden />
        <h3 className="font-display text-base font-semibold">{heading}</h3>
      </div>
      <p className="max-w-2xl text-sm leading-relaxed text-muted">{body}</p>

      {rows.length > 0 && (
        <dl className="mt-4 space-y-1.5 border-t border-black/[0.08] pt-3">
          {rows.map(([key, value]) => (
            <div key={key} className="flex flex-wrap gap-x-3 text-xs">
              <dt className="w-36 shrink-0 text-muted">{key}</dt>
              <dd className="break-all font-mono text-ink">{value}</dd>
            </div>
          ))}
        </dl>
      )}

      <p className="mt-4 text-xs text-muted">
        Place the verified project artifact at this path to enable this view. No
        values are substituted.
      </p>
    </div>
  );
}
