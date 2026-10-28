import { Info } from "lucide-react";

interface Props {
  title?: string;
  children: React.ReactNode;
}

/** Research-information panel used for limitations and caveats. */
export function ResearchNote({ title, children }: Props) {
  return (
    <div className="flex gap-3 rounded-xl border-l-2 border-prediction bg-prediction/[0.05] p-4">
      <Info className="mt-0.5 h-4 w-4 shrink-0 text-prediction" aria-hidden />
      <div className="min-w-0 text-sm leading-relaxed">
        {title && <span className="font-semibold text-prediction">{title} </span>}
        <span className="text-ink/90">{children}</span>
      </div>
    </div>
  );
}
