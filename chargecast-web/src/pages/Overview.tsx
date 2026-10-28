import { useMemo, useState } from "react";

import { endpoints } from "@/api/endpoints";
import { BarSeries } from "@/charts/BarSeries";
import { COLORS } from "@/charts/theme";
import { DemandRibbon } from "@/charts/DemandRibbon";
import { ForecastChart } from "@/charts/ForecastChart";
import { ProfileChart } from "@/charts/ProfileChart";
import { KpiCard } from "@/components/KpiCard";
import { PageHeader } from "@/components/PageHeader";
import { QueryBoundary } from "@/components/QueryBoundary";
import { ResearchNote } from "@/components/ResearchNote";
import { SectionHeading } from "@/components/SectionHeading";
import { StatTile } from "@/components/StatTile";
import { Card, CardHint, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { useApi } from "@/hooks/useApi";
import { dateLabel, energy, int, num, rate, ratio } from "@/lib/format";
import type {
  ArtifactsResponse,
  DemandProfile,
  ForecastWindowDetail,
  ForecastWindows,
  HourlyDemand,
  Overview as OverviewData,
  WeekdaySplit,
} from "@/types/api";

export default function Overview() {
  const overview = useApi<OverviewData>(endpoints.overview);
  const hourly = useApi<HourlyDemand>(endpoints.demandHourly, { downsample: 2 });
  const profile = useApi<DemandProfile>(endpoints.demandProfile);
  const weekday = useApi<WeekdaySplit>(endpoints.demandWeekday);
  const artifacts = useApi<ArtifactsResponse>(endpoints.artifacts);

  const models = overview.data?.forecast?.models ?? [];
  const [model, setModel] = useState<string>("");
  const activeModel = model || models[0] || "";

  const windows = useApi<ForecastWindows>(
    endpoints.forecastWindows,
    { model: activeModel },
    { skip: !activeModel },
  );
  const latestWindow = windows.data?.windows?.at(-1)?.id;
  const detail = useApi<ForecastWindowDetail>(
    latestWindow ? endpoints.forecastWindow(latestWindow) : null,
    { model: activeModel },
    { skip: !latestWindow || !activeModel },
  );

  const artifactHealth = useMemo(() => {
    const rows = artifacts.data?.artifacts ?? [];
    return {
      available: rows.filter((r) => r.status === "available").length,
      missing: rows.filter((r) => r.status === "missing").length,
      optional: rows.filter((r) => r.status === "optional").length,
      total: rows.length,
    };
  }, [artifacts.data]);

  return (
    <div>
      <PageHeader
        title="EV Charging Demand Intelligence"
        lede="Historical demand reconstruction, forecasting, peak behaviour and model diagnostics"
        meta="Caltech ACN · historical forecasting study"
      />

      <QueryBoundary
        loading={overview.loading}
        error={overview.error}
        data={overview.data}
        height={120}
      >
        {(data) => (
          <>
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-3 xl:grid-cols-6">
              <KpiCard
                label="Hourly observations"
                value={int(data.demand.observations)}
                countTo={data.demand.observations ?? null}
                format={(v) => int(v)}
                delay={0}
              />
              <KpiCard
                label="Total reconstructed energy"
                value={energy(data.demand.totalKwh, 0)}
                accent="signal"
                countTo={data.demand.totalKwh ?? null}
                format={(v) => energy(v, 0)}
                delay={0.04}
              />
              <KpiCard
                label="Mean demand"
                value={rate(data.demand.mean)}
                countTo={data.demand.mean ?? null}
                format={(v) => rate(v)}
                delay={0.08}
              />
              <KpiCard
                label="Peak demand"
                value={rate(data.demand.maximum)}
                accent="prediction"
                countTo={data.demand.maximum ?? null}
                format={(v) => rate(v)}
                delay={0.12}
              />
              <KpiCard
                label="Peak / average"
                value={ratio(data.demand.peakOverAverage)}
                delay={0.16}
              />
              <KpiCard
                label="Zero-demand hours"
                value={int(data.demand.zeroHours)}
                sub="MAPE undefined on these"
                delay={0.2}
              />
            </div>

            {data.demand.coverageStart && (
              <p className="mt-3 text-xs text-muted">
                Coverage {dateLabel(data.demand.coverageStart)} &ndash;{" "}
                {dateLabel(data.demand.coverageEnd)} (America/Los_Angeles).
              </p>
            )}
          </>
        )}
      </QueryBoundary>

      <SectionHeading
        title="Demand ribbon"
        hint="Reconstructed hourly demand across the study period — drag the brush to zoom"
      />
      <Card>
        <QueryBoundary
          loading={hourly.loading}
          error={hourly.error}
          data={hourly.data}
          height={340}
        >
          {(data) => (
            <>
              <DemandRibbon
                points={data.points}
                peakThreshold={data.peakThreshold}
                unit={data.unit}
              />
              <p className="mt-2 text-xs text-muted">
                {int(data.totalPoints)} stored observations, drawn at 1-in-
                {data.downsample} resolution. The dashed line marks the 90th
                percentile.
              </p>
            </>
          )}
        </QueryBoundary>
      </Card>

      <div className="mt-4 grid gap-4 xl:grid-cols-2">
        <Card>
          <CardTitle>Demand profile</CardTitle>
          <CardHint className="mb-3">Mean demand by hour of day</CardHint>
          <QueryBoundary
            loading={profile.loading}
            error={profile.error}
            data={profile.data}
          >
            {(data) => <ProfileChart points={data.points} unit={data.unit} />}
          </QueryBoundary>
        </Card>

        <Card>
          <CardTitle>Week pattern</CardTitle>
          <CardHint className="mb-3">Weekday against weekend</CardHint>
          <QueryBoundary
            loading={weekday.loading}
            error={weekday.error}
            data={weekday.data}
          >
            {(data) => (
              <>
                <BarSeries
                  data={data.points as unknown as Record<string, number | string | null>[]}
                  xKey="hour"
                  unit={data.unit}
                  series={[
                    { key: "weekday", name: "Weekday", color: COLORS.signal },
                    { key: "weekend", name: "Weekend", color: COLORS.prediction },
                  ]}
                />
                <div className="mt-3 grid grid-cols-2 gap-3">
                  <StatTile label="Weekday mean" value={rate(data.weekdayMean)} />
                  <StatTile label="Weekend mean" value={rate(data.weekendMean)} />
                </div>
              </>
            )}
          </QueryBoundary>
        </Card>
      </div>

      <SectionHeading
        title="Forecast pulse"
        hint="Latest stored 24-hour test-period forecast"
      />
      <Card>
        <div className="mb-4 max-w-xs">
          <Select
            label="Model"
            value={activeModel}
            onChange={(e) => setModel(e.target.value)}
          >
            {models.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </Select>
        </div>
        <QueryBoundary
          loading={detail.loading || windows.loading}
          error={detail.error ?? windows.error}
          data={detail.data}
          height={320}
        >
          {(data) => (
            <>
              <ForecastChart points={data.points} unit={data.unit} />
              <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-5">
                <StatTile label="MAE" value={num(data.stats.mae, 3)} />
                <StatTile label="RMSE" value={num(data.stats.rmse, 3)} />
                <StatTile label="R²" value={num(data.stats.r2, 3)} />
                <StatTile
                  label="Observed total"
                  value={energy(data.stats.observedTotal, 1)}
                />
                <StatTile
                  label="Forecast total"
                  value={energy(data.stats.predictedTotal, 1)}
                />
              </div>
              <p className="mt-3 text-xs text-muted">{data.note}</p>
            </>
          )}
        </QueryBoundary>
      </Card>

      <div className="mt-4 grid gap-4 xl:grid-cols-2">
        <Card>
          <CardTitle>Temporal signals</CardTitle>
          <CardHint className="mb-3">
            Autocorrelation of the reconstructed demand series
          </CardHint>
          <div className="grid grid-cols-3 gap-3">
            {(overview.data?.temporalSignals ?? []).map((signal) => (
              <StatTile
                key={signal.lag}
                label={`${signal.label} ACF`}
                value={num(signal.value, 3)}
                hint={`lag ${signal.lag} h`}
              />
            ))}
          </div>
          <p className="mt-3 text-xs leading-relaxed text-muted">
            Strong dependence at one hour, one day and one week is what makes
            lagged demand the central feature group, and makes a seasonal naive
            benchmark a demanding comparison.
          </p>
        </Card>

        <Card>
          <CardTitle>Research status</CardTitle>
          <CardHint className="mb-3">Artefact health</CardHint>
          <div className="grid grid-cols-3 gap-3">
            <StatTile label="Available" value={int(artifactHealth.available)} />
            <StatTile label="Optional absent" value={int(artifactHealth.optional)} />
            <StatTile label="Expected absent" value={int(artifactHealth.missing)} />
          </div>
          <p className="mt-3 text-xs text-muted">
            {int(artifactHealth.total)} expected artefacts checked live. The
            Research page lists each one with its path.
          </p>
        </Card>
      </div>

      <div className="mt-6">
        <ResearchNote title="Target construction.">
          {overview.data?.targetLimitation}
        </ResearchNote>
      </div>
    </div>
  );
}
