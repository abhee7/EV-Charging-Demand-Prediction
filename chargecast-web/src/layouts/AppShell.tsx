import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import {
  Activity,
  ArrowUpRight,
  Circle,
  CircleDot,
  Grid2x2,
  PanelLeftClose,
  PanelLeftOpen,
  PieChart,
  Repeat,
  TrendingUp,
  Waves,
} from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { useHealth } from "@/hooks/useHealth";
import { cn } from "@/lib/utils";

interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  end?: boolean;
}

const NAV: NavItem[] = [
  { to: "/", label: "Overview", icon: CircleDot, end: true },
  { to: "/forecast", label: "Forecast", icon: ArrowUpRight },
  { to: "/model-lab", label: "Model Lab", icon: Grid2x2 },
  { to: "/analytics", label: "Demand Analytics", icon: Waves },
  { to: "/peak", label: "Peak Intelligence", icon: TrendingUp },
  { to: "/explainability", label: "Explainability", icon: PieChart },
  { to: "/robustness", label: "Robustness", icon: Repeat },
  { to: "/research", label: "Research", icon: Circle },
];

function ApiStatus() {
  const { status, health } = useHealth();

  const tone =
    status === "online"
      ? "border-signal/25 bg-signal/[0.08] text-signal"
      : status === "offline"
        ? "border-rose/25 bg-rose/[0.08] text-rose"
        : "border-black/10 bg-black/[0.04] text-muted";

  const dot =
    status === "online" ? "bg-signal" : status === "offline" ? "bg-rose" : "bg-muted";

  const label =
    status === "online"
      ? "API CONNECTED"
      : status === "offline"
        ? "API OFFLINE"
        : "CHECKING API";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-full border px-2.5 py-1 text-2xs tracking-wider",
        tone,
      )}
      title={
        health
          ? `${health.artifactsAvailable}/${health.artifactsTotal} artefacts available`
          : undefined
      }
    >
      <span className={cn("h-1.5 w-1.5 rounded-full animate-pulse-dot", dot)} />
      {label}
    </span>
  );
}

export function AppShell() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const reduced = useReducedMotion();
  const { health } = useHealth();

  // Collapse by default on narrow viewports.
  useEffect(() => {
    const query = window.matchMedia("(max-width: 1024px)");
    const apply = () => setCollapsed(query.matches);
    apply();
    query.addEventListener("change", apply);
    return () => query.removeEventListener("change", apply);
  }, []);

  return (
    <div className="flex min-h-screen">
      <aside
        className={cn(
          "sticky top-0 z-20 flex h-screen shrink-0 flex-col border-r border-black/[0.08] bg-white transition-[width] duration-200",
          collapsed ? "w-[68px]" : "w-60",
        )}
      >
        <div className="flex items-center gap-2 px-4 py-5">
          {!collapsed && (
            <div className="min-w-0">
              <p className="truncate font-display text-lg font-bold tracking-tight">
                Charge<span className="text-signal">Cast</span>
              </p>
              <p className="truncate text-2xs text-muted">EV demand intelligence</p>
            </div>
          )}
          <button
            type="button"
            onClick={() => setCollapsed((v) => !v)}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-expanded={!collapsed}
            className="ml-auto rounded-lg border border-transparent p-1.5 text-muted transition-colors hover:border-black/10 hover:bg-black/[0.04] hover:text-ink"
          >
            {collapsed ? (
              <PanelLeftOpen className="h-4 w-4" />
            ) : (
              <PanelLeftClose className="h-4 w-4" />
            )}
          </button>
        </div>

        <nav className="flex-1 space-y-0.5 px-2" aria-label="Primary">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              title={collapsed ? label : undefined}
              className={({ isActive }) =>
                cn(
                  "group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                  isActive
                    ? "bg-signal/[0.10] text-signal"
                    : "text-muted hover:bg-black/[0.04] hover:text-ink",
                )
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <span
                      aria-hidden
                      className="absolute inset-y-1.5 left-0 w-0.5 rounded-full bg-signal"
                    />
                  )}
                  <Icon className="h-4 w-4 shrink-0" aria-hidden />
                  {!collapsed && <span className="truncate">{label}</span>}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {!collapsed && (
          <div className="border-t border-black/[0.08] px-4 py-4 text-2xs leading-relaxed text-muted">
            Read-only view of the verified research outputs. Nothing is
            retrained and no artefact is modified.
          </div>
        )}
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 border-b border-black/[0.08] bg-canvas/85 backdrop-blur">
          <div className="mx-auto flex max-w-[1600px] flex-wrap items-center gap-x-6 gap-y-2 px-5 py-3.5">
            <div>
              <p className="font-display text-base font-bold tracking-[0.06em]">
                CHARGE<span className="text-signal">CAST</span>
              </p>
              <p className="text-2xs tracking-[0.14em] text-muted">
                EV DEMAND INTELLIGENCE
              </p>
            </div>

            <div className="ml-auto flex flex-wrap items-center gap-x-6 gap-y-2">
              <div className="hidden sm:block">
                <p className="text-2xs text-muted">Dataset</p>
                <p className="text-sm font-semibold">Caltech ACN</p>
              </div>
              <div className="hidden md:block">
                <p className="text-2xs text-muted">Artefacts</p>
                <p className="tnum text-sm font-semibold">
                  {health
                    ? `${health.artifactsAvailable}/${health.artifactsTotal}`
                    : "\u2014"}
                </p>
              </div>
              <div className="hidden lg:block">
                <p className="text-2xs text-muted">Mode</p>
                <p className="flex items-center gap-1.5 text-sm font-semibold">
                  <Activity className="h-3.5 w-3.5 text-signal" aria-hidden />
                  Historical dataset
                </p>
              </div>
              <ApiStatus />
            </div>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[1600px] flex-1 px-5 py-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={reduced ? false : { opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={reduced ? undefined : { opacity: 0, y: -4 }}
              transition={{ duration: 0.22 }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>

        <footer className="border-t border-black/[0.08] px-5 py-5">
          <div className="mx-auto flex max-w-[1600px] flex-wrap items-center gap-x-6 gap-y-1 text-2xs text-muted">
            <span className="font-display text-sm font-semibold text-ink">
              ChargeCast
            </span>
            <span>Research dashboard</span>
            <span>Caltech ACN</span>
            <span className="ml-auto">2026</span>
          </div>
        </footer>
      </div>
    </div>
  );
}
