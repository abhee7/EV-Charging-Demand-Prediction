import { useState } from "react";

import { endpoints } from "@/api/endpoints";
import { ImportanceBars } from "@/charts/ImportanceBars";
import { COLORS } from "@/charts/theme";
import { PageHeader } from "@/components/PageHeader";
import { QueryBoundary } from "@/components/QueryBoundary";
import { ResearchNote } from "@/components/ResearchNote";
import { SectionHeading } from "@/components/SectionHeading";
import { StatTile } from "@/components/StatTile";
import { Card, CardHint, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { Tabs } from "@/components/ui/tabs";
import { useApi } from "@/hooks/useApi";
import { num } from "@/lib/format";
import type { CombinedShap, ImportanceResponse } from "@/types/api";

const SOURCES = [
  { key: "shap", label: "SHAP importance" },
  { key: "importance", label: "Built-in model importance" },
];

const SOURCE_HELP: Record<string, string> = {
  shap: "SHAP attributes each prediction to its inputs, then averages the absolute attribution. It is model-agnostic and measures how much a feature moved predictions.",
  importance:
    "Tree ensembles expose their own importance from the splitting process. Random Forest and XGBoost compute it differently, so these scores compare within a model rather than between models.",
};

export default function Explainability() {
  const [source, setSource] = useState("shap");
  const [feature, setFeature] = useState<string | null>(null);

  const combined = useApi<CombinedShap>(endpoints.shap);
  const rf = useApi<ImportanceResponse>(endpoints.randomForest, { source });
  const xgb = useApi<ImportanceResponse>(endpoints.xgboost, { source });

  const selectedDetail = (() => {
    if (!feature) return null;
    for (const response of [rf.data, xgb.data]) {
      const hit = response?.features?.find((f) => f.feature === feature);
      if (hit) return { ...hit, model: response?.model };
    }
    return null;
  })();

  return (
    <div>
      <PageHeader
        title="Explainability"
        lede="What the models' predictions are associated with"
        meta="SHAP and built-in importance, read from the research exports"
      />

      <ResearchNote title="Not causal inference.">
        SHAP describes model contribution, not causality. A large contribution
        does not establish that the feature causes demand.
      </ResearchNote>

      <SectionHeading title="SHAP overview" hint="Combined mean absolute SHAP" />
      <Card>
        <QueryBoundary
          loading={combined.loading}
          error={combined.error}
          data={combined.data}
          height={360}
        >
          {(data) => (
            <>
              <CombinedShapView data={data} onSelect={setFeature} selected={feature} />
              {data.interpretation && (
                <p className="mt-3 text-xs leading-relaxed text-muted">
                  {data.interpretation}
                </p>
              )}
            </>
          )}
        </QueryBoundary>
      </Card>

      <SectionHeading
        title="Feature importance vs SHAP"
        hint="Switch the attribution source"
      />
      <Tabs items={SOURCES} value={source} onChange={setSource} className="mb-4" />
      <p className="mb-4 text-xs leading-relaxed text-muted">{SOURCE_HELP[source]}</p>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardTitle>Random Forest</CardTitle>
          <CardHint className="mb-3">
            {source === "shap" ? "Mean absolute SHAP" : "Built-in importance"}
          </CardHint>
          <QueryBoundary loading={rf.loading} error={rf.error} data={rf.data} height={380}>
            {(data) => (
              <ImportanceBars
                features={data.features ?? []}
                color={COLORS.prediction}
                valueLabel={data.valueColumn ?? "Value"}
                selected={feature}
                onSelect={setFeature}
              />
            )}
          </QueryBoundary>
        </Card>

        <Card>
          <CardTitle>XGBoost</CardTitle>
          <CardHint className="mb-3">
            {source === "shap" ? "Mean absolute SHAP" : "Built-in importance"}
          </CardHint>
          <QueryBoundary loading={xgb.loading} error={xgb.error} data={xgb.data} height={380}>
            {(data) => (
              <ImportanceBars
                features={data.features ?? []}
                color={COLORS.signal}
                valueLabel={data.valueColumn ?? "Value"}
                selected={feature}
                onSelect={setFeature}
              />
            )}
          </QueryBoundary>
        </Card>
      </div>

      <SectionHeading
        title="Feature explorer"
        hint="Select a feature, or click a bar above"
      />
      <Card>
        <div className="mb-4 max-w-sm">
          <Select
            label="Feature"
            value={feature ?? ""}
            onChange={(e) => setFeature(e.target.value || null)}
          >
            <option value="">Select a feature…</option>
            {(rf.data?.features ?? xgb.data?.features ?? []).map((f) => (
              <option key={f.feature} value={f.feature}>
                {f.feature}
              </option>
            ))}
          </Select>
        </div>

        {selectedDetail ? (
          <>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              <StatTile label="Feature" value={selectedDetail.feature} />
              <StatTile
                label={source === "shap" ? "Mean absolute SHAP" : "Importance"}
                value={num(selectedDetail.value, 6)}
              />
              <StatTile label="Model" value={selectedDetail.model ?? "—"} />
            </div>
            <div className="mt-4 rounded-xl border border-black/[0.08] border-l-2 border-l-signal bg-black/[0.02] p-4">
              <p className="font-mono text-sm text-signal">{selectedDetail.feature}</p>
              <p className="mt-2 text-sm leading-relaxed text-ink/90">
                {selectedDetail.description ??
                  "This feature is part of the engineered feature set. See the Research page for the full feature definitions."}
              </p>
            </div>
          </>
        ) : (
          <p className="text-sm text-muted">
            Choose a feature to see its contribution and a plain-language
            description.
          </p>
        )}
      </Card>

      <div className="mt-6">
        <ResearchNote title="Reading these results.">
          SHAP values describe model contribution and should not be interpreted
          as causal effects.
        </ResearchNote>
      </div>
    </div>
  );
}

function CombinedShapView({
  data,
  onSelect,
  selected,
}: {
  data: CombinedShap;
  onSelect: (feature: string) => void;
  selected: string | null;
}) {
  const groups = data.groups ?? [];
  const [group, setGroup] = useState("");
  const active = group || groups[0]?.model || "";
  const current = groups.find((g) => g.model === active);

  return (
    <>
      {groups.length > 1 && (
        <div className="mb-4 max-w-xs">
          <Select label="Model" value={active} onChange={(e) => setGroup(e.target.value)}>
            {groups.map((g) => (
              <option key={g.model} value={g.model}>
                {g.model}
              </option>
            ))}
          </Select>
        </div>
      )}
      <ImportanceBars
        features={current?.features ?? []}
        color={COLORS.signal}
        valueLabel="Mean |SHAP|"
        selected={selected}
        onSelect={onSelect}
      />
    </>
  );
}
