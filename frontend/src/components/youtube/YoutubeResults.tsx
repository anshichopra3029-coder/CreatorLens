import { Link } from "react-router-dom";
import { KpiCard } from "../dashboard/KpiCard.tsx";
import { QueryPanel } from "../common/QueryPanel.tsx";
import { useApiQuery } from "../../hooks/useApiQuery.ts";
import { formatNumber, formatRate } from "../../services/format.ts";
import { getYoutubeAnalysis, listYoutubeAnalyses } from "../../services/youtube.ts";
import type { EvidencePoint, YoutubeAnalysis, YoutubeListItem, YoutubeNarrative } from "../../types/youtube.ts";
import {
  CrossVideoEngagementChart,
  EngagementCountsChart,
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
        <p className="mt-2 text-sm text-slate-600">None were recorded from the available sources.</p>
      ) : (
        <ul className="mt-3 space-y-3">
          {items.map((item) => (
            <li key={`${item.source}-${item.claim}`} className="text-sm leading-6 text-slate-700">
              <p className="font-medium text-slate-900">{item.claim}</p>
              <p className="mt-1">{item.evidence}</p>
              <p className="mt-1 text-xs uppercase tracking-wide text-slate-500">Source: {item.source}</p>
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
      <p className="mt-2 text-xs leading-5 text-slate-500">Criteria: {criteria}</p>
      <p className="mt-3 text-sm leading-6 text-slate-700">{finding}</p>
      <p className="mt-2 text-xs text-slate-500">Gemini observation from the supplied text. This is not a measured score.</p>
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
          <span className="font-medium">Intended audience: </span>
          {narrative.intended_audience}
        </p>
        <p className="mt-2 text-sm text-slate-700">
          <span className="font-medium">Main topic: </span>
          {narrative.main_topic}
        </p>
        {model ? <p className="mt-3 text-xs text-slate-500">Written analysis model: {model}</p> : null}
      </section>
      <section className="grid gap-4 lg:grid-cols-2">
        <Scorecard
          title="Title"
          criteria="Does the title name the subject a viewer would search for?"
          finding={narrative.title_assessment}
        />
        <Scorecard
          title="Description"
          criteria="Does the description match the title and say what the video contains?"
          finding={narrative.description_assessment}
        />
        <Scorecard
          title="Call to action"
          criteria="Is there a specific next step, and does the supplied text support it?"
          finding={narrative.cta_assessment}
        />
        <Scorecard
          title="Opening"
          criteria="Assess the opening only from a transcript. Without one, do not describe the video."
          finding={narrative.hook_assessment}
        />
      </section>
      <section className="card p-5">
        <h2 className="text-base font-semibold">Topics and takeaways</h2>
        {narrative.subtopics.length > 0 ? (
          <p className="mt-2 text-sm text-slate-700">Subtopics: {narrative.subtopics.join(", ")}</p>
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
      <EvidenceList title="Opening evidence" items={narrative.hook_evidence} />
      <div className="grid gap-4 lg:grid-cols-2">
        <EvidenceList title="Strengths" items={narrative.strengths} />
        <EvidenceList title="Weaknesses" items={narrative.weaknesses} />
      </div>
      <EvidenceList title="Recommendations" items={narrative.recommendations} />
      <section className="card p-5">
        <h2 className="text-base font-semibold">Suggested next steps</h2>
        <p className="mt-2 text-xs text-slate-500">Ideas from the written analysis. They are not predicted performance.</p>
        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          <div>
            <h3 className="text-sm font-semibold">Titles</h3>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
              {narrative.suggested_titles.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold">Thumbnail concepts</h3>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
              {narrative.thumbnail_concepts.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </div>
        <h3 className="mt-4 text-sm font-semibold">Description</h3>
        <p className="mt-2 text-sm leading-6 text-slate-700">{narrative.suggested_description}</p>
        <h3 className="mt-4 text-sm font-semibold">Content ideas</h3>
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
      loadingLabel="Loading saved YouTube analysis"
      emptyTitle="Analysis not found"
      emptyBody="This saved YouTube analysis is no longer available."
      isEmpty={() => false}
    >
      {(data) => (
        <ResultsBody data={data} others={saved.status === "success" ? saved.data.analyses : []} />
      )}
    </QueryPanel>
  );
}

function ResultsBody({ data, others }: { data: YoutubeAnalysis; others: YoutubeListItem[] }) {
  const stats = data.statistics;
  return (
    <div className="space-y-6">
      <section className="card overflow-hidden">
        <div className="grid gap-4 p-5 sm:grid-cols-[180px_minmax(0,1fr)]">
          {data.metadata.thumbnail_url ? (
            <img
              src={data.metadata.thumbnail_url}
              alt=""
              className="h-28 w-full rounded-lg object-cover sm:h-24"
            />
          ) : (
            <div className="flex h-28 items-center justify-center rounded-lg bg-slate-100 text-xs text-slate-500 sm:h-24">
              No thumbnail
            </div>
          )}
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-indigo-700">Saved YouTube analysis</p>
            <h2 className="mt-2 text-xl font-semibold">{data.metadata.title}</h2>
            <p className="mt-2 text-sm text-slate-600">
              {data.metadata.channel_title} · {data.metadata.privacy_status} · Saved {data.created_at}
            </p>
            <a className="mt-2 inline-block text-sm font-semibold text-indigo-700" href={data.metadata.url}>
              Open on YouTube
            </a>
          </div>
        </div>
        <div className="flex flex-wrap gap-3 border-t border-slate-200 px-5 py-4">
          <button type="button" className="btn-secondary" onClick={() => downloadReport(data)}>
            Export JSON report
          </button>
          <Link to="/youtube" className="text-sm font-semibold text-indigo-700">
            Analyse another video
          </Link>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5" aria-label="Public statistics">
        <KpiCard
          label="Views"
          value={countLabel(stats.views, stats.views_available)}
          detail={stats.views_available ? "Public view count" : "YouTube did not return a view count"}
        />
        <KpiCard
          label="Likes"
          value={countLabel(stats.likes, stats.likes_available)}
          detail={stats.likes_available ? "Public like count" : "Like count is hidden or missing"}
        />
        <KpiCard
          label="Comments"
          value={countLabel(stats.comments, stats.comments_available)}
          detail={stats.comments_available ? "Public comment count" : "Comment count is hidden or missing"}
        />
        <KpiCard
          label="Duration"
          value={formatDuration(data.metadata.duration_seconds)}
          detail={data.metadata.duration_seconds === null ? "Duration was not returned" : "From the public video metadata"}
        />
        <KpiCard
          label="Engagement rate"
          value={formatRate(stats.engagement_rate)}
          detail={stats.engagement_rate === null ? "Needs public views, likes, and comments" : stats.engagement_formula}
        />
      </section>
      <p className="text-xs leading-5 text-slate-500">{stats.engagement_note}</p>

      <div className="grid gap-4 xl:grid-cols-2">
        <EngagementCountsChart statistics={stats} />
        <CrossVideoEngagementChart currentId={data.id} analyses={others} />
        <SnapshotTrendChart videoId={data.metadata.video_id} analyses={others} />
        <RetentionChart analytics={data.analytics} />
      </div>

      <section className="card p-5">
        <h2 className="text-base font-semibold">What was measured</h2>
        <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-700">
          <li>Public statistics come from the YouTube Data API snapshot saved with this analysis.</li>
          <li>
            Transcript: {data.transcript.available ? "text was supplied to the written analysis." : data.transcript.reason}
          </li>
          <li>Creator analytics: {data.analytics.reason}</li>
          <li>Comments: {data.comments_status}. {data.comments.length} public comment snippets were stored.</li>
        </ul>
      </section>

      {data.narrative ? (
        <NarrativeSections narrative={data.narrative} model={data.model} />
      ) : (
        <section className="card border-amber-200 bg-amber-50 p-5" role="status">
          <h2 className="text-base font-semibold text-amber-950">Written analysis unavailable</h2>
          <p className="mt-2 text-sm leading-6 text-amber-950">{data.narrative_message}</p>
        </section>
      )}

      {data.metadata.description ? (
        <section className="card p-5">
          <h2 className="text-base font-semibold">Description used as metadata</h2>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-700">{data.metadata.description}</p>
        </section>
      ) : null}
    </div>
  );
}
