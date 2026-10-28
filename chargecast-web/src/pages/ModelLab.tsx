import { useEffect, useMemo, useState } from "react";

import { endpoints } from "@/api/endpoints";
import { HorizonChart } from "@/charts/HorizonChart";
import { MetricDots } from "@/charts/MetricDots";
import { DataTable } from "@/components/DataTable";
import { PageHeader } from "@/components/PageHeader";
import { ProvenanceNote } from "@/components/ProvenanceNote";
import { QueryBoundary } from "@/components/QueryBoundary";
import { SectionHeading } from "@/components/SectionHeading";
import { StatTile } from "@/components/StatTile";
import { Badge } from "@/components/ui/badge";
import { Card, CardHint, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { useApi } from "@/hooks/useApi";
import { num, pValue } from "@/lib/format";
import type {
  DmAudited,
  DmInteractive,
  HorizonResponse,
  MetricKey,
  MetricsResponse,
} from "@/types/api";

const METRIC_LABELS: Record<MetricKey, string> = {
  mae: "MAE",
  rmse: "RMSE",
  r2: "R²",
  smape: "sMAPE",
  mase: "MASE",
};

export default function ModelLab() {
  const [metric, setMetric] = useState<MetricKey>("mae");
  const [order, setOrder] = useState<"model" | MetricKey>("model");
  const [horizonMetric, setHorizonMetric] = useState<MetricKey>("mae");

  const metrics = useApi<MetricsResponse>(endpoints.modelMetrics);
  const horizon = useApi<HorizonResponse>(endpoints.modelHorizon, {
    metric: horizonMetric,
  });
  const audited = useApi<DmAudited>(endpoints.dmAudited);

  const [modelA, setModelA] = useState("");
  const [modelB, setModelB] = useState("");
  const [hacLag, setHacLag] = useState(23);

  // Memoised so the identity is stable across renders; otherwise the effect
  // below would re-run on every render.
  const available = useMemo(
    () => metrics.data?.models?.map((m) => m.model) ?? [],
    [metrics.data],
  );
  useEffect(() => {
    if (!modelA && available.length) setModelA(available[0]);
    if (!modelB && available.length > 1) setModelB(available[1]);
  }, [available, modelA, modelB]);

  const interactive = useApi<DmInteractive>(
    endpoints.dmInteractive,
    { model_a: modelA, model_b: modelB, hac_lag: hacLag },
    { skip: !modelA || !modelB || modelA === modelB },
  );

  const sortedModels = (() => {
    const rows = metrics.data?.models ?? [];
    if (order === "model") {
      return [...rows].sort((a, b) =>
        a.model.toLowerCase().localeCompare(b.model.toLowerCase()),
      );
    }
    return [...rows].sort((a, b) => {
      const left = a[order] ?? Number.POSITIVE_INFINITY;
      const right = b[order] ?? Number.POSITIVE_INFINITY;
      const descending = order === "r2";
      return descending ? Number(right) - Number(left) : Number(left) - Number(right);
    });
  })();

  return (
    <div>
      <PageHeader
        title="Model Lab"
        lede="Metric comparison and paired statistical testing"
        meta="Models are listed by name; no ordering is implied"
      />

      <SectionHeading
        title="Metric explorer"
        hint="Choose a metric to compare across every model"
      />
      <Card>
        <div className="mb-4 max-w-xs">
          <Select
            label="Metric"
            value={metric}
            onChange={(e) => setMetric(e.target.value as MetricKey)}
          >
            {(metrics.data?.metrics ?? []).map((m) => (
              <option key={m.key} value={m.key}>
                {m.label}
              </option>
            ))}
          </Select>
        </div>
        <QueryBoundary
          loading={metrics.loading}
          error={metrics.error}
          data={metrics.data}
          height={300}
        >
          {(data) => {
            const descriptor = data.metrics.find((m) => m.key === metric);
            return (
              <>
                <MetricDots
                  models={[...data.models].sort((a, b) =>
                    a.model.toLowerCase().localeCompare(b.model.toLowerCase()),
                  )}
                  metric={metric}
                  label={descriptor?.label ?? METRIC_LABELS[metric]}
                  unit={descriptor?.unit}
                />
                <p className="mt-2 text-xs text-muted">
                  Points are positioned by value and ordered by model name, so
                  the chart carries no implied ranking.
                </p>
              </>
            );
          }}
        </QueryBoundary>
      </Card>

      <SectionHeading title="Model metrics" hint="Stored test figures" />
      <Card>
        <div className="mb-4 max-w-xs">
          <Select
            label="Display order"
            value={order}
            onChange={(e) => setOrder(e.target.value as "model" | MetricKey)}
          >
            <option value="model">Model name (default)</option>
            {(metrics.data?.metrics ?? []).map((m) => (
              <option key={m.key} value={m.key}>
                {m.label}
              </option>
            ))}
          </Select>
        </div>
        <QueryBoundary
          loading={metrics.loading}
          error={metrics.error}
          data={metrics.data}
          height={220}
        >
          {(data) => (
            <>
              <DataTable
                columns={["Model", ...data.metrics.map((m) => m.label)]}
                rows={sortedModels.map((row) => {
                  const out: Record<string, unknown> = { Model: row.model };
                  for (const descriptor of data.metrics) {
                    out[descriptor.label] = row[descriptor.key] ?? null;
                  }
                  return out;
                })}
              />
              <p className="mt-3 text-xs leading-relaxed text-muted">
                {order === "model"
                  ? data.orderingNote
                  : `Display sorted by ${METRIC_LABELS[order as MetricKey]}. Sorting is for display only; it is not a scientific ranking.`}
              </p>
              <dl className="mt-3 grid gap-1.5 text-xs text-muted sm:grid-cols-2">
                {data.metrics.map((m) => (
                  <div key={m.key}>
                    <dt className="inline font-medium text-ink">{m.label}</dt>
                    <dd className="inline">
                      {" "}
                      — {m.unit ? `measured in ${m.unit}. ` : ""}
                      {m.lowerIsBetter ? "Smaller values mean smaller error." : "Larger values mean more variance explained."}
                    </dd>
                  </div>
                ))}
              </dl>
            </>
          )}
        </QueryBoundary>
      </Card>

      <SectionHeading
        title="Audited research result"
        hint="Diebold–Mariano, read from the verified artefact"
      />
      <Card>
        <ProvenanceNote
          kind="audited"
          note="Read directly from results/metrics/diebold_mariano_tests.csv. This is the authoritative statistical result for the study."
          className="mb-4"
        />
        <QueryBoundary
          loading={audited.loading}
          error={audited.error}
          data={audited.data}
          height={240}
        >
          {(data) => (
            <AuditedDm data={data} />
          )}
        </QueryBoundary>
      </Card>

      <SectionHeading
        title="Interactive DM explorer"
        hint="Recomputed from stored predictions"
      />
      <Card>
        <ProvenanceNote
          kind="exploratory"
          note="This panel recomputes the test from stored predictions using the selected model pair and HAC lag. It does not overwrite or replace the audited result above."
          className="mb-4"
        />
        <div className="grid gap-4 sm:grid-cols-3">
          <Select label="Model A" value={modelA} onChange={(e) => setModelA(e.target.value)}>
            {available.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </Select>
          <Select label="Model B" value={modelB} onChange={(e) => setModelB(e.target.value)}>
            {available.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </Select>
          <Select
            label="HAC lag"
            value={hacLag}
            onChange={(e) => setHacLag(Number(e.target.value))}
            hint="Newey–West truncation lag"
          >
            {[0, 6, 12, 23, 24, 36, 48].map((lag) => (
              <option key={lag} value={lag}>
                {lag}
              </option>
            ))}
          </Select>
        </div>

        {modelA === modelB ? (
          <p className="mt-4 text-sm text-muted">
            Select two different models to run the test.
          </p>
        ) : (
          <div className="mt-4">
            <QueryBoundary
              loading={interactive.loading}
              error={interactive.error}
              data={interactive.data}
              height={140}
            >
              {(data) => (
                <>
                  <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                    <StatTile
                      label="DM statistic"
                      value={num(data.statistic, 6)}
                    />
                    <StatTile label="p-value" value={pValue(data.pValue)} />
                    <StatTile
                      label="Paired observations"
                      value={data.observations?.toLocaleString() ?? "—"}
                    />
                    <StatTile label="HAC lag" value={String(data.hacLag ?? "—")} />
                  </div>
                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    <Badge tone={data.significantAt5Pct ? "prediction" : "neutral"}>
                      {data.significantAt5Pct
                        ? "Significant at the 5% level"
                        : "Not significant at the 5% level"}
                    </Badge>
                    <Badge>{data.loss ?? "squared error"} loss</Badge>
                  </div>
                  <p className="mt-3 text-xs leading-relaxed text-muted">
                    The test asks whether the average difference in squared
                    error is distinguishable from zero once serial correlation
                    is accounted for. A p-value above 0.05 means the evidence
                    does not separate the two models on this sample. The
                    statistic's sign indicates which model carried the larger
                    average squared error; it does not order them.
                  </p>
                </>
              )}
            </QueryBoundary>
          </div>
        )}
      </Card>

      <SectionHeading
        title="Horizon performance"
        hint="Accuracy by hours ahead of the forecast origin"
      />
      <Card>
        <div className="mb-4 max-w-xs">
          <Select
            label="Metric"
            value={horizonMetric}
            onChange={(e) => setHorizonMetric(e.target.value as MetricKey)}
          >
            {(horizon.data?.availableMetrics ?? ["mae", "rmse"]).map((m) => (
              <option key={m} value={m}>
                {METRIC_LABELS[m]}
              </option>
            ))}
          </Select>
        </div>
        <QueryBoundary
          loading={horizon.loading}
          error={horizon.error}
          data={horizon.data}
          height={320}
        >
          {(data) => (
            <HorizonChart
              series={data.series ?? []}
              label={data.label ?? "MAE"}
              unit={data.unit}
            />
          )}
        </QueryBoundary>
      </Card>
    </div>
  );
}

function AuditedDm({ data }: { data: DmAudited }) {
  const [index, setIndex] = useState(0);
  const selected = data.comparisons[index];

  return (
    <>
      {data.comparisons.length > 1 && (
        <div className="mb-4 max-w-md">
          <Select
            label="Comparison"
            value={index}
            onChange={(e) => setIndex(Number(e.target.value))}
          >
            {data.comparisons.map((c, i) => (
              <option key={i} value={i}>
                {c.modelA ?? "A"} vs {c.modelB ?? "B"}
              </option>
            ))}
          </Select>
        </div>
      )}

      {selected && (
        <>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <StatTile label="DM statistic" value={num(selected.statistic, 6)} />
            <StatTile label="p-value" value={pValue(selected.pValue)} />
            <StatTile
              label="Observations"
              value={selected.observations?.toLocaleString() ?? "—"}
            />
            <StatTile
              label="HAC / Newey–West lag"
              value={selected.hacLag != null ? String(selected.hacLag) : "—"}
            />
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            {selected.loss && <Badge>{selected.loss} loss</Badge>}
            {selected.pValue != null && (
              <Badge tone={selected.pValue < 0.05 ? "prediction" : "neutral"}>
                {selected.pValue < 0.05
                  ? "Significant at the 5% level"
                  : "Not significant at the 5% level"}
              </Badge>
            )}
          </div>
        </>
      )}

      <div className="mt-5">
        <CardTitle>Source table</CardTitle>
        <CardHint className="mb-3">Rendered exactly as stored</CardHint>
        <DataTable columns={data.columns} rows={data.rows} />
        <p className="mt-2 text-xs text-muted">
          {data.rows.length} stored comparison
          {data.rows.length === 1 ? "" : "s"} from {data.source}.
          {data.absentFields.length > 0 &&
            ` Fields not present in this artefact: ${data.absentFields.join(", ")}.`}
        </p>
      </div>
    </>
  );
}
