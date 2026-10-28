import { useState } from "react";

import { endpoints } from "@/api/endpoints";
import { BarSeries } from "@/charts/BarSeries";
import { ConfusionMatrix } from "@/charts/ConfusionMatrix";
import { COLORS } from "@/charts/theme";
import { DataTable } from "@/components/DataTable";
import { KpiCard } from "@/components/KpiCard";
import { PageHeader } from "@/components/PageHeader";
import { ProvenanceNote } from "@/components/ProvenanceNote";
import { QueryBoundary } from "@/components/QueryBoundary";
import { ResearchNote } from "@/components/ResearchNote";
import { SectionHeading } from "@/components/SectionHeading";
import { StatTile } from "@/components/StatTile";
import { Badge } from "@/components/ui/badge";
import { Card, CardHint, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { useApi } from "@/hooks/useApi";
import { int, num, pct, rate, ratio } from "@/lib/format";
import type {
  CapacityResult,
  DemandSummary,
  PeakAudited,
  PeakInteractive,
  PeakThresholds,
} from "@/types/api";

const PERCENTILES = [75, 90, 95, 99];
const CAPACITIES = [60, 120, 180, 240, 360];

export default function Peak() {
  const [percentile, setPercentile] = useState(90);
  const [model, setModel] = useState("");
  const [capacity, setCapacity] = useState(120);

  const summary = useApi<DemandSummary>(endpoints.demandSummary);
  const audited = useApi<PeakAudited>(endpoints.peakAudited);
  const thresholds = useApi<PeakThresholds>(endpoints.peakThresholds);
  const interactive = useApi<PeakInteractive>(endpoints.peakInteractive, {
    percentile,
    model: model || undefined,
  });
  const capacityView = useApi<CapacityResult>(endpoints.demandCapacity, {
    capacity_kw: capacity,
  });

  const activeModel = model || interactive.data?.availableModels?.[0] || "";

  return (
    <div>
      <PageHeader
        title="Peak Intelligence"
        lede="High-demand hours and how the stored forecasts classify them"
        meta="Audited research output, with an exploratory recomputation alongside"
      />

      <QueryBoundary
        loading={summary.loading}
        error={summary.error}
        data={summary.data}
        height={120}
      >
        {(data) => (
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-3 xl:grid-cols-6">
            <KpiCard
              label="Peak demand"
              value={rate(data.maximum)}
              accent="prediction"
              countTo={data.maximum ?? null}
              format={(v) => rate(v)}
            />
            <KpiCard label="Peak / average" value={ratio(data.peakOverAverage)} />
            <KpiCard label="P90" value={rate(data.p90)} />
            <KpiCard label="P95" value={rate(data.p95)} />
            <KpiCard label="P99" value={rate(data.p99)} />
            <KpiCard
              label="Test threshold"
              value={
                interactive.data?.threshold != null
                  ? rate(interactive.data.threshold)
                  : "—"
              }
              sub={`P${percentile} of test demand`}
            />
          </div>
        )}
      </QueryBoundary>

      <SectionHeading
        title="Audited peak results"
        hint="Read from the verified research pipeline output"
      />
      <Card>
        <ProvenanceNote
          kind="audited"
          note="Read directly from results/peak_analysis/. This is the authoritative peak analysis for the study."
          className="mb-4"
        />

        <CardTitle>High-demand thresholds</CardTitle>
        <CardHint className="mb-3">Verified threshold definition</CardHint>
        <QueryBoundary
          loading={thresholds.loading}
          error={thresholds.error}
          data={thresholds.data}
          height={160}
        >
          {(data) => (
            <>
              <DataTable columns={data.columns} rows={data.rows} />
              <p className="mt-2 text-xs text-muted">
                Read from {data.source}, rendered as stored.
              </p>
            </>
          )}
        </QueryBoundary>

        <div className="mt-6">
          <CardTitle>Peak detection by model</CardTitle>
          <CardHint className="mb-3">
            Precision, recall and F1 from the verified artefact
          </CardHint>
          <QueryBoundary
            loading={audited.loading}
            error={audited.error}
            data={audited.data}
            height={260}
          >
            {(data) => <AuditedPeak data={data} />}
          </QueryBoundary>
        </div>
      </Card>

      <SectionHeading
        title="Interactive peak explorer"
        hint="Recomputed from stored predictions"
      />
      <Card>
        <ProvenanceNote
          kind="exploratory"
          note="This recalculates peak classification from stored predictions using the selected percentile. It does not replace the audited result above."
          className="mb-4"
        />

        <div className="grid gap-4 sm:grid-cols-2 lg:max-w-xl">
          <Select
            label="Percentile"
            value={percentile}
            onChange={(e) => setPercentile(Number(e.target.value))}
            hint="The audited analysis uses the 90th percentile"
          >
            {PERCENTILES.map((p) => (
              <option key={p} value={p}>
                P{p}
              </option>
            ))}
          </Select>
          <Select
            label="Model"
            value={activeModel}
            onChange={(e) => setModel(e.target.value)}
          >
            {(interactive.data?.availableModels ?? []).map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </Select>
        </div>

        <div className="mt-5">
          <QueryBoundary
            loading={interactive.loading}
            error={interactive.error}
            data={interactive.data}
            height={280}
          >
            {(data) => (
              <>
                {data.differsFromAudited && (
                  <div className="mb-4">
                    <ResearchNote title="Interactive threshold differs from audited research threshold.">
                      These figures use the P{data.percentile} threshold and are
                      not comparable with the audited section, which uses P
                      {data.auditedPercentile}.
                    </ResearchNote>
                  </div>
                )}
                <p className="mb-3 text-xs text-muted">
                  A peak hour is reconstructed demand at or above{" "}
                  {rate(data.threshold)}, applied identically to the observed
                  and forecast series.
                </p>
                <DataTable
                  columns={["Model", "Precision", "Recall", "F1", "Observed peak hours", "Forecast peak hours"]}
                  rows={(data.models ?? []).map((m) => ({
                    Model: m.model,
                    Precision: m.precision,
                    Recall: m.recall,
                    F1: m.f1,
                    "Observed peak hours": m.observedPeakHours ?? null,
                    "Forecast peak hours": m.forecastPeakHours ?? null,
                  }))}
                />
                {data.selected && (
                  <div className="mt-5 grid gap-5 lg:grid-cols-[1fr_auto]">
                    <div className="grid grid-cols-3 gap-3 self-start">
                      <StatTile label="Precision" value={num(data.selected.precision, 4)} />
                      <StatTile label="Recall" value={num(data.selected.recall, 4)} />
                      <StatTile label="F1" value={num(data.selected.f1, 4)} />
                    </div>
                    {data.selected.truePositive != null && (
                      <ConfusionMatrix
                        truePositive={data.selected.truePositive ?? 0}
                        falsePositive={data.selected.falsePositive ?? 0}
                        falseNegative={data.selected.falseNegative ?? 0}
                        trueNegative={data.selected.trueNegative ?? 0}
                        title={`${data.selected.model} — recomputed classification`}
                      />
                    )}
                  </div>
                )}
                <p className="mt-4 text-xs leading-relaxed text-muted">
                  Precision is the share of forecast peak hours that were
                  observed peaks; recall is the share of observed peak hours the
                  forecast identified. Raising one generally lowers the other,
                  so these describe a trade-off rather than an ordering.
                </p>
              </>
            )}
          </QueryBoundary>
        </div>
      </Card>

      <SectionHeading
        title="Indicative sizing pressure"
        hint="Charger capacity comparison"
      />
      <Card>
        <div className="mb-4 max-w-xs">
          <Select
            label="Nominal capacity"
            value={capacity}
            onChange={(e) => setCapacity(Number(e.target.value))}
          >
            {CAPACITIES.map((c) => (
              <option key={c} value={c}>
                {c} kW
              </option>
            ))}
          </Select>
        </div>
        <QueryBoundary
          loading={capacityView.loading}
          error={capacityView.error}
          data={capacityView.data}
          height={160}
        >
          {(data) => (
            <>
              <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
                <StatTile label="Selected capacity" value={`${int(data.capacityKw)} kW`} />
                <StatTile label="Historical peak" value={rate(data.historicalPeak)} />
                <StatTile
                  label="Peak / capacity"
                  value={ratio(data.peakOverCapacity)}
                />
                <StatTile label="Hours above capacity" value={int(data.hoursAbove)} />
                <StatTile
                  label="Share of observations"
                  value={pct(data.shareAbove, 2)}
                />
              </div>
              <p className="mt-3 text-sm text-muted">
                {data.hoursAbove > 0
                  ? `Historical reconstructed demand exceeds the selected nominal capacity during ${int(data.hoursAbove)} of ${int(data.observations)} observations.`
                  : "Historical reconstructed demand remains at or below the selected nominal capacity across all observations."}
              </p>
              <div className="mt-4">
                <ResearchNote title="Units.">{data.note}</ResearchNote>
              </div>
            </>
          )}
        </QueryBoundary>
      </Card>

      {audited.data?.caveat && (
        <div className="mt-6">
          <ResearchNote title="What a peak means here.">
            {audited.data.caveat}
          </ResearchNote>
        </div>
      )}
    </div>
  );
}

function AuditedPeak({ data }: { data: PeakAudited }) {
  const [selected, setSelected] = useState("");
  const active = selected || data.models[0]?.model || "";
  const row = data.models.find((m) => m.model === active);

  const chartData = data.models.map((m) => ({
    model: m.model,
    precision: m.precision ?? 0,
    recall: m.recall ?? 0,
    f1: m.f1 ?? 0,
  }));

  return (
    <>
      <DataTable columns={data.columns} rows={data.rows} />
      <p className="mt-2 text-xs text-muted">
        Read from {data.source}, rendered as stored.
        {data.absentFields.length > 0 &&
          ` Fields not present in this artefact: ${data.absentFields.join(", ")}.`}
      </p>

      {chartData.some((d) => d.precision || d.recall) && (
        <div className="mt-5">
          <BarSeries
            data={chartData}
            xKey="model"
            series={[
              { key: "precision", name: "Precision", color: COLORS.signal },
              { key: "recall", name: "Recall", color: COLORS.prediction },
              { key: "f1", name: "F1", color: COLORS.violet },
            ]}
          />
        </div>
      )}

      {data.hasConfusionMatrix && (
        <div className="mt-6">
          <div className="mb-4 max-w-xs">
            <Select
              label="Model"
              value={active}
              onChange={(e) => setSelected(e.target.value)}
            >
              {data.models.map((m) => (
                <option key={m.model} value={m.model}>
                  {m.model}
                </option>
              ))}
            </Select>
          </div>
          {row && (
            <div className="grid gap-5 lg:grid-cols-[1fr_auto]">
              <div className="grid grid-cols-3 gap-3 self-start">
                <StatTile label="Precision" value={num(row.precision, 4)} />
                <StatTile label="Recall" value={num(row.recall, 4)} />
                <StatTile label="F1" value={num(row.f1, 4)} />
              </div>
              <ConfusionMatrix
                truePositive={row.truePositive ?? 0}
                falsePositive={row.falsePositive ?? 0}
                falseNegative={row.falseNegative ?? 0}
                trueNegative={row.trueNegative ?? 0}
                title={`${row.model} — audited peak classification`}
              />
            </div>
          )}
        </div>
      )}

      {!data.hasConfusionMatrix && (
        <div className="mt-4">
          <Badge>Confusion counts not present in this artefact</Badge>
        </div>
      )}
    </>
  );
}
