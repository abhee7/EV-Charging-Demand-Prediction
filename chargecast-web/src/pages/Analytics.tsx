import { useState } from "react";

import { endpoints } from "@/api/endpoints";
import { AcfChart } from "@/charts/AcfChart";
import { BarSeries } from "@/charts/BarSeries";
import { DistributionChart } from "@/charts/DistributionChart";
import { Heatmap } from "@/charts/Heatmap";
import { ProfileChart } from "@/charts/ProfileChart";
import { COLORS } from "@/charts/theme";
import { PageHeader } from "@/components/PageHeader";
import { QueryBoundary } from "@/components/QueryBoundary";
import { ResearchNote } from "@/components/ResearchNote";
import { StatTile } from "@/components/StatTile";
import { Card, CardHint, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Tabs } from "@/components/ui/tabs";
import { useApi } from "@/hooks/useApi";
import { energy, num, rate, ratio } from "@/lib/format";
import type {
  Autocorrelation,
  DemandDistribution,
  DemandHeatmap,
  DemandProfile,
  MonthlyDemand,
  ScenarioResult,
  WeekdaySplit,
} from "@/types/api";

const TABS = [
  { key: "hourly", label: "Hourly" },
  { key: "weekday", label: "Weekday" },
  { key: "weekend", label: "Weekend" },
  { key: "monthly", label: "Monthly" },
  { key: "heatmap", label: "Hour × Day" },
  { key: "distribution", label: "Distribution" },
  { key: "percentiles", label: "Percentiles" },
  { key: "acf", label: "ACF" },
  { key: "scenario", label: "Scenario" },
];

