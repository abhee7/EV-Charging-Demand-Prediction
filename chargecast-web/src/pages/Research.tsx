import { endpoints } from "@/api/endpoints";
import { DataTable } from "@/components/DataTable";
import { PageHeader } from "@/components/PageHeader";
import { QueryBoundary } from "@/components/QueryBoundary";
import { ResearchNote } from "@/components/ResearchNote";
import { SectionHeading } from "@/components/SectionHeading";
import { Badge } from "@/components/ui/badge";
import { Card, CardHint, CardTitle } from "@/components/ui/card";
import { useApi } from "@/hooks/useApi";
import { useHealth } from "@/hooks/useHealth";
import type { ArtifactsResponse, ProvenanceResponse } from "@/types/api";

const FLOW = [
  "Raw charging sessions",
  "Cleaning",
  "Hourly reconstruction",
  "Feature engineering",
  "Chronological split",
  "24-hour forecasting",
  "Evaluation",
  "Explainability",
];

const STATUS_GLYPH: Record<string, string> = {
  available: "\u2713 available",
  optional: "\u26a0 optional",
  missing: "\u2715 missing",
  quarantined: "Quarantined",
  absent: "\u2014 absent",
};

export default function Research() {
  const provenance = useApi<ProvenanceResponse>(endpoints.provenance);
  const artifacts = useApi<ArtifactsResponse>(endpoints.artifacts);
  const { health } = useHealth();

  return (
    <div>
      <PageHeader
        title="Research"
        lede="Methodology, controls and artefact provenance"
        meta="Everything on this dashboard traces to a stored research output"
      />

      <QueryBoundary
        loading={provenance.loading}
        error={provenance.error}
        data={provenance.data}
        height={400}
      >
        {(data) => (
          <>
            <SectionHeading title="Study" />
            <Card>
              <CardTitle>{data.study.title}</CardTitle>
              <CardHint className="mb-4">
                Comparing machine-learning and time-series approaches for
                day-ahead EV charging demand forecasting.
              </CardHint>
              <dl className="grid gap-x-8 gap-y-3 sm:grid-cols-2">
                {[
                  ["Dataset", data.study.dataset],
                  ["Train / validation / test", data.study.split],
                  ["Forecasting", data.study.forecasting],
                  ["Statistical testing", data.study.statisticalTesting],
                  ["Explainability", data.study.explainability],
                  ["Robustness", data.study.robustness],
                ].map(([key, value]) => (
                  <div key={key}>
                    <dt className="text-2xs uppercase tracking-wider text-muted">
                      {key}
                    </dt>
                    <dd className="mt-0.5 text-sm">{value}</dd>
                  </div>
                ))}
              </dl>
              <div className="mt-5">
                <p className="text-2xs uppercase tracking-wider text-muted">
                  Models
                </p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {data.study.models.map((m) => (
                    <Badge key={m} tone={m.includes("SARIMAX") ? "rose" : "neutral"}>
                      {m}
                    </Badge>
                  ))}
                </div>
              </div>
            </Card>

            <SectionHeading title="Target construction" />
            <ResearchNote title="Retrospective reconstruction.">
              {data.statements.targetLimitation}
            </ResearchNote>

            <SectionHeading title="Methodology flow" />
            <Card>
              <ol className="space-y-1.5">
                {FLOW.map((step, i) => (
                  <li key={step}>
                    <div className="rounded-lg border border-black/[0.08] border-l-2 border-l-signal bg-black/[0.02] px-3.5 py-2.5 text-sm">
                      {step}
                    </div>
                    {i < FLOW.length - 1 && (
                      <div className="ml-5 h-3 w-px bg-signal/25" aria-hidden />
                    )}
                  </li>
                ))}
              </ol>
            </Card>

            <SectionHeading title="Limitations" />
            <div className="grid gap-3 xl:grid-cols-2">
              {data.limitations.map((limit) => (
                <Card key={limit.title}>
                  <p className="font-display text-sm font-semibold">{limit.title}</p>
                  <p className="mt-1.5 text-sm leading-relaxed text-muted">
                    {limit.body}
                  </p>
                </Card>
              ))}
            </div>

            <SectionHeading
              title="Artifact provenance"
              hint="Which results are audited pipeline outputs"
            />
            <Card>
              <DataTable
                columns={["Result", "Status", "Path", "Role"]}
                rows={data.rows.map((row) => ({
                  Result: row.result,
                  Status: STATUS_GLYPH[row.status] ?? row.status,
                  Path: row.path,
                  Role: row.role,
                }))}
              />
            </Card>
          </>
        )}
      </QueryBoundary>

      <SectionHeading
        title="Artifact status"
        hint="Live check of every expected file"
      />
      <Card>
        <QueryBoundary
          loading={artifacts.loading}
          error={artifacts.error}
          data={artifacts.data}
          height={400}
        >
          {(data) => (
            <>
              <DataTable
                columns={["Artefact", "Group", "Status", "Rows", "Path", "Produced by"]}
                rows={data.artifacts.map((row) => ({
                  "Artefact": row.label,
                  Group: row.group,
                  Status: STATUS_GLYPH[row.status] ?? row.status,
                  Rows: row.rows,
                  Path: row.path,
                  "Produced by": row.producedBy,
                }))}
              />
              <p className="mt-3 text-xs text-muted">
                Repository root: <span className="font-mono">{data.repositoryRoot}</span>
                {health && ` · ${health.artifactsAvailable} of ${health.artifactsTotal} artefacts available`}
              </p>

              <div className="mt-5">
                <CardTitle>Directories</CardTitle>
                <CardHint className="mb-3">Scanned for supporting outputs</CardHint>
                <DataTable
                  columns={["Label", "Path", "Pattern", "Files", "Status"]}
                  rows={data.directories.map((d) => ({
                    Label: d.label,
                    Path: d.path,
                    Pattern: d.pattern,
                    Files: d.fileCount,
                    Status: STATUS_GLYPH[d.status] ?? d.status,
                  }))}
                />
              </div>
            </>
          )}
        </QueryBoundary>
      </Card>

      <div className="mt-6 space-y-3">
        <ResearchNote title="Read-only.">
          This dashboard never writes to data/ or results/, never retrains a
          model and never substitutes a value for a missing artefact.
        </ResearchNote>
      </div>
    </div>
  );
}
