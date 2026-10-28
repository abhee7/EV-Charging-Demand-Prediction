import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

const badge = cva(
  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-2xs font-medium tracking-wide",
  {
    variants: {
      tone: {
        neutral: "border-black/10 bg-black/[0.04] text-muted",
        signal: "border-signal/25 bg-signal/[0.08] text-signal",
        prediction: "border-prediction/25 bg-prediction/[0.08] text-prediction",
        violet: "border-violet/25 bg-violet/[0.08] text-violet",
        rose: "border-rose/25 bg-rose/[0.08] text-rose",
      },
    },
    defaultVariants: { tone: "neutral" },
  },
);

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badge> {}

export function Badge({ className, tone, ...props }: BadgeProps) {
  return <span className={cn(badge({ tone }), className)} {...props} />;
}
