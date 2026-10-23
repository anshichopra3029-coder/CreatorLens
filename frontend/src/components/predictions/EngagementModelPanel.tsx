import { useState } from "react";
import type { FormEvent } from "react";
import { QueryPanel } from "../common/QueryPanel.tsx";
import { useApiQuery } from "../../hooks/useApiQuery.ts";
import {
  listEngagementModels,
  listTrainingDatasets,
  predictEngagement,
  trainFromDemo,
  trainFromDocument,
} from "../../services/engagement.ts";
import type { EngagementModelInfo, EngagementPrediction, PredictionInput } from "../../types/engagement.ts";

export function EngagementModelPanel() {
  const [reloadKey, setReloadKey] = useState(0);
  const models = useApiQuery(() => listEngagementModels(), `engagement-models-${reloadKey}`);
  const datasets = useApiQuery(() => listTrainingDatasets(), "engagement-datasets");
  const [documentId, setDocumentId] = useState("");
  const [training, setTraining] = useState(false);
  const [trainError, setTrainError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState("");

  async function train(source: "document" | "demo") {
    setTraining(true);
    setTrainError(null);
    try {
      const info = source === "demo" ? await trainFromDemo() : await trainFromDocument(documentId);
      setSelectedId(info.model_id);
      setReloadKey((value) => value + 1);
    } catch (caught: unknown) {
      setTrainError(caught instanceof Error ? caught.message : "Training didn't work. Please try again.");
    } finally {
      setTraining(false);
    }
  }

  const allDatasets = datasets.status === "success" ? datasets.data.datasets : [];
  const eligible = allDatasets.filter((item) => item.check.eligible);
  const ineligible = allDatasets.filter((item) => !item.check.eligible);
  const chosen = allDatasets.find((item) => item.document_id === documentId);

  return (
    <section className="card space-y-5 p-5">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Engagement predictor</p>
        <h2 className="mt-1 text-base font-semibold">Estimate a post's engagement before you publish it</h2>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
          It learns from your past posts in a saved CSV, then estimates how many people will like, comment, or share
          compared with how many view. It only uses things you know before posting: platform, category, posting day and
          time, title, and length. We try a few methods, test each on posts we kept aside (your most recent ones when
          dates are available), and keep the most accurate one. (Technical: target = (likes + comments + shares) / views × 100; methods compared are a mean
          baseline, a decision tree, a random forest, and XGBoost.)
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-3">
        <label className="min-w-64 flex-1">
          <span className="field-label">Your saved posts CSV</span>
          <select className="field" value={documentId} onChange={(event) => setDocumentId(event.target.value)}>
            <option value="">
              {datasets.status === "loading"
                ? "Checking your saved CSV files…"
                : eligible.length === 0
                  ? "None of your saved CSVs can be used yet"
                  : "Choose a saved posts CSV"}
            </option>
            {eligible.map((item) => (
              <option key={item.document_id} value={item.document_id}>
                {item.filename} · {item.check.usable_rows} posts · {item.created_at.slice(0, 10)}
              </option>
            ))}
            {ineligible.map((item) => (
              <option key={item.document_id} value={item.document_id} disabled>
                {item.filename} · can't be used
              </option>
            ))}
          </select>
        </label>
        <button type="button" className="btn-primary" disabled={!documentId || training} onClick={() => void train("document")}>
          {training ? "Training…" : "Train model"}
        </button>
        <button type="button" className="btn-secondary" disabled={training} onClick={() => void train("demo")}>
          Try the demo posts
        </button>
      </div>
      <p className="text-xs text-slate-500">
        First upload a CSV of your posts on the Upload Dataset page. It needs at least 30 posts, each with more than zero
        views, and columns for views, likes, and comments.
      </p>
      {chosen ? <p className="text-sm text-emerald-800">{chosen.check.message}</p> : null}
      {datasets.status === "error" ? (
        <p className="text-sm text-red-700" role="alert">
          {datasets.error}
        </p>
      ) : null}
      {ineligible.length > 0 ? (
        <details className="text-sm text-slate-600">
          <summary className="cursor-pointer font-medium text-slate-800">
            {ineligible.length} saved CSV {ineligible.length === 1 ? "file can't" : "files can't"} be used yet (see why)
          </summary>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            {ineligible.map((item) => (
              <li key={item.document_id}>
                <span className="font-medium">{item.filename}</span>: {item.check.message}
              </li>
            ))}
          </ul>
        </details>
      ) : null}
      {trainError ? (
        <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900" role="alert">
          {trainError}
        </p>
      ) : null}

      <QueryPanel
        query={models}
        loadingLabel="Loading your trained predictors…"
        emptyTitle="No predictor trained yet"
        emptyBody="Train one from a saved posts CSV, or try the demo posts. We won't show any estimate until a predictor has been trained and tested."
        isEmpty={(data) => data.models.length === 0}
      >
        {(data) => {
          const active = data.models.find((item) => item.model_id === selectedId) ?? data.models[0];
          return (
            <div className="space-y-5">
              <label className="block max-w-md">
                <span className="field-label">Trained predictor</span>
                <select className="field" value={active.model_id} onChange={(event) => setSelectedId(event.target.value)}>
                  {data.models.map((item) => (
                    <option key={item.model_id} value={item.model_id}>
                      {item.source_label} · {item.selected_label} · {item.trained_at.slice(0, 16).replace("T", " ")}
                    </option>
                  ))}
                </select>
              </label>
              <ModelReport info={active} />
              <PredictionForm key={active.model_id + active.trained_at} info={active} />
            </div>
          );
        }}
      </QueryPanel>
    </section>
  );
}

function ModelReport({ info }: { info: EngagementModelInfo }) {
  const maxImportance = Math.max(0.0001, ...info.importance.map((item) => Math.abs(item.importance)));
  return (
    <div className="space-y-4">
      <div className="grid gap-4 lg:grid-cols-2">
        <div>
          <h3 className="text-sm font-semibold">How accurate it was in testing</h3>
          <p className="mt-1 text-xs text-slate-500">
            Learned from {info.train_rows} posts, then tested on {info.holdout_rows} posts we kept aside
            {info.split === "chronological" && info.holdout_start ? ` (your most recent, from ${info.holdout_start} onward)` : " (picked at random)"}.
            "Average miss" is how far off its guesses were, in engagement-rate points. Lower is better.
          </p>
          <table className="mt-3 w-full text-left text-sm">
            <thead className="text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="py-1.5 pr-3">Method</th>
                <th className="py-1.5 pr-3">Average miss (MAE)</th>
                <th className="py-1.5">Big-miss score (RMSE)</th>
              </tr>
            </thead>
            <tbody>
              {info.scores.map((score) => (
                <tr key={score.name} className={`border-t border-slate-200 ${score.name === info.selected_model ? "font-semibold text-indigo-800" : ""}`}>
                  <td className="py-1.5 pr-3">
                    {score.label}
                    {score.name === info.selected_model ? " · chosen" : ""}
                  </td>
                  <td className="py-1.5 pr-3">{score.mae.toFixed(2)}</td>
                  <td className="py-1.5">{score.rmse.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!info.beats_baseline ? (
            <p className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
              None of the methods did better than a simple average guess on the test posts, so this predictor won't make
              estimates. Try training it on more posts.
            </p>
          ) : null}
        </div>
        <div>
          <h3 className="text-sm font-semibold">Which inputs the model relies on</h3>
          <p className="mt-1 text-xs text-slate-500">
            A longer bar means the predictor leans on that input more. This shows a pattern, not a cause. (Technical:
            how much the average miss grows when each input is shuffled on the test posts.)
          </p>
          <ul className="mt-3 space-y-2">
            {info.importance.map((item) => (
              <li key={item.feature} className="text-sm">
                <div className="flex justify-between gap-3">
                  <span>{item.label}</span>
                  <span className="text-slate-500">{item.importance.toFixed(2)} ± {item.spread.toFixed(2)}</span>
                </div>
                <div className="mt-1 h-2 rounded-full bg-slate-100">
                  <div
                    className="h-2 rounded-full bg-indigo-500"
                    style={{ width: `${Math.max(0, (item.importance / maxImportance) * 100)}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {info.observations.length > 0 ? (
        <div>
          <h3 className="text-sm font-semibold">Average engagement in your past posts</h3>
          <p className="mt-1 text-xs text-slate-500">Averages for each group in your file. They show patterns, not causes.</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {info.observations.map((item) => (
              <span key={`${item.feature}-${item.value}`} className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs text-slate-700">
                {item.value}: {item.mean_rate.toFixed(2)}% ({item.posts} posts)
              </span>
            ))}
          </div>
        </div>
      ) : null}

      <details className="text-sm text-slate-600">
        <summary className="cursor-pointer font-medium text-slate-800">Details and limits</summary>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          <li>Data: {info.source_label}. {info.rows_used} posts used, {info.rows_dropped} couldn't be used.</li>
          {info.drop_reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
          <li>
            What it predicts: engagement rate ({info.target_formula}). In your past posts the average was{" "}
            {info.target_summary.mean.toFixed(2)}% and the middle value (median) was {info.target_summary.median.toFixed(2)}%.
          </li>
          <li>What it looks at: {info.features.map((feature) => info.feature_labels[feature] ?? feature).join(", ")}.</li>
          {info.excluded_columns.length > 0 ? <li>Results it never looks at (to keep it fair): {info.excluded_columns.join(", ")}.</li> : null}
          {info.limitations.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </details>
    </div>
  );
}

function PredictionForm({ info }: { info: EngagementModelInfo }) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EngagementPrediction | null>(null);
  const uses = (feature: string) => info.features.includes(feature as EngagementModelInfo["features"][number]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setResult(null);
    const input: PredictionInput = {};
    if (uses("platform")) input.platform = values.platform ?? "";
    if (uses("category")) input.category = values.category ?? "";
    if (uses("posted_at")) input.posted_at = values.posted_at ?? "";
    if (uses("posting_hour") && values.posting_hour) input.posting_hour = Number(values.posting_hour);
    if (uses("title")) input.title = values.title ?? "";
    if (uses("duration_seconds") && values.duration_seconds) input.duration_seconds = Number(values.duration_seconds);
    try {
      setResult(await predictEngagement(info.model_id, input));
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "We couldn't make an estimate. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  function set(name: string, value: string) {
    setValues((current) => ({ ...current, [name]: value }));
  }

  return (
    <div className="space-y-4 border-t border-slate-200 pt-4">
      <form className="grid gap-3 sm:grid-cols-2" onSubmit={(event) => void submit(event)}>
        {(["platform", "category"] as const).filter(uses).map((name) => (
          <label key={name}>
            <span className="field-label">{info.feature_labels[name]}</span>
            <input
              className="field"
              list={`${name}-options`}
              value={values[name] ?? ""}
              onChange={(event) => set(name, event.target.value)}
              required
            />
            <datalist id={`${name}-options`}>
              {(info.categories[name] ?? []).map((option) => (
                <option key={option} value={option} />
              ))}
            </datalist>
          </label>
        ))}
        {uses("posted_at") ? (
          <label>
            <span className="field-label">Planned posting date</span>
            <input className="field" type="date" value={values.posted_at ?? ""} onChange={(event) => set("posted_at", event.target.value)} required />
          </label>
        ) : null}
        {uses("posting_hour") ? (
          <label>
            <span className="field-label">Planned posting hour (0–23)</span>
            <input className="field" type="number" min={0} max={23} step={1} value={values.posting_hour ?? ""} onChange={(event) => set("posting_hour", event.target.value)} required />
          </label>
        ) : null}
        {uses("duration_seconds") ? (
          <label>
            <span className="field-label">Duration (seconds)</span>
            <input className="field" type="number" min={0} value={values.duration_seconds ?? ""} onChange={(event) => set("duration_seconds", event.target.value)} required />
          </label>
        ) : null}
        {uses("title") ? (
          <label className="sm:col-span-2">
            <span className="field-label">Planned title</span>
            <input className="field" maxLength={300} value={values.title ?? ""} onChange={(event) => set("title", event.target.value)} required />
          </label>
        ) : null}
        <div className="sm:col-span-2">
          <button type="submit" className="btn-primary" disabled={busy || !info.beats_baseline}>
            {busy ? "Estimating…" : "Estimate engagement"}
          </button>
        </div>
      </form>

      {error ? (
        <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900" role="alert">
          {error}
        </p>
      ) : null}
      {result ? <PredictionResult result={result} /> : null}
    </div>
  );
}

function PredictionResult({ result }: { result: EngagementPrediction }) {
  const maxContribution = Math.max(0.0001, ...(result.contributions ?? []).map((item) => Math.abs(item.value)));
  return (
    <div className="space-y-4 rounded-xl border border-indigo-200 bg-indigo-50/60 p-4" role="status">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-indigo-700">Estimated engagement rate · {result.model_label}</p>
          <p className="mt-1 text-3xl font-semibold tracking-tight text-slate-900">{result.predicted_engagement_rate.toFixed(2)}%</p>
          <p className="mt-1 text-sm text-slate-600">
            In testing, its guesses were off by about {result.typical_error.toFixed(2)} points on average, so somewhere
            around {result.band_low.toFixed(2)}% to {result.band_high.toFixed(2)}% is realistic. That's based on past
            misses, not a guaranteed range.
          </p>
        </div>
        <div className="text-sm text-slate-600">
          <p>Your past posts averaged {result.historical.training_mean.toFixed(2)}%</p>
          <p>Middle value (median): {result.historical.training_median.toFixed(2)}%</p>
          {result.historical.matching_groups.map((group) => (
            <p key={`${group.feature}-${group.value}`}>
              {group.value} posts averaged {group.mean_rate.toFixed(2)}% ({group.posts} posts)
            </p>
          ))}
        </div>
      </div>
      <p className="text-xs text-slate-500">Engagement rate = {result.target_formula}</p>

      {result.warnings.length > 0 ? (
        <ul className="list-disc space-y-1 pl-5 text-sm text-amber-900">
          {result.warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      ) : null}

      <div>
        <h3 className="text-sm font-semibold">What pushed this estimate up or down</h3>
        <p className="mt-1 text-xs text-slate-500">{result.contribution_note}</p>
        {result.contributions && result.base_value !== null ? (
          <ul className="mt-3 space-y-2">
            <li className="text-sm text-slate-600">Starting point before any inputs: {result.base_value.toFixed(2)}%</li>
            {result.contributions.map((item) => (
              <li key={item.feature} className="text-sm">
                <div className="flex justify-between gap-3">
                  <span>{item.label}</span>
                  <span className={item.value >= 0 ? "text-emerald-700" : "text-rose-700"}>
                    {item.value >= 0 ? "+" : ""}
                    {item.value.toFixed(2)}
                  </span>
                </div>
                <div className="mt-1 h-2 rounded-full bg-white">
                  <div
                    className={`h-2 rounded-full ${item.value >= 0 ? "bg-emerald-500" : "bg-rose-500"}`}
                    style={{ width: `${(Math.abs(item.value) / maxContribution) * 100}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        ) : null}
      </div>
      <p className="text-xs text-slate-600">{result.disclaimer}</p>
    </div>
  );
}
