import { useState } from "react";

import { endpoints } from "@/api/endpoints";
import { HorizonChart } from "@/charts/HorizonChart";
import { MetricDots } from "@/charts/MetricDots";
import { DataTable } from "@/components/DataTable";
import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { QueryBoundary } from "@/components/QueryBoundary";
import { ResearchNote } from "@/components/ResearchNote";
import { SectionHeading } from "@/components/SectionHeading";
import { StatTile } from "@/components/StatTile";
import { Card, CardHint, CardTitle } from "@/components/ui/card";
import { Tabs } from "@/components/ui/tabs";
import { useApi } from "@/hooks/useApi";
import { energy, int, rate } from "@/lib/format";
import type {
  RobustnessHorizon,
  RobustnessMetrics,
  RobustnessSummary,
} from "@/types/api";

const TABS = [
  { key: "primary", label: "Primary target" },
  { key: "arrival", label: "Arrival-hour target" },
];

export default function Robustness() {
  const [tab, setTab] = useState("primary");

  const summary = useApi<RobustnessSummary>(endpoints.robustnessSummary);
  const metrics = useApi<RobustnessMetrics>(endpoints.robustnessMetrics);
  const horizon = useApi<RobustnessHorizon>(endpoints.robustnessHorizon, {
    metric: "mae",
  });

  const target = summary.data?.targets.find((t) => t.target === tab);
  const metricTarget = metrics.data?.targets.find((t) => t.target === tab);
  const horizonTarget = horizon.data?.targets.find((t) => t.target === tab);

  return (
    <div>
      <PageHeader
        title="Robustness"
        lede="Does the reconstruction choice change the conclusions?"
        meta="Two target constructions, identical models, features and split"
      />

      {summary.data?.question && (
        <ResearchNote title="Robustness question.">
          {summary.data.question}
        </ResearchNote>
      )}

      <div className="mt-6">
        <Tabs items={TABS} value={tab} onChange={setTab} className="mb-5" />
      </div>

      {/* Both tabs render through the same structure, so neither construction
          is privileged by presentation. */}
      <Card>
        <CardTitle>{target?.label ?? "Target"}</CardTitle>
        <CardHint className="mb-3">{target?.construction}</CardHint>
        <QueryBoundary
          loading={summary.loading}
          error={summary.error}
          data={target}
          height={180}
        >
          {(data) => (
            <>
              <p className="mb-4 max-w-3xl text-sm leading-relaxed text-muted">
                {data.definition}
              </p>
              <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
                <StatTile label="Observations" value={int(data.observations)} />
                <StatTile label="Total energy" value={energy(data.totalKwh, 0)} />
                <StatTile label="Mean" value={rate(data.mean)} />
                <StatTile label="Median" value={rate(data.median)} />
                <StatTile label="Peak" value={rate(data.maximum)} />
                <StatTile label="Zero-demand hours" value={int(data.zeroHours)} />
              </div>
            </>
          )}
        </QueryBoundary>
      </Card>

      <SectionHeading title="Model metrics" hint="Under this construction" />
      <Card>
        <QueryBoundary
          loading={metrics.loading}
          error={metrics.error}
          data={metricTarget}
          height={240}
        >
          {(data) =>
            data.models ? (
              <DataTable
                columns={["Model", "MAE", "RMSE", "R²", "sMAPE", "MASE"]}
                rows={data.models.map((m) => ({
                  Model: m.model,
                  MAE: m.mae ?? null,
                  RMSE: m.rmse ?? null,
                  "R²": m.r2 ?? null,
                  sMAPE: m.smape ?? null,
                  MASE: m.mase ?? null,
                }))}
                caption={`Read from ${data.source}. Models in alphabetical order.`}
              />
            ) : (
              <EmptyState payload={data} />
            )
          }
        </QueryBoundary>
      </Card>

      <SectionHeading title="RMSE comparison" hint="Across models, this construction" />
      <Card>
        <QueryBoundary
          loading={metrics.loading}
          error={metrics.error}
          data={metricTarget}
          height={300}
        >
          {(data) =>
            data.models ? (
              <MetricDots
                models={data.models}
                metric="rmse"
                label="RMSE"
                unit="kWh/h"
              />
            ) : (
              <EmptyState payload={data} />
            )
          }
        </QueryBoundary>
      </Card>

      <SectionHeading title="Horizon metrics" hint="MAE by hours ahead" />
      <Card>
        <QueryBoundary
          loading={horizon.loading}
          error={horizon.error}
          data={horizonTarget}
          height={320}
        >
          {(data) =>
            data.series ? (
              <HorizonChart series={data.series} label="MAE" unit="kWh/h" />
            ) : (
              <EmptyState payload={data} />
            )
          }
        </QueryBoundary>
      </Card>

      <SectionHeading title="Interpretation" hint="Reading across the two targets" />
      <div className="space-y-4">
        <ResearchNote title="Different target definitions.">
          {summary.data?.warning}
        </ResearchNote>
        <ResearchNote title="Why this experiment exists.">
          {summary.data?.limitation}
        </ResearchNote>
        <Card>
          <p className="text-sm leading-relaxed text-muted">
            MASE is the most interpretable column across the two constructions:
            it is scaled by a seasonal naive benchmark computed on each target's
            own training data, so it remains meaningful when the two series
            differ in scale. Neither construction is treated as correct; the
            question is only whether the relative behaviour of the methods is
            stable.
          </p>
        </Card>
      </div>
    </div>
  );
}
