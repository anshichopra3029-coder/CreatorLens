import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { PerformanceDiagnosisPanel } from "../diagnosis/PerformanceDiagnosis.tsx";
import { RoastCourt } from "./RoastCourt.tsx";
import { KpiCard } from "../dashboard/KpiCard.tsx";
import { QueryPanel } from "../common/QueryPanel.tsx";
import { useApiQuery } from "../../hooks/useApiQuery.ts";
import { formatNumber, formatRate } from "../../services/format.ts";
import { getYoutubeAnalysis, listYoutubeAnalyses, refreshYoutube } from "../../services/youtube.ts";
import type { EvidencePoint, YoutubeAnalysis, YoutubeListItem, YoutubeNarrative } from "../../types/youtube.ts";
import {
  CrossVideoEngagementChart,
  EngagementCountsChart,
  ForecastChart,
  InteractionDonut,
  RetentionChart,
  SnapshotTrendChart,
} from "./YoutubeCharts.tsx";

function formatDuration(seconds: number | null): string {
  if (seconds === null) {
    return "Unavailable";
  }
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainder = seconds % 60;
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`;
  }
  return `${minutes}:${String(remainder).padStart(2, "0")}`;
}

function countLabel(value: number | null, available: boolean): string {
  if (!available || value === null) {
    return "Unavailable";
  }
  return formatNumber(value);
}

function downloadReport(analysis: YoutubeAnalysis) {
  const blob = new Blob([JSON.stringify(analysis, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `youtube-${analysis.metadata.video_id}-${analysis.id.slice(0, 8)}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

function EvidenceList({ title, items }: { title: string; items: EvidencePoint[] }) {
  return (
    <section className="card p-5">
      <h2 className="text-base font-semibold">{title}</h2>
      {items.length === 0 ? (
        <p className="mt-2 text-sm text-slate-600">Nothing to show here from the information we had.</p>
      ) : (
        <ul className="mt-3 space-y-3">
          {items.map((item) => (
            <li key={`${item.source}-${item.claim}`} className="text-sm leading-6 text-slate-700">
              <p className="font-medium text-slate-900">{item.claim}</p>
              <p className="mt-1">{item.evidence}</p>
              <p className="mt-1 text-xs uppercase tracking-wide text-slate-500">Based on: {item.source}</p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function Scorecard({
  title,
  criteria,
  finding,
}: {
  title: string;
  criteria: string;
  finding: string;
}) {
  return (
    <article className="card p-5">
      <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
      <p className="mt-2 text-xs leading-5 text-slate-500">What we looked for: {criteria}</p>
      <p className="mt-3 text-sm leading-6 text-slate-700">{finding}</p>
      <p className="mt-2 text-xs text-slate-500">AI's opinion based on the video's text. It's not a measured score.</p>
    </article>
  );
}

function NarrativeSections({ narrative, model }: { narrative: YoutubeNarrative; model: string | null }) {
  return (
    <>
      <section className="card p-5">
        <h2 className="text-base font-semibold">Overview</h2>
        <p className="mt-3 text-sm leading-6 text-slate-700">{narrative.executive_summary}</p>
        <p className="mt-3 text-sm text-slate-700">
          <span className="font-medium">Who it's for: </span>
          {narrative.intended_audience}
        </p>
        <p className="mt-2 text-sm text-slate-700">
          <span className="font-medium">Main topic: </span>
          {narrative.main_topic}
        </p>
        {model ? <p className="mt-3 text-xs text-slate-500">Written by AI ({model})</p> : null}
      </section>
      <section className="grid gap-4 lg:grid-cols-2">
        <Scorecard
          title="Title"
          criteria="Does the title say what the video is about, in words people would search for?"
          finding={narrative.title_assessment}
        />
        <Scorecard
          title="Description"
          criteria="Does the description match the title and say what's in the video?"
          finding={narrative.description_assessment}
        />
        <Scorecard
          title="Call to action"
          criteria="Does the video ask viewers to do something specific next, like comment or subscribe?"
          finding={narrative.cta_assessment}
        />
        <Scorecard
          title="Opening"
          criteria="How the first seconds grab attention. We can only judge this from the spoken words (transcript)."
          finding={narrative.hook_assessment}
        />
      </section>
      <section className="card p-5">
        <h2 className="text-base font-semibold">Topics and takeaways</h2>
        {narrative.subtopics.length > 0 ? (
          <p className="mt-2 text-sm text-slate-700">Also covers: {narrative.subtopics.join(", ")}</p>
        ) : null}
        <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-700">
          {narrative.key_takeaways.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        {narrative.structure_notes.length > 0 ? (
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-700">
            {narrative.structure_notes.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : null}
        <p className="mt-3 text-sm leading-6 text-slate-600">{narrative.limitations}</p>
      </section>
      <EvidenceList title="About the opening" items={narrative.hook_evidence} />
      <div className="grid gap-4 lg:grid-cols-2">
        <EvidenceList title="What works well" items={narrative.strengths} />
        <EvidenceList title="What could be better" items={narrative.weaknesses} />
      </div>
      <EvidenceList title="Tips for next time" items={narrative.recommendations} />
      <section className="card p-5">
        <h2 className="text-base font-semibold">Ideas to try</h2>
        <p className="mt-2 text-xs text-slate-500">Suggestions from the AI review. They're ideas, not a promise of better results.</p>
        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          <div>
            <h3 className="text-sm font-semibold">Title ideas</h3>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
              {narrative.suggested_titles.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold">Thumbnail ideas</h3>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
              {narrative.thumbnail_concepts.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </div>
        <h3 className="mt-4 text-sm font-semibold">Suggested description</h3>
        <p className="mt-2 text-sm leading-6 text-slate-700">{narrative.suggested_description}</p>
        <h3 className="mt-4 text-sm font-semibold">Ideas for future videos</h3>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
          {narrative.content_ideas.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </>
  );
}

export function YoutubeResults({ analysisId }: { analysisId: string }) {
  const analysis = useApiQuery(() => getYoutubeAnalysis(analysisId), analysisId);
  const saved = useApiQuery(() => listYoutubeAnalyses(), "youtube-list");

  return (
    <QueryPanel
      query={analysis}
      loadingLabel="Loading your saved YouTube analysis…"
      emptyTitle="Analysis not found"
      emptyBody="This saved YouTube analysis isn't available any more."
      isEmpty={() => false}
    >
      {(data) => (
        <ResultsBody key={data.id} data={data} others={saved.status === "success" ? saved.data.analyses : []} />
      )}
    </QueryPanel>
  );
}

function ResultsBody({ data, others }: { data: YoutubeAnalysis; others: YoutubeListItem[] }) {
  const [analysis, setAnalysis] = useState(data);
  const stats = analysis.statistics;
  const navigate = useNavigate();
  const [refreshing, setRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState<string | null>(null);

  async function onRefresh() {
    setRefreshing(true);
    setRefreshError(null);
    try {
      const next = await refreshYoutube(analysis.id);
      navigate(`/youtube/${next.id}`);
    } catch (caught: unknown) {
      setRefreshError(caught instanceof Error ? caught.message : "We couldn't get fresh numbers. Please try again.");
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <div className="space-y-6">
      <section className="card overflow-hidden">
        <div className="grid gap-4 p-5 sm:grid-cols-[180px_minmax(0,1fr)]">
          {analysis.metadata.thumbnail_url ? (
            <img
              src={analysis.metadata.thumbnail_url}
              alt=""
              className="h-28 w-full rounded-lg object-cover sm:h-24"
            />
          ) : (
            <div className="flex h-28 items-center justify-center rounded-lg bg-slate-100 text-xs text-slate-500 sm:h-24">
              No thumbnail
            </div>
          )}
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-indigo-700">Your saved YouTube analysis</p>
            <h2 className="mt-2 text-xl font-semibold">{analysis.metadata.title}</h2>
            <p className="mt-2 text-sm text-slate-600">
              {analysis.metadata.channel_title}
              {analysis.metadata.channel_id ? ` · ${analysis.metadata.channel_id}` : ""}
              {analysis.metadata.category ? ` · ${analysis.metadata.category}` : ""} · {analysis.metadata.privacy_status} · Saved{" "}
              {analysis.created_at}
            </p>
            {analysis.metadata.tags.length > 0 ? (
              <p className="mt-2 text-sm text-slate-500">{analysis.metadata.tags.join(", ")}</p>
            ) : null}
            <a className="mt-2 inline-block text-sm font-semibold text-indigo-700" href={analysis.metadata.url}>
              Open on YouTube
            </a>
          </div>
        </div>
        <div className="flex flex-wrap gap-3 border-t border-slate-200 px-5 py-4">
          <button type="button" className="btn-secondary" onClick={() => downloadReport(analysis)}>
            Download report (JSON file)
          </button>
          <button type="button" className="btn-secondary" onClick={() => void onRefresh()} disabled={refreshing}>
            {refreshing ? "Getting fresh numbers…" : "Get fresh numbers from YouTube"}
          </button>
          <Link to="/youtube" className="text-sm font-semibold text-indigo-700">
            Analyse another video
          </Link>
          {refreshError ? (
            <p className="text-sm text-red-700" role="alert">
              {refreshError}
            </p>
          ) : null}
        </div>
      </section>

      <RoastCourt analysis={analysis} onChange={setAnalysis} />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3" aria-label="Public statistics">
        <KpiCard
          label="Views"
          value={countLabel(stats.views, stats.views_available)}
          detail={stats.views_available ? "Public view count" : "YouTube didn't show a view count"}
        />
        <KpiCard
          label="Likes"
          value={countLabel(stats.likes, stats.likes_available)}
          detail={stats.likes_available ? "Public like count" : "Likes are hidden or missing"}
        />
        <KpiCard
          label="Comments"
          value={countLabel(stats.comments, stats.comments_available)}
          detail={stats.comments_available ? "Public comment count" : "Comments are hidden or missing"}
        />
        <KpiCard
          label="Duration"
          value={formatDuration(analysis.metadata.duration_seconds)}
          detail={analysis.metadata.duration_seconds === null ? "YouTube didn't show the length" : "Video length"}
        />
        <KpiCard
          label="Engagement rate"
          value={formatRate(stats.engagement_rate)}
          detail={
            stats.engagement_rate === null
              ? "Needs public views, likes, and comments"
              : `Likes and comments compared with views (${stats.engagement_formula})`
          }
        />
        <KpiCard
          label="Views per day"
          value={analysis.views_per_day === null ? "Unavailable" : formatNumber(Math.round(analysis.views_per_day))}
          detail={analysis.views_per_day_note}
        />
      </section>
      <p className="text-xs leading-5 text-slate-500">{stats.engagement_note}</p>

      <div className="grid gap-4 xl:grid-cols-2">
        <EngagementCountsChart statistics={stats} />
        <InteractionDonut likes={stats.likes} comments={stats.comments} />
        <CrossVideoEngagementChart currentId={analysis.id} analyses={others} />
        <SnapshotTrendChart videoId={analysis.metadata.video_id} analyses={others} />
        <RetentionChart analytics={analysis.analytics} />
      </div>

      <ForecastChart
        eligible={analysis.prediction.eligible}
        message={analysis.prediction.message}
        limitations={analysis.prediction.limitations}
        series={analysis.prediction.series}
        method={analysis.prediction.model_label ?? analysis.prediction.method}
      />
      {analysis.warnings.length > 0 ? (
        <ul className="list-disc space-y-1 pl-5 text-sm text-slate-600">
          {analysis.warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      ) : null}

      <PerformanceDiagnosisPanel
        diagnosis={analysis.diagnosis}
        evidence={analysis.diagnosis_evidence}
        message={analysis.diagnosis_message}
        retrying={refreshing}
        onRetry={() => void onRefresh()}
      />

      <section className="card p-5">
        <h2 className="text-base font-semibold">Where these numbers come from</h2>
        <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-700">
          <li>
            The numbers come from the video's public YouTube page, saved when you ran this analysis. We didn't download
            the video.
          </li>
          <li>
            Spoken words (transcript): {analysis.transcript.available ? "used for the written review." : analysis.transcript.reason}
          </li>
          <li>Your YouTube Studio numbers: {analysis.analytics.reason}</li>
          <li>
            Comment text:{" "}
            {analysis.comments_status === "available"
              ? "available"
              : analysis.comments_status === "disabled"
                ? "comments are turned off"
                : "not read"}
            .{" "}
            {analysis.comments.length} public comments were saved.
          </li>
        </ul>
      </section>

      {analysis.narrative ? (
        <NarrativeSections narrative={analysis.narrative} model={analysis.model} />
      ) : (
        <section className="card border-amber-200 bg-amber-50 p-5" role="status">
          <h2 className="text-base font-semibold text-amber-950">Written review not available</h2>
          <p className="mt-2 text-sm leading-6 text-amber-950">{analysis.narrative_message}</p>
        </section>
      )}

      {analysis.metadata.description ? (
        <section className="card p-5">
          <h2 className="text-base font-semibold">The video's description</h2>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-700">{analysis.metadata.description}</p>
        </section>
      ) : null}
    </div>
  );
}
