import { useState } from "react";
import { Link } from "react-router-dom";
import { QueryPanel } from "../common/QueryPanel.tsx";
import { ForecastChart } from "../youtube/YoutubeCharts.tsx";
import { useApiQuery } from "../../hooks/useApiQuery.ts";
import { formatNumber } from "../../services/format.ts";
import { getVideoForecast, importVideoHistory, recordVideoSnapshot } from "../../services/youtube.ts";
import type { PredictionResult, VideoForecastResponse } from "../../types/prediction.ts";

const CSV_EXAMPLE = `observed_at,views
2026-10-01T09:00:00Z,1200
2026-10-02T09:00:00Z,1850
2026-10-03,2400`;

export function VideoForecastPanel({ videoId, onChanged }: { videoId: string; onChanged: () => void }) {
  const [version, setVersion] = useState(0);
  const forecast = useApiQuery(() => getVideoForecast(videoId), `${videoId}-${version}`);
  const [busy, setBusy] = useState<"snapshot" | "import" | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionNote, setActionNote] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);

  function refresh() {
    setVersion((value) => value + 1);
    onChanged();
  }

  async function snapshot() {
    setBusy("snapshot");
    setActionError(null);
    setActionNote(null);
    try {
      const result = await recordVideoSnapshot(videoId);
      const latest = result.observations[result.observations.length - 1];
      setActionNote(latest ? `Saved ${formatNumber(latest.views)} views at ${formatTimestamp(latest.observed_at)}.` : "Snapshot saved.");
      refresh();
    } catch (caught: unknown) {
      setActionError(caught instanceof Error ? caught.message : "We couldn't save a snapshot. Please try again.");
    } finally {
      setBusy(null);
    }
  }

  async function importFile() {
    if (!file) {
      return;
    }
    setBusy("import");
    setActionError(null);
    setActionNote(null);
    try {
      const result = await importVideoHistory(videoId, file);
      setActionNote(
        [`Imported ${result.inserted} view count(s).`, result.skipped_existing ? `${result.skipped_existing} were already saved.` : "", ...result.warnings]
          .filter(Boolean)
          .join(" "),
      );
      setFile(null);
      refresh();
    } catch (caught: unknown) {
      setActionError(caught instanceof Error ? caught.message : "The import didn't work. Please try again.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <QueryPanel query={forecast} loadingLabel="Working out the forecast from your saved view counts…" emptyTitle="Forecast not available" emptyBody="" isEmpty={() => false}>
      {(data) => (
        <div className="space-y-4">
          <ForecastSummary title={data.title} subtitle={data.channel_title} prediction={data.prediction} />
          {data.prediction.status === "forecast" ? (
            <ForecastChart
              eligible
              message={data.prediction.message}
              limitations={data.prediction.limitations}
              series={data.prediction.series}
              method={data.prediction.model_label ?? data.prediction.method}
            />
          ) : data.prediction.series.length >= 2 ? (
            <ForecastChart
              eligible
              message="Your saved view counts so far. A forecast line appears once there's enough history."
              limitations="Only real saved counts are shown."
              series={data.prediction.series}
              method="no forecast yet"
            />
          ) : null}
          <HistoryActions
            data={data}
            busy={busy}
            file={file}
            onFile={setFile}
            onSnapshot={() => void snapshot()}
            onImport={() => void importFile()}
            error={actionError}
            note={actionNote}
          />
          <Link to={`/youtube/${data.latest_analysis_id}`} className="text-sm font-semibold text-indigo-700">
            Open this video's latest analysis
          </Link>
        </div>
      )}
    </QueryPanel>
  );
}

function formatTimestamp(value: string): string {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString();
}

export function ForecastSummary({ title, subtitle, prediction }: { title: string; subtitle?: string; prediction: PredictionResult }) {
  const horizons = prediction.horizons ?? [];
  const metrics = prediction.metrics ?? [];
  return (
    <section className="card space-y-4 p-5">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Views forecast</p>
        <h2 className="mt-1 text-lg font-semibold">{title}</h2>
        {subtitle ? <p className="text-sm text-slate-500">{subtitle}</p> : null}
      </div>

      {prediction.status !== "forecast" ? (
        <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm leading-6 text-amber-950" role="status">
          {prediction.message}
        </p>
      ) : null}

      {prediction.latest_views !== null && prediction.latest_views !== undefined ? (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-lg border border-slate-200 p-3">
              <p className="text-xs uppercase tracking-wide text-slate-500">Latest saved views</p>
              <p className="mt-1 text-xl font-semibold">{formatNumber(prediction.latest_views)}</p>
              <p className="text-xs text-slate-500">
                {prediction.latest_observed_at ? `Saved ${formatTimestamp(prediction.latest_observed_at)}` : ""}
              </p>
            </div>
            {horizons.map((item) => (
              <div key={item.label} className={`rounded-lg border p-3 ${item.supported ? "border-indigo-200 bg-indigo-50/50" : "border-slate-200 bg-slate-50"}`}>
                <p className="text-xs uppercase tracking-wide text-slate-500">In {item.label}</p>
                {item.supported && item.predicted_views !== null ? (
                  <>
                    <p className="mt-1 text-xl font-semibold">{formatNumber(item.predicted_views)}</p>
                    <p className="text-xs text-slate-600">
                      +{formatNumber(item.added_views ?? 0)} views
                      {item.growth_percent !== null ? ` · +${item.growth_percent.toFixed(2)}%` : ""}
                    </p>
                  </>
                ) : (
                  <p className="mt-1 text-xs leading-5 text-slate-500">{item.note}</p>
                )}
              </div>
            ))}
          </div>
      ) : null}

      {prediction.status === "forecast" ? (
        <>
          <div className="space-y-1 text-sm text-slate-700">
            <p>
              <span className="font-semibold">Forecast method:</span> {prediction.model_label ?? prediction.method}
              {prediction.selection === "provisional" ? (
                <span className="ml-2 rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-xs text-amber-900">Early estimate</span>
              ) : prediction.selection === "evaluated" ? (
                <span className="ml-2 rounded-full border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-xs text-emerald-900">Tested on your data</span>
              ) : null}
            </p>
            {prediction.selection_reason ? <p className="text-slate-600">{prediction.selection_reason}</p> : null}
          </div>

          {metrics.length > 0 ? (
            <table className="w-full max-w-xl text-left text-sm">
              <thead className="text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="py-1.5 pr-3">Method</th>
                  <th className="py-1.5 pr-3">Average miss (views)</th>
                  <th className="py-1.5 pr-3">Miss compared with real growth</th>
                  <th className="py-1.5">Times tested</th>
                </tr>
              </thead>
              <tbody>
                {metrics.map((metric) => (
                  <tr key={metric.name} className={`border-t border-slate-200 ${prediction.method === metric.name ? "font-semibold text-indigo-800" : ""}`}>
                    <td className="py-1.5 pr-3">{metric.label}</td>
                    <td className="py-1.5 pr-3">{metric.available && metric.mae !== null ? formatNumber(metric.mae) : "—"}</td>
                    <td className="py-1.5 pr-3">{metric.available && metric.growth_wape !== null ? `${metric.growth_wape.toFixed(1)}%` : "—"}</td>
                    <td className="py-1.5">{metric.available ? metric.pairs : metric.note || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
          <p className="text-xs leading-5 text-slate-500">
            "Average miss" is how far off each method was, in views, when we tested it on your later real counts
            (technical: MAE from a rolling back-test). "Miss compared with real growth" is the total miss divided by the
            views actually gained, so it still makes sense for big videos. Past accuracy doesn't guarantee future
            results; these are estimates, not promises. We don't show a likely range, because we can't calculate one
            we'd trust.
          </p>
        </>
      ) : null}

      {(prediction.warnings ?? []).length > 0 ? (
        <ul className="list-disc space-y-1 pl-5 text-xs text-amber-900">
          {(prediction.warnings ?? []).map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}

function HistoryActions({
  data,
  busy,
  file,
  onFile,
  onSnapshot,
  onImport,
  error,
  note,
}: {
  data: VideoForecastResponse;
  busy: "snapshot" | "import" | null;
  file: File | null;
  onFile: (file: File | null) => void;
  onSnapshot: () => void;
  onImport: () => void;
  error: string | null;
  note: string | null;
}) {
  return (
    <section className="card space-y-4 p-5">
      <div>
        <h2 className="text-base font-semibold">Saved view history</h2>
        <p className="mt-1 text-sm text-slate-600">{data.guidance}</p>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <button type="button" className="btn-primary" disabled={busy !== null} onClick={onSnapshot}>
          {busy === "snapshot" ? "Saving…" : "Save today's view count"}
        </button>
        <span className="text-xs text-slate-500">Saves the current public view count from YouTube. You can do this once an hour.</span>
      </div>
      <div className="flex flex-wrap items-end gap-3">
        <label className="min-w-64 flex-1">
          <span className="field-label">Import past view counts (CSV)</span>
          <input
            className="field"
            type="file"
            accept=".csv,text/csv"
            onChange={(event) => onFile(event.target.files?.[0] ?? null)}
          />
        </label>
        <button type="button" className="btn-secondary" disabled={!file || busy !== null} onClick={onImport}>
          {busy === "import" ? "Importing…" : "Import CSV"}
        </button>
      </div>
      <details className="text-sm text-slate-600">
        <summary className="cursor-pointer font-medium text-slate-800">CSV format</summary>
        <p className="mt-2">
          Columns: <code>observed_at</code> (ISO date or time; a date means 00:00 UTC) and <code>views</code> (whole number).
          An optional <code>video_id</code> column must equal {data.video_id}. Each timestamp may appear once.
        </p>
        <pre className="mt-2 overflow-x-auto rounded-lg bg-slate-50 p-3 text-xs">{CSV_EXAMPLE}</pre>
      </details>
      {error ? (
        <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900" role="alert">
          {error}
        </p>
      ) : null}
      {note ? <p className="text-sm text-emerald-800" role="status">{note}</p> : null}
      <details className="text-sm text-slate-600">
        <summary className="cursor-pointer font-medium text-slate-800">{data.observations.length} recorded observation(s)</summary>
        <ul className="mt-2 max-h-56 space-y-1 overflow-y-auto">
          {[...data.observations].reverse().map((item) => (
            <li key={`${item.observed_at}-${item.source}`} className="flex justify-between gap-3 text-xs">
              <span>{new Date(item.observed_at).toLocaleString()}</span>
              <span>
                {formatNumber(item.views)} · {item.source === "analysis" ? "saved analysis" : item.source === "csv" ? "CSV import" : "snapshot"}
              </span>
            </li>
          ))}
        </ul>
      </details>
    </section>
  );
}
