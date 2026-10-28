import type { InputHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export interface SliderProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  display?: string;
}

export function Slider({ className, label, display, id, ...props }: SliderProps) {
  const sliderId = id ?? label?.toLowerCase().replace(/\s+/g, "-");
  return (
    <label className="block" htmlFor={sliderId}>
      {(label || display) && (
        <span className="mb-2 flex items-baseline justify-between">
          {label && (
            <span className="text-2xs uppercase tracking-wider text-muted">{label}</span>
          )}
          {display && (
            <span className="tnum font-display text-sm font-semibold text-signal">
              {display}
            </span>
          )}
        </span>
      )}
      <input
        id={sliderId}
        type="range"
        className={cn(
          "h-1.5 w-full cursor-pointer appearance-none rounded-full bg-black/10",
          "[&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:w-4",
          "[&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full",
          "[&::-webkit-slider-thumb]:bg-signal [&::-webkit-slider-thumb]:shadow-glow",
          "[&::-moz-range-thumb]:h-4 [&::-moz-range-thumb]:w-4 [&::-moz-range-thumb]:rounded-full",
          "[&::-moz-range-thumb]:border-0 [&::-moz-range-thumb]:bg-signal",
          className,
        )}
        {...props}
      />
    </label>
  );
}
