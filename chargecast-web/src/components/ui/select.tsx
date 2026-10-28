import { ChevronDown } from "lucide-react";
import type { SelectHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  hint?: string;
}

export function Select({ className, label, hint, id, ...props }: SelectProps) {
  const selectId = id ?? label?.toLowerCase().replace(/\s+/g, "-");
  return (
    <label className="block" htmlFor={selectId}>
      {label && (
        <span className="mb-1.5 block text-2xs uppercase tracking-wider text-muted">
          {label}
        </span>
      )}
      <span className="relative block">
        <select
          id={selectId}
          className={cn(
            "h-9 w-full appearance-none rounded-lg border border-black/10 bg-elevated pl-3 pr-9 text-sm text-ink",
            "transition-colors hover:border-signal/25 focus:border-signal/40",
            className,
          )}
          {...props}
        />
        <ChevronDown
          aria-hidden
          className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted"
        />
      </span>
      {hint && <span className="mt-1 block text-2xs text-muted">{hint}</span>}
    </label>
  );
}
