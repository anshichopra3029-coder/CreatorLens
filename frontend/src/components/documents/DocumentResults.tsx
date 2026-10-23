import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { CategoryComparisonChart } from "../charts/CategoryComparisonChart.tsx";
import { EngagementTrendChart } from "../charts/EngagementTrendChart.tsx";
import { QueryPanel } from "../common/QueryPanel.tsx";
import { KpiCard } from "../dashboard/KpiCard.tsx";
import { useApiQuery } from "../../hooks/useApiQuery.ts";
import { askDocument, getDocument } from "../../services/documents.ts";
import { formatBytes, formatNumber, formatRate } from "../../services/format.ts";
import type { DocumentAnalysis } from "../../types/documents.ts";
import type { GroupMetric, TrendPoint } from "../../types/api.ts";

function BulletList({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) {
    return null;
  }
  return (
    <section className="card p-5">
      <h2 className="text-base font-semibold">{title}</h2>
      <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-700">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

function toCategories(document: DocumentAnalysis): GroupMetric[] {
  return (document.csv_profile?.categories ?? []).map((item) => ({
    name: item.name,
    post_count: item.count,
    avg_engagement_rate: item.avg_engagement_rate,
    total_interactions: item.total_interactions ?? 0,
    avg_views: null,
  }));
}

function toTrends(document: DocumentAnalysis): TrendPoint[] {
  return (document.csv_profile?.trends ?? []).map((item) => ({
    period: item.period,
    label: item.label,
    avg_engagement_rate: item.avg_engagement_rate,
    post_count: item.count,
    total_interactions: item.total_interactions ?? 0,
  }));
}

export function DocumentResults({ documentId }: { documentId: string }) {
  const query = useApiQuery(() => getDocument(documentId), documentId);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [askError, setAskError] = useState<string | null>(null);

  async function onAsk(event: FormEvent, reload: () => void) {
    event.preventDefault();
    const text = question.trim();
    if (text === "") {
      return;
    }
    setAsking(true);
    setAskError(null);
    try {
      await askDocument(documentId, text);
      setQuestion("");
      reload();
    } catch (error: unknown) {
      setAskError(error instanceof Error ? error.message : "We couldn't answer that question. Please try again.");
    } finally {
      setAsking(false);
    }
  }

  return (
    <QueryPanel
      query={query}
      loadingLabel="Loading your saved analysis…"
      emptyTitle="Analysis not found"
      emptyBody="This saved analysis isn't available any more."
      isEmpty={() => false}
    >
      {(data) => <AnalysisBody data={data} question={question} setQuestion={setQuestion} asking={asking} askError={askError} onAsk={onAsk} reload={query.reload} />}
    </QueryPanel>
  );
}

function AnalysisBody({
  data,
  question,
  setQuestion,
  asking,
  askError,
  onAsk,
  reload,
}: {
  data: DocumentAnalysis;
  question: string;
  setQuestion: (value: string) => void;
  asking: boolean;
  askError: string | null;
  onAsk: (event: FormEvent, reload: () => void) => void;
  reload: () => void;
}) {
  const profile = data.csv_profile;
  const categories = toCategories(data);
  const trends = toTrends(data);
  return (
    <div className="space-y-6">
      <section className="card p-5">
        <p className="text-xs font-semibold uppercase tracking-wide text-indigo-700">Saved analysis</p>
        <h2 className="mt-2 text-xl font-semibold">{data.filename}</h2>
        <p className="mt-2 text-sm text-slate-600">
          {data.format.toUpperCase()} · {formatBytes(data.size_bytes)} · Saved {data.created_at}
        </p>
        <p className="mt-3 text-sm leading-6 text-slate-700">{data.narrative_message}</p>
        {data.file_saved ? <p className="mt-2 text-sm font-medium text-emerald-800">Your file and its analysis are saved.</p> : null}
        <div className="mt-4 flex flex-wrap gap-3">
          <Link to="/upload" className="btn-secondary">
            Upload another document
          </Link>
          <Link to="/documents" className="text-sm font-semibold text-indigo-700">
            View saved analyses
          </Link>
        </div>
      </section>

      {data.posts_dataset ? (
        <section
          className={`card p-5 ${data.posts_dataset.eligible ? "border-emerald-200 bg-emerald-50" : "border-amber-200 bg-amber-50"}`}
          role="status"
        >
          <h2 className="text-base font-semibold">
            {data.posts_dataset.eligible
              ? "Ready to train an engagement predictor"
              : "Can't be used to train an engagement predictor yet"}
          </h2>
          <p className="mt-2 text-sm leading-6 text-slate-800">{data.posts_dataset.message}</p>
          {data.posts_dataset.eligible ? (
            <Link to="/predictions" className="btn-primary mt-3">
              Train it on the Predictions page
            </Link>
          ) : null}
        </section>
      ) : null}

      {data.status === "unreadable" ? (
        <section className="card border-amber-200 bg-amber-50 p-5" role="status">
          <h2 className="text-base font-semibold text-amber-950">No readable text</h2>
          <p className="mt-2 text-sm leading-6 text-amber-950">{data.narrative_message}</p>
        </section>
      ) : null}

      {data.summary ? (
        <section className="card p-5">
          <h2 className="text-base font-semibold">Summary</h2>
          {data.subject ? <p className="mt-2 text-sm font-medium text-slate-800">{data.subject}</p> : null}
          <p className="mt-3 text-sm leading-6 text-slate-700">{data.summary}</p>
          {data.model ? <p className="mt-3 text-xs text-slate-500">Written by AI ({data.model})</p> : null}
        </section>
      ) : null}

      {profile?.engagement_available ? (
        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Calculated summary">
          <KpiCard label="Rows analyzed" value={formatNumber(profile.posts_analyzed ?? 0)} detail="Posts counted from your CSV" />
          <KpiCard label="Avg. engagement rate" value={formatRate(profile.avg_engagement_rate)} detail="On average, likes, comments, and shares compared with views" />
          <KpiCard label="Total interactions" value={formatNumber(profile.total_interactions ?? 0)} detail="All likes, comments, and shares added up" />
          <KpiCard label="Best category" value={profile.best_category ?? "—"} detail="The type of content with the most engagement" />
        </section>
      ) : null}

      {profile && !profile.engagement_available ? (
        <section className="card p-5">
          <h2 className="text-base font-semibold">What's in your file</h2>
          <p className="mt-2 text-sm text-slate-600">
            {formatNumber(profile.row_count)} rows and {formatNumber(profile.column_count)} columns. For each column you
            can see what kind of data it holds, how many cells are empty, and the average (for numbers).
          </p>
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <caption className="sr-only">Column statistics</caption>
              <thead className="text-slate-500">
                <tr>
                  <th className="py-2 pr-4 font-medium">Column</th>
                  <th className="py-2 pr-4 font-medium">Type</th>
                  <th className="py-2 pr-4 font-medium">Empty cells</th>
                  <th className="py-2 pr-4 font-medium">Average</th>
                </tr>
              </thead>
              <tbody>
                {profile.columns.map((column) => (
                  <tr key={column.name} className="border-t border-slate-200">
                    <td className="py-2 pr-4">{column.name}</td>
                    <td className="py-2 pr-4">{column.kind}</td>
                    <td className="py-2 pr-4">{column.missing_count}</td>
                    <td className="py-2 pr-4">{column.numeric_mean ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {categories.length > 0 || trends.length > 0 ? (
        <section className="grid gap-4 lg:grid-cols-5">
          {trends.length > 0 ? (
            <div className="card p-5 lg:col-span-3">
              <h2 className="text-base font-semibold">Engagement over time</h2>
              <p className="mb-4 mt-1 text-sm text-slate-500">Average engagement for each week, from your file.</p>
              <EngagementTrendChart
                points={trends}
                caption="Each point is one week's average from your CSV."
              />
            </div>
          ) : null}
          {categories.length > 0 ? (
            <div className="card p-5 lg:col-span-2">
              <h2 className="text-base font-semibold">Category comparison</h2>
              <p className="mb-4 mt-1 text-sm text-slate-500">Average engagement for each type of content.</p>
              <CategoryComparisonChart
                categories={categories}
                caption="Worked out from the categories in your CSV."
              />
            </div>
          ) : null}
        </section>
      ) : null}

      {profile && profile.anomalies.length > 0 ? (
        <section className="card p-5">
          <h2 className="text-base font-semibold">Unusual values</h2>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-700">
            {profile.anomalies.map((item) => (
              <li key={`${item.column}-${item.row_number}`}>
                Row {item.row_number}, {item.column}: {item.value}. {item.reason}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <BulletList title="Main points" items={data.main_points} />
        <BulletList title="Key findings" items={data.key_findings} />
        <BulletList title="Facts and figures" items={data.facts} />
        <BulletList title="Dates" items={data.dates} />
        <BulletList title="People, brands, and places" items={data.entities} />
        <BulletList title="Risks and issues" items={data.risks} />
        <BulletList title="Recommendations" items={data.recommendations} />
      </div>

      {data.text_preview ? (
        <section className="card p-5">
          <h2 className="text-base font-semibold">Text we read from your file</h2>
          <pre className="mt-3 max-h-64 overflow-auto whitespace-pre-wrap text-sm leading-6 text-slate-700">{data.text_preview}</pre>
        </section>
      ) : null}

      <section className="card p-5">
        <h2 className="text-base font-semibold">Ask about this document</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Ask anything about this file. Answers only use what's written in it, and will say so if the answer isn't there.
        </p>
        <form className="mt-4 flex flex-col gap-3 sm:flex-row" onSubmit={(event) => onAsk(event, reload)}>
          <label className="sr-only" htmlFor="document-question">
            Question
          </label>
          <input
            id="document-question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            maxLength={500}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            placeholder="Ask a question about this file"
          />
          <button type="submit" className="btn-primary" disabled={asking || question.trim() === ""}>
            {asking ? "Asking…" : "Ask"}
          </button>
        </form>
        {askError ? (
          <p className="mt-3 text-sm text-red-700" role="alert">
            {askError}
          </p>
        ) : null}
        <div className="mt-5 space-y-4">
          {data.questions.length === 0 ? <p className="text-sm text-slate-500">No questions yet.</p> : null}
          {data.questions.map((item) => (
            <article key={item.id} className="rounded-lg border border-slate-200 p-4">
              <h3 className="text-sm font-semibold">{item.question}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-700">{item.answer}</p>
              <p className="mt-2 text-sm text-slate-600">From your file: {item.cited_evidence}</p>
              <p className="mt-1 text-sm text-slate-500">{item.uncertainty_note}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
