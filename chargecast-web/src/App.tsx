import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "@/layouts/AppShell";
import { ChartSkeleton } from "@/components/ui/skeleton";

// Pages are code-split so the first paint does not carry every chart.
const Overview = lazy(() => import("@/pages/Overview"));
const Forecast = lazy(() => import("@/pages/Forecast"));
const ModelLab = lazy(() => import("@/pages/ModelLab"));
const Analytics = lazy(() => import("@/pages/Analytics"));
const Peak = lazy(() => import("@/pages/Peak"));
const Explainability = lazy(() => import("@/pages/Explainability"));
const Robustness = lazy(() => import("@/pages/Robustness"));
const Research = lazy(() => import("@/pages/Research"));

function PageFallback() {
  return (
    <div className="space-y-4">
      <ChartSkeleton height={72} />
      <ChartSkeleton height={320} />
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route
          index
          element={
            <Suspense fallback={<PageFallback />}>
              <Overview />
            </Suspense>
          }
        />
        <Route
          path="forecast"
          element={
            <Suspense fallback={<PageFallback />}>
              <Forecast />
            </Suspense>
          }
        />
        <Route
          path="model-lab"
          element={
            <Suspense fallback={<PageFallback />}>
              <ModelLab />
            </Suspense>
          }
        />
        <Route
          path="analytics"
          element={
            <Suspense fallback={<PageFallback />}>
              <Analytics />
            </Suspense>
          }
        />
        <Route
          path="peak"
          element={
            <Suspense fallback={<PageFallback />}>
              <Peak />
            </Suspense>
          }
        />
        <Route
          path="explainability"
          element={
            <Suspense fallback={<PageFallback />}>
              <Explainability />
            </Suspense>
          }
        />
        <Route
          path="robustness"
          element={
            <Suspense fallback={<PageFallback />}>
              <Robustness />
            </Suspense>
          }
        />
        <Route
          path="research"
          element={
            <Suspense fallback={<PageFallback />}>
              <Research />
            </Suspense>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
