import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { QueryPanel } from "../components/common/QueryPanel.tsx";
import { useApiQuery } from "../hooks/useApiQuery.ts";
import { formatNumber, formatRate } from "../services/format.ts";
import { analyzeYoutube, getYoutubeOauthStatus, listYoutubeAnalyses, previewYoutube } from "../services/youtube.ts";
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

  async function onPreview(event: FormEvent) {
    event.preventDefault();
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
      setError(caught instanceof Error ? caught.message : "The video preview failed.");
    }
  }

  async function onAnalyze() {
    setError(null);
    setPhase("analyzing");
    try {
      const savedAnalysis = await analyzeYoutube(url.trim());
      navigate(`/youtube/${savedAnalysis.id}`);
    } catch (caught: unknown) {
      setPhase(preview ? "ready" : "idle");
      setError(caught instanceof Error ? caught.message : "The analysis failed.");
    }
  }

  const busy = phase === "previewing" || phase === "analyzing";

  return (
    <div className="space-y-6">
      <p className="max-w-2xl text-sm leading-6 text-slate-600">
        Paste a public YouTube watch, youtu.be, or Shorts URL. The server reads public metadata and statistics.
        It does not download the video.
      </p>

      <form className="card space-y-4 p-5" onSubmit={(event) => void onPreview(event)}>
        <div>
          <label className="field-label" htmlFor="youtube-url">
            YouTube URL
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
            {phase === "previewing" ? "Checking the video…" : "Preview video"}
          </button>
          <button type="button" className="btn-secondary" disabled={busy || preview === null} onClick={() => void onAnalyze()}>
            {phase === "analyzing" ? "Saving the analysis…" : "Start analysis"}
          </button>
        </div>
        {phase === "previewing" ? (
          <p className="text-sm text-slate-600" role="status">
            Requesting the public title, channel, duration, and statistics.
          </p>
        ) : null}
        {phase === "analyzing" ? (
          <p className="text-sm text-slate-600" role="status">
            Saving public statistics and requesting a written analysis when Gemini is configured.
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
                {preview.cached ? " · cached metadata" : ""}
              </p>
              <p className="mt-2 text-sm text-slate-700">
                Views {preview.statistics.views === null ? "unavailable" : formatNumber(preview.statistics.views)} · Likes{" "}
                {preview.statistics.likes === null ? "unavailable" : formatNumber(preview.statistics.likes)} · Comments{" "}
                {preview.statistics.comments === null ? "unavailable" : formatNumber(preview.statistics.comments)} · Rate{" "}
                {formatRate(preview.statistics.engagement_rate)}
              </p>
            </div>
          </div>
          <p className="mt-4 text-sm leading-6 text-slate-600">{preview.transcript.reason}</p>
        </section>
      ) : null}

      <section className="card p-5">
        <h2 className="text-base font-semibold">Creator analytics</h2>
        {oauth.status === "success" ? (
          <p className="mt-2 text-sm leading-6 text-slate-600">{oauth.data.reason}</p>
        ) : (
          <p className="mt-2 text-sm text-slate-600">Checking whether a creator YouTube account is connected.</p>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-base font-semibold">Previous video analyses</h2>
        <QueryPanel
          query={saved}
          loadingLabel="Loading previous video analyses"
          emptyTitle="No video analyses yet"
          emptyBody="A saved analysis appears here after you start one from a public video URL."
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
