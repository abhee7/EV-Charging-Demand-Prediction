import { ShieldCheck, FlaskConical } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface Props {
  kind: "audited" | "exploratory";
  note?: string;
  className?: string;
}

/**
 * Marks a panel as either the verified research artefact or an in-dashboard
 * recomputation. The two are always visually distinct.
 */
export function ProvenanceNote({ kind, note, className }: Props) {
  const audited = kind === "audited";
  const Icon = audited ? ShieldCheck : FlaskConical;

  return (
    <div
      className={cn(
        "flex flex-wrap items-start gap-3 rounded-xl border p-3.5",
        audited
          ? "border-signal/20 bg-signal/[0.05]"
          : "border-prediction/20 bg-prediction/[0.05]",
        className,
      )}
    >
      <Icon
        aria-hidden
        className={cn(
          "mt-0.5 h-4 w-4 shrink-0",
          audited ? "text-signal" : "text-prediction",
        )}
      />
      <div className="min-w-0 flex-1 space-y-1.5">
        <Badge tone={audited ? "signal" : "prediction"}>
          {audited
            ? "SOURCE: VERIFIED RESEARCH ARTIFACT"
            : "EXPLORATORY \u2014 NOT THE AUDITED RESULT"}
        </Badge>
        {note && <p className="text-xs leading-relaxed text-muted">{note}</p>}
      </div>
    </div>
  );
}