export default function Analytics() {
  const [tab, setTab] = useState("hourly");
  const [lag, setLag] = useState(168);
  const [change, setChange] = useState(0);

  const profile = useApi<DemandProfile>(endpoints.demandProfile);
  const weekday = useApi<WeekdaySplit>(endpoints.demandWeekday);
  const monthly = useApi<MonthlyDemand>(endpoints.demandMonthly);
  const heatmap = useApi<DemandHeatmap>(endpoints.demandHeatmap);
  const distribution = useApi<DemandDistribution>(endpoints.demandDistribution);
  const acf = useApi<Autocorrelation>(endpoints.demandAcf, { max_lag: 336, lag });
  const scenario = useApi<ScenarioResult>(endpoints.demandScenario, { change });

  return (
    <div>
      <PageHeader
        title="Demand Analytics"
        lede="Temporal structure of the reconstructed demand series"
        meta="Caltech ACN · America/Los_Angeles calendar"
      />

      <Tabs items={TABS} value={tab} onChange={setTab} className="mb-5" />

      {tab === "hourly" && (
        <Card>
          <CardTitle>Hourly demand profile</CardTitle>
          <CardHint className="mb-3">Mean with interquartile band</CardHint>
          <QueryBoundary loading={profile.loading} error={profile.error} data={profile.data}>
            {(data) => <ProfileChart points={data.points} unit={data.unit} />}
          </QueryBoundary>
        </Card>
      )}

      {(tab === "weekday" || tab === "weekend") && (
        <Card>
          <CardTitle>
            {tab === "weekday" ? "Weekday demand" : "Weekend demand"}
          </CardTitle>
          <CardHint className="mb-3">
            Mean demand by hour, both segments shown for contrast
          </CardHint>
          <QueryBoundary loading={weekday.loading} error={weekday.error} data={weekday.data}>
            {(data) => (
              <>
                <BarSeries
                  data={data.points as unknown as Record<string, number | string | null>[]}
                  xKey="hour"
                  unit={data.unit}
                  xLabel="Hour of day (America/Los_Angeles)"
                  series={
                    tab === "weekday"
                      ? [
                          { key: "weekday", name: "Weekday", color: COLORS.signal },
                          { key: "weekend", name: "Weekend", color: "rgba(234,88,12,0.35)" },
                        ]
                      : [
                          { key: "weekend", name: "Weekend", color: COLORS.prediction },
                          { key: "weekday", name: "Weekday", color: "rgba(79,70,229,0.3)" },
                        ]
                  }
                />
                <div className="mt-4 grid grid-cols-2 gap-3">
                  <StatTile label="Weekday mean" value={rate(data.weekdayMean)} />
                  <StatTile label="Weekend mean" value={rate(data.weekendMean)} />
                </div>
              </>
            )}
          </QueryBoundary>
        </Card>
      )}

      {tab === "monthly" && (
        <Card>
          <CardTitle>Monthly demand</CardTitle>
          <CardHint className="mb-3">Aggregated across the study period</CardHint>
          <QueryBoundary loading={monthly.loading} error={monthly.error} data={monthly.data}>
            {(data) => (
              <>
                <BarSeries
                  data={data.points as unknown as Record<string, number | string | null>[]}
                  xKey="label"
                  unit="kWh"
                  series={[{ key: "total", name: "Total energy", color: COLORS.signal }]}
                />
                <p className="mt-3 text-xs text-muted">{data.note}</p>
              </>
            )}
          </QueryBoundary>
        </Card>
      )}

      {tab === "heatmap" && (
        <Card>
          <CardTitle>Hour by day-of-week</CardTitle>
          <CardHint className="mb-4">Mean demand surface</CardHint>
          <QueryBoundary loading={heatmap.loading} error={heatmap.error} data={heatmap.data} height={320}>
            {(data) => (
              <Heatmap
                cells={data.cells}
                days={data.days}
                min={data.min}
                max={data.max}
                unit={data.unit}
              />
            )}
          </QueryBoundary>
        </Card>
      )}

      {(tab === "distribution" || tab === "percentiles") && (
        <Card>
          <CardTitle>
            {tab === "distribution" ? "Demand distribution" : "Percentiles"}
          </CardTitle>
          <CardHint className="mb-3">
            Histogram with P75, P90, P95 and P99 markers
          </CardHint>
          <QueryBoundary
            loading={distribution.loading}
            error={distribution.error}
            data={distribution.data}
          >
            {(data) => (
              <>
                {tab === "distribution" && (
                  <DistributionChart
                    bins={data.bins}
                    percentiles={data.percentiles}
                    unit={data.unit}
                  />
                )}
                <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <StatTile label="P75" value={rate(data.percentiles.p75)} />
                  <StatTile label="P90" value={rate(data.percentiles.p90)} />
                  <StatTile label="P95" value={rate(data.percentiles.p95)} />
                  <StatTile label="P99" value={rate(data.percentiles.p99)} />
                </div>
              </>
            )}
          </QueryBoundary>
        </Card>
      )}

      {tab === "acf" && (
        <Card>
          <CardTitle>Autocorrelation explorer</CardTitle>
          <CardHint className="mb-4">Select a lag to inspect</CardHint>
          <div className="mb-5 max-w-md">
            <Slider
              label="Lag (hours)"
              min={1}
              max={336}
              step={1}
              value={lag}
              display={`Lag ${lag}`}
              onChange={(e) => setLag(Number(e.target.value))}
            />
          </div>
          <QueryBoundary loading={acf.loading} error={acf.error} data={acf.data} height={320}>
            {(data) => (
              <>
                <AcfChart
                  points={data.points}
                  selectedLag={lag}
                  confidence={data.confidence}
                />
                {data.selected && (
                  <div className="mt-4 grid gap-3 sm:grid-cols-4">
                    <StatTile
                      label={`Lag ${data.selected.lag}`}
                      value={num(data.selected.value, 4)}
                    />
                    {data.highlights.map((h) => (
                      <StatTile
                        key={h.lag}
                        label={`Lag ${h.lag}`}
                        value={num(h.value, 4)}
                      />
                    ))}
                  </div>
                )}
                {data.selected && (
                  <p className="mt-3 text-xs text-muted">{data.selected.meaning}</p>
                )}
                <p className="mt-1 text-xs text-muted">
                  Dotted lines mark the 95% significance band. Lags 1, 24 and
                  168 are highlighted in indigo; the selected lag is orange.
                </p>
              </>
            )}
          </QueryBoundary>
        </Card>
      )}

      {tab === "scenario" && (
        <Card>
          <CardTitle>Scenario simulator</CardTitle>
          <CardHint className="mb-4">
            Arithmetic transformation of the historical series
          </CardHint>
          <div className="mb-5 max-w-md">
            <Slider
              label="Demand change"
              min={-20}
              max={50}
              step={5}
              value={change}
              display={`${change > 0 ? "+" : ""}${change}%`}
              onChange={(e) => setChange(Number(e.target.value))}
            />
          </div>
          <QueryBoundary
            loading={scenario.loading}
            error={scenario.error}
            data={scenario.data}
            height={180}
          >
            {(data) => (
              <>
                <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
                  <StatTile label="Scenario mean" value={rate(data.scenario.mean)} />
                  <StatTile label="Scenario peak" value={rate(data.scenario.maximum)} />
                  <StatTile label="Scenario P90" value={rate(data.scenario.p90)} />
                  <StatTile label="Scenario P95" value={rate(data.scenario.p95)} />
                  <StatTile
                    label="Scenario total energy"
                    value={energy(data.scenario.totalKwh, 0)}
                  />
                  <StatTile
                    label="Peak / average"
                    value={ratio(data.scenario.peakOverAverage)}
                  />
                </div>
                <div className="mt-4">
                  <BarSeries
                    data={[
                      { metric: "Mean", historical: data.baseline.mean ?? 0, scenario: data.scenario.mean ?? 0 },
                      { metric: "P90", historical: data.baseline.p90 ?? 0, scenario: data.scenario.p90 ?? 0 },
                      { metric: "P95", historical: data.baseline.p95 ?? 0, scenario: data.scenario.p95 ?? 0 },
                      { metric: "Peak", historical: data.baseline.maximum ?? 0, scenario: data.scenario.maximum ?? 0 },
                    ]}
                    xKey="metric"
                    unit={data.unit}
                    series={[
                      { key: "historical", name: "Historical", color: "rgba(79,70,229,0.55)" },
                      { key: "scenario", name: "Scenario", color: COLORS.prediction },
                    ]}
                  />
                </div>
                <div className="mt-4">
                  <ResearchNote title="Scenario simulation — not a new forecast.">
                    {data.note}
                  </ResearchNote>
                </div>
              </>
            )}
          </QueryBoundary>
        </Card>
      )}
    </div>
  );
}
