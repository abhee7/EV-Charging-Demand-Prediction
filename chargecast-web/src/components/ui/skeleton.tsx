import type { CSSProperties } from "react";

import { cn } from "@/lib/utils";

export function Skeleton({
  className,
  style,
}: {
  className?: string;
  style?: CSSProperties;
}) {
  return (
    <div
      className={cn("animate-pulse rounded-lg bg-black/[0.05]", className)}
      style={style}
      aria-hidden
    />
  );
}

/** Placeholder sized to the chart it replaces, so the layout does not jump. */
export function ChartSkeleton({ height = 280 }: { height?: number }) {
  return <Skeleton className="w-full" style={{ height }} />;
}
