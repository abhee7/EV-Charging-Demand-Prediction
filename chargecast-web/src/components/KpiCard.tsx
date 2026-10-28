import { motion, useReducedMotion } from "framer-motion";
import { useEffect, useState } from "react";

import { cn } from "@/lib/utils";

interface Props {
  label: string;
  value: string;
  sub?: string;
  accent?: "signal" | "prediction" | "none";
  /** Numeric value to count up to. Omit for non-numeric values. */
  countTo?: number | null;
  format?: (value: number) => string;
  delay?: number;
}

function useCountUp(target: number | null | undefined, enabled: boolean) {
  const [value, setValue] = useState(enabled && target != null ? 0 : target ?? 0);

  useEffect(() => {
    if (!enabled || target == null) {
      setValue(target ?? 0);
      return;
    }
    const duration = 620;
    const start = performance.now();
    let frame = 0;

    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      // ease-out cubic
      setValue(target * (1 - Math.pow(1 - t, 3)));
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target, enabled]);

  return value;
}

export function KpiCard({
  label,
  value,
  sub,
  accent = "none",
  countTo,
  format,
  delay = 0,
}: Props) {
  const reduced = useReducedMotion();
  const animate = !reduced && countTo != null && !!format;
  const counted = useCountUp(countTo, animate);

  return (
    <motion.div
      initial={reduced ? false : { opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.28, delay }}
      className="glass relative overflow-hidden p-4 transition-colors hover:border-signal/20"
    >
      <span
        aria-hidden
        className="absolute inset-x-4 top-0 h-px bg-gradient-to-r from-signal/70 to-transparent"
      />
      <p className="text-2xs uppercase tracking-wider text-muted">{label}</p>
      <p
        className={cn(
          "tnum mt-2 font-display text-2xl font-semibold leading-none",
          accent === "signal" && "text-signal",
          accent === "prediction" && "text-prediction",
        )}
      >
        {animate && format ? format(counted) : value}
      </p>
      {sub && <p className="mt-1.5 text-xs text-muted">{sub}</p>}
    </motion.div>
  );
}
