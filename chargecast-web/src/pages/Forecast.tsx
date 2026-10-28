import { useEffect, useState } from "react";

import { endpoints } from "@/api/endpoints";
import { ErrorProfile } from "@/charts/ErrorProfile";
import { ForecastChart } from "@/charts/ForecastChart";
import { HorizonChart } from "@/charts/HorizonChart";
import { DataTable } from "@/components/DataTable";
import { PageHeader } from "@/components/PageHeader";
import { QueryBoundary } from "@/components/QueryBoundary";
import { SectionHeading } from "@/components/SectionHeading";
import { StatTile } from "@/components/StatTile";
import { Card, CardHint, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { useApi } from "@/hooks/useApi";
import { dateTimeLabel, energy, num, rate } from "@/lib/format";
import type {
  ForecastModels,
  ForecastWindowDetail,
  ForecastWindows,
  HorizonResponse,
  MetricKey,
} from "@/types/api";

const HORIZON_CHOICES = [6, 12, 24];

export default function Forecast() {
  const [set, setSet] = useState("primary");
  const [model, setModel] = useState("");
  const [windowId, setWindowId] = useState<number | null>(null);
  const [horizon, setHorizon] = useState(24);
  const [metric, setMetric] = useState<MetricKey>("mae");

  const models = useApi<ForecastModels>(endpoints.forecastModels, {
    prediction_set: set,
  });
  const activeModel = model || models.data?.models?.[0] || "";

  const windows = useApi<ForecastWindows>(
    endpoints.forecastWindows,
    { prediction_set: set, model: activeModel },
    { skip: !activeModel },
  );

  // Default to the most recent stored window whenever the selection changes.
  useEffect(() => {
    const list = windows.data?.windows;
    if (list?.length) setWindowId(list[list.length - 1].id);
  }, [windows.data]);

  const detail = useApi<ForecastWindowDetail>(
    windowId ? endpoints.forecastWindow(windowId) : null,
    { model: activeModel, prediction_set: set, horizon },
    { skip: !windowId || !activeModel },
  );

  const horizonMetrics = useApi<HorizonResponse>(endpoints.modelHorizon, {
    metric,
  });

  return (
    <div>
      <PageHeader
        title="Forecast"
        lede="Day-ahead replay across the held-out test period"
        meta="Stored predictions only — no model is loaded and no inference runs here"
      />

      <Card>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Select
            label="Prediction set"
            value={set}
            onChange={(e) => {
              setSet(e.target.value);
              setModel("");
              setWindowId(null);
            }}
          >
            {(models.data?.sets ?? [{ key: "primary", label: "Primary target", available: true, path: "" }])
              .filter((s) => s.available)
              .map((s) => (
                <option key={s.key} value={s.key}>
                  {s.label}
                </option>
              ))}
          </Select>

          <Select
            label="Model"
            value={activeModel}
            onChange={(e) => setModel(e.target.value)}
          >
            {(models.data?.models ?? []).map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </Select>

          <Select
            label="Forecast window"
            value={windowId ?? ""}
            onChange={(e) => setWindowId(Number(e.target.value))}
            hint={`${windows.data?.count ?? 0} stored windows`}
          >
            {(windows.data?.windows ?? []).map((w) => (
              <option key={w.id} value={w.id}>
                {w.origin ? `${w.label} · ${dateTimeLabel(w.origin)}` : w.label}
              </option>
            ))}
          </Select>

          <Select
            label="Horizon"
            value={horizon}
            onChange={(e) => setHorizon(Number(e.target.value))}
          >
            {HORIZON_CHOICES.map((h) => (
              <option key={h} value={h}>
                1 – {h} hours
              </option>
            ))}
          </Select>
        </div>
      </Card>

      <SectionHeading
        title="Actual against prediction"
        hint="Observed in indigo, forecast in orange"
      />
      <Card>
        <QueryBoundary
          loading={detail.loading}
          error={detail.error}
          data={detail.data}
          height={360}
        >
          {(data) => (
            <>
              <ForecastChart points={data.points} unit={data.unit} />
              <p className="mt-2 text-xs text-muted">
                Background bands mark morning, afternoon and evening in
                America/Los_Angeles. No uncertainty interval is shown: the
                stored outputs are point forecasts.
              </p>
            </>
          )}
        </QueryBoundary>
      </Card>

      <QueryBoundary
        loading={detail.loading}
        error={detail.error}
        data={detail.data}
        height={100}
      >
        {(data) => (
          <>
            <SectionHeading title="Forecast summary" hint="This window only" />
            <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
              <StatTile label="MAE" value={num(data.stats.mae, 4)} />
              <StatTile label="RMSE" value={num(data.stats.rmse, 4)} />
              <StatTile label="R²" value={num(data.stats.r2, 4)} />
              <StatTile
                label="Observed total"
                value={energy(data.stats.observedTotal, 1)}
              />
              <StatTile
                label="Predicted total"
                value={energy(data.stats.predictedTotal, 1)}
              />
              <StatTile
                label="Observed peak"
                value={rate(data.stats.observedPeak)}
              />
            </div>
            <div className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-3">
              <StatTile
                label="Predicted peak"
                value={rate(data.stats.predictedPeak)}
              />
              <StatTile
                label="Forecast origin"
                value={data.origin ? dateTimeLabel(data.origin) : "—"}
              />
              <StatTile label="Horizons shown" value={String(data.points.length)} />
            </div>

            <SectionHeading
              title="Forecast error profile"
              hint="Absolute error by horizon for this window"
            />
            <Card>
              <ErrorProfile points={data.points} unit={data.unit} />
              <p className="mt-2 text-xs text-muted">
                Error at a longer horizon reflects how much observed history was
                available at the forecast origin. It is not by itself evidence
                that a model performs poorly.
              </p>
            </Card>

            <SectionHeading title="Horizon detail" hint="Every stored step" />
            <DataTable
              columns={["Horizon", "Target hour (UTC)", "Actual", "Prediction", "Absolute error"]}
              rows={data.points.map((p) => ({
                Horizon: p.horizon,
                "Target hour (UTC)": p.timestamp ? dateTimeLabel(p.timestamp) : "—",
                Actual: p.actual,
                Prediction: p.prediction,
                "Absolute error": p.absoluteError,
              }))}
              caption={`Values in ${data.unit}, read from ${data.source}.`}
            />
          </>
        )}
      </QueryBoundary>

      <SectionHeading
        title="Error across all horizons"
        hint="Pooled over the whole test period, every model"
      />
      <Card>
        <CardTitle>Horizon 1 → 24</CardTitle>
        <CardHint className="mb-3">
          Select the metric used for the horizon curve
        </CardHint>
        <div className="mb-4 max-w-xs">
          <Select
            label="Metric"
            value={metric}
            onChange={(e) => setMetric(e.target.value as MetricKey)}
          >
            {(horizonMetrics.data?.availableMetrics ?? ["mae", "rmse"]).map((m) => (
              <option key={m} value={m}>
                {m.toUpperCase()}
              </option>
            ))}
          </Select>
        </div>
        <QueryBoundary
          loading={horizonMetrics.loading}
          error={horizonMetrics.error}
          data={horizonMetrics.data}
          height={320}
        >
          {(data) => (
            <>
              <HorizonChart
                series={data.series ?? []}
                label={data.label ?? "MAE"}
                unit={data.unit}
              />
              {data.note && <p className="mt-2 text-xs text-muted">{data.note}</p>}
            </>
          )}
        </QueryBoundary>
      </Card>
    </div>
  );
}
