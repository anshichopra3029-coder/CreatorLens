import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { QueryPanel } from "../components/common/QueryPanel.tsx";
import { useApiQuery } from "../hooks/useApiQuery.ts";
import { formatNumber, formatRate } from "../services/format.ts";
import { analyzeAnalytics, listAnalytics, previewAnalytics } from "../services/analytics.ts";
import { analyzeYoutube, getYoutubeOauthStatus, listYoutubeAnalyses, previewYoutube } from "../services/youtube.ts";
import type { AnalyticsPreview } from "../types/analytics.ts";
import { parseYoutubeVideoId } from "../services/youtubeUrl.ts";
import type { YoutubePreview } from "../types/youtube.ts";

type Phase = "idle" | "previewing" | "ready" | "analyzing";

function formatDuration(seconds: number | null): string {
  if (seconds === null) {
    return "Unavailable";
  }
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return `${minutes}:${String(remainder).padStart(2, "0")}`;
}

export function YoutubePage() {
  const navigate = useNavigate();
  const saved = useApiQuery(() => listYoutubeAnalyses(), "youtube-analyses");
  const oauth = useApiQuery(() => getYoutubeOauthStatus(), "youtube-oauth");
  const [url, setUrl] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<YoutubePreview | null>(null);
  const uploads = useApiQuery(() => listAnalytics(), "analytics-files");
  const [file, setFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<AnalyticsPreview | null>(null);
  const [filePhase, setFilePhase] = useState<Phase>("idle");
  const [fileError, setFileError] = useState<string | null>(null);

  async function onPreview() {
    setError(null);
    setPreview(null);
    try {
      parseYoutubeVideoId(url);
    } catch (caught: unknown) {
      setPhase("idle");
      setError(caught instanceof Error ? caught.message : "That URL is not a supported YouTube video.");
      return;
    }
    setPhase("previewing");
    try {
      const next = await previewYoutube(url.trim());
      setPreview(next);
      setPhase("ready");
    } catch (caught: unknown) {
      setPhase("idle");
      setError(caught instanceof Error ? caught.message : "We couldn't preview that video. Please try again.");
    }
  }

  async function onAnalyze() {
    setError(null);
    try {
      parseYoutubeVideoId(url);
    } catch (caught: unknown) {
      setPhase(preview ? "ready" : "idle");
      setError(caught instanceof Error ? caught.message : "That URL is not a supported YouTube video.");
      return;
    }
    setPhase("analyzing");
    try {
      const savedAnalysis = await analyzeYoutube(url.trim());
      navigate(`/youtube/${savedAnalysis.id}`);
    } catch (caught: unknown) {
      setPhase(preview ? "ready" : "idle");
      setError(caught instanceof Error ? caught.message : "We couldn't analyze that video. Please try again.");
    }
  }

  async function onFilePreview() {
    if (!file) {
      return;
    }
    setFileError(null);
    setFilePreview(null);
    setFilePhase("previewing");
    try {
      const next = await previewAnalytics(file);
      setFilePreview(next);
      setFilePhase("ready");
    } catch (caught: unknown) {
      setFilePhase("idle");
      setFileError(caught instanceof Error ? caught.message : "The file could not be checked.");
    }
  }

  async function onFileAnalyze() {
    if (!file) {
      return;
    }
    setFileError(null);
    setFilePhase("analyzing");
    try {
      const savedFile = await analyzeAnalytics(file);
      navigate(`/performance/${savedFile.id}`);
    } catch (caught: unknown) {
      setFilePhase(filePreview ? "ready" : "idle");
      setFileError(caught instanceof Error ? caught.message : "We couldn't analyze that file. Please try again.");
    }
  }

  const busy = phase === "previewing" || phase === "analyzing";
  const fileBusy = filePhase === "previewing" || filePhase === "analyzing";

  return (
    <div className="space-y-6">
      <p className="max-w-2xl text-sm leading-6 text-slate-600">
        Paste a link to any public YouTube video (including Shorts). We read the video's public details, like its
        title, views, likes, and comments. We don't download the video.
      </p>

      <form
        className="card space-y-4 p-5"
        onSubmit={(event) => {
          event.preventDefault();
          void onAnalyze();
        }}
      >
        <div>
          <label className="field-label" htmlFor="youtube-url">
            YouTube video link
          </label>
          <input
            id="youtube-url"
            className="field"
            value={url}
            onChange={(event) => {
              setUrl(event.target.value);
              setPreview(null);
              setPhase("idle");
              setError(null);
            }}
            placeholder="https://www.youtube.com/watch?v="
            autoComplete="off"
            disabled={busy}
          />
        </div>
        <div className="flex flex-wrap gap-3">
          <button type="submit" className="btn-primary" disabled={busy || url.trim() === ""}>
            {phase === "analyzing" ? "Saving the analysis…" : "Analyze Video"}
          </button>
          <button type="button" className="btn-secondary" disabled={busy || url.trim() === ""} onClick={() => void onPreview()}>
            {phase === "previewing" ? "Checking the video…" : "Preview video"}
          </button>
        </div>
        {phase === "previewing" ? (
          <p className="text-sm text-slate-600" role="status">
            Getting the video's title, channel, length, and public numbers…
          </p>
        ) : null}
        {phase === "analyzing" ? (
          <p className="text-sm text-slate-600" role="status">
            Saving the video's numbers and asking the AI for a written review. This can take a little while…
          </p>
        ) : null}
        {error ? (
          <p className="text-sm text-red-700" role="alert">
            {error}
          </p>
        ) : null}
      </form>

      {preview ? (
        <section className="card p-5" role="status">
          <div className="grid gap-4 sm:grid-cols-[180px_minmax(0,1fr)]">
            {preview.metadata.thumbnail_url ? (
              <img src={preview.metadata.thumbnail_url} alt="" className="h-28 w-full rounded-lg object-cover" />
            ) : null}
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Preview ready</p>
              <h2 className="mt-2 text-lg font-semibold">{preview.metadata.title}</h2>
              <p className="mt-2 text-sm text-slate-600">
                {preview.metadata.channel_title} · {formatDuration(preview.metadata.duration_seconds)}
                {preview.cached ? " · details saved earlier" : ""}
              </p>
              <p className="mt-2 text-sm text-slate-700">
                Views {preview.statistics.views === null ? "unavailable" : formatNumber(preview.statistics.views)} · Likes{" "}
                {preview.statistics.likes === null ? "unavailable" : formatNumber(preview.statistics.likes)} · Comments{" "}
                {preview.statistics.comments === null ? "unavailable" : formatNumber(preview.statistics.comments)} · Engagement{" "}
                {formatRate(preview.statistics.engagement_rate)}
              </p>
            </div>
          </div>
          <p className="mt-4 text-sm leading-6 text-slate-600">{preview.transcript.reason}</p>
        </section>
      ) : null}

      <section className="card p-5">
        <h2 className="text-base font-semibold">Your YouTube Studio numbers</h2>
        {oauth.status === "success" ? (
          <p className="mt-2 text-sm leading-6 text-slate-600">{oauth.data.reason}</p>
        ) : (
          <p className="mt-2 text-sm text-slate-600">Checking whether your YouTube account is connected…</p>
        )}
      </section>

      <section className="card space-y-4 p-5">
        <h2 className="text-base font-semibold">Upload your analytics (CSV)</h2>
        <p className="text-sm leading-6 text-slate-600">
          Upload a CSV exported from YouTube Studio or a spreadsheet. It needs a video ID or title, plus views, likes, or
          comments. If your file also has dates, shares, impressions, click-through rate, watch time, or subscribers,
          we'll use those too.
        </p>
        <input
          className="block text-sm"
          type="file"
          accept=".csv,text/csv"
          onChange={(event) => {
            setFile(event.target.files?.[0] ?? null);
            setFilePreview(null);
            setFilePhase("idle");
            setFileError(null);
          }}
        />
        <div className="flex flex-wrap gap-3">
          <button type="button" className="btn-secondary" disabled={fileBusy || file === null} onClick={() => void onFilePreview()}>
            {filePhase === "previewing" ? "Checking the file…" : "Preview file"}
          </button>
          <button type="button" className="btn-primary" disabled={fileBusy || filePreview === null} onClick={() => void onFileAnalyze()}>
            {filePhase === "analyzing" ? "Saving the analysis…" : "Analyze file"}
          </button>
        </div>
        {fileError ? (
          <p className="text-sm text-red-700" role="alert">
            {fileError}
          </p>
        ) : null}
        {filePreview ? (
          <div role="status">
            <p className="text-sm text-slate-700">
              {filePreview.row_count} rows · {filePreview.video_count} videos · {filePreview.forecast_message}
            </p>
            <div className="mt-3 overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <caption className="sr-only">Preview rows</caption>
                <thead className="text-slate-500">
                  <tr>
                    <th className="py-2 pr-4 font-medium">Video</th>
                    <th className="py-2 pr-4 font-medium">Date</th>
                    <th className="py-2 pr-4 font-medium">Views</th>
                    <th className="py-2 pr-4 font-medium">Likes</th>
                    <th className="py-2 pr-4 font-medium">Comments</th>
                  </tr>
                </thead>
                <tbody>
                  {filePreview.preview.map((row) => (
                    <tr key={`${row.video_id}-${row.observed_at ?? "none"}`} className="border-t border-slate-200">
                      <td className="py-2 pr-4">{row.title}</td>
                      <td className="py-2 pr-4">{row.observed_at ?? "—"}</td>
                      <td className="py-2 pr-4">{row.views ?? "—"}</td>
                      <td className="py-2 pr-4">{row.likes ?? "—"}</td>
                      <td className="py-2 pr-4">{row.comments ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}
      </section>

      <section className="space-y-3">
        <h2 className="text-base font-semibold">Previous analytics files</h2>
        <QueryPanel
          query={uploads}
          loadingLabel="Loading your analytics files…"
          emptyTitle="No analytics files yet"
          emptyBody="Choose a CSV, click Preview file, then Analyze file to save it here."
          isEmpty={(data) => data.analyses.length === 0}
        >
          {(data) => (
            <ul className="card divide-y divide-slate-200">
              {data.analyses.map((item) => (
                <li key={item.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
                  <div>
                    <p className="text-sm font-semibold">{item.filename}</p>
                    <p className="mt-1 text-xs text-slate-500">
                      {item.video_count} videos · {item.observation_count} rows · {formatRate(item.average_engagement_rate)}
                    </p>
                  </div>
                  <Link to={`/performance/${item.id}`} className="btn-secondary">
                    Open
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </QueryPanel>
      </section>

      <section className="space-y-3">
        <h2 className="text-base font-semibold">Previous video analyses</h2>
        <QueryPanel
          query={saved}
          loadingLabel="Loading your previous video analyses…"
          emptyTitle="No video analyses yet"
          emptyBody="Paste a public video link above and click Analyze Video. Your analysis will appear here."
          isEmpty={(data) => data.analyses.length === 0}
        >
          {(data) => (
            <ul className="card divide-y divide-slate-200">
              {data.analyses.map((item) => (
                <li key={item.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold">{item.title}</p>
                    <p className="mt-1 text-xs text-slate-500">
                      {item.channel_title} · {item.views === null ? "views unavailable" : `${formatNumber(item.views)} views`} ·{" "}
                      {formatRate(item.engagement_rate)}
                    </p>
                  </div>
                  <Link to={`/youtube/${item.id}`} className="btn-secondary">
                    Open
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </QueryPanel>
      </section>
    </div>
  );
}
