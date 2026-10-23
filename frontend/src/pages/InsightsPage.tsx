import { DemoBanner, MetricCaption } from "../components/common/DemoBanner.tsx";
import { QueryPanel } from "../components/common/QueryPanel.tsx";
import { useApiQuery } from "../hooks/useApiQuery.ts";
import { getInsights } from "../services/api.ts";
import { ActiveDocumentSwitch } from "../components/documents/ActiveDocumentSwitch.tsx";

export function InsightsPage() {
  return <ActiveDocumentSwitch demo={<InsightsDemo />} />;
}

function InsightsDemo() {
  const insights = useApiQuery(() => getInsights(), "insights");

  return (
    <div className="space-y-6">
      <DemoBanner>
        These are example insights from the built-in demo data. They describe patterns, not proven causes.
      </DemoBanner>
      <QueryPanel
        query={insights}
        loadingLabel="Loading demo insights…"
        emptyTitle="No demo insights"
        emptyBody="The demo data didn't produce any insights."
        isEmpty={(data) => data.cards.length === 0}
      >
        {(data) => (
          <div className="space-y-4">
            <p className="max-w-3xl text-sm leading-6 text-slate-600">{data.disclaimer}</p>
            <MetricCaption formula={data.metric_formula} />
            <div className="grid gap-4 lg:grid-cols-2">
              {data.cards.map((card) => (
                <article key={card.id} className="card p-5">
                  <p className="text-xs font-semibold uppercase tracking-wide text-amber-800">Example insight (demo data)</p>
                  <h2 className="mt-2 text-lg font-semibold">{card.title}</h2>
                  <p className="mt-3 text-sm leading-6 text-slate-800">{card.summary}</p>
                  <p className="mt-3 text-sm leading-6 text-slate-600">{card.evidence}</p>
                </article>
              ))}
            </div>
          </div>
        )}
      </QueryPanel>
    </div>
  );
}
