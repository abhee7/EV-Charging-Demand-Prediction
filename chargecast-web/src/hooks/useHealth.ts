import { useEffect, useState } from "react";

import { apiGet } from "@/api/client";
import { endpoints } from "@/api/endpoints";
import type { Health } from "@/types/api";

export type HealthState = "checking" | "online" | "offline";

/** Polls /api/health. The indicator reflects the real response, never a guess. */
export function useHealth(intervalMs = 30_000) {
  const [status, setStatus] = useState<HealthState>("checking");
  const [health, setHealth] = useState<Health | null>(null);

  useEffect(() => {
    let cancelled = false;

    const check = async () => {
      try {
        const data = await apiGet<Health>(endpoints.health);
        if (cancelled) return;
        setHealth(data);
        setStatus("online");
      } catch {
        if (cancelled) return;
        setHealth(null);
        setStatus("offline");
      }
    };

    void check();
    const timer = window.setInterval(() => void check(), intervalMs);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [intervalMs]);

  return { status, health };
}
