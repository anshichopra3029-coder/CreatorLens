import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { QueryPanel } from "../components/common/QueryPanel.tsx";
import { PerformanceDiagnosisPanel } from "../components/diagnosis/PerformanceDiagnosis.tsx";
import { ForecastChart, InteractionDonut } from "../components/youtube/YoutubeCharts.tsx";
import { KpiCard } from "../components/dashboard/KpiCard.tsx";
import { useApiQuery } from "../hooks/useApiQuery.ts";
import { getAnalytics } from "../services/analytics.ts";
import { formatNumber, formatRate } from "../services/format.ts";
import type { AnalyticsAnalysis } from "../types/analytics.ts";

export function PerformancePage() {
  const { analysisId } = useParams();
  const query = useApiQuery(() => getAnalytics(analysisId ?? ""), analysisId ?? "missing");
  if (!analysisId) {
    return <p className="text-sm text-slate-600">Choose a saved analytics file.</p>;
  }
  return (
    <QueryPanel
      query={query}
      loadingLabel="Loading saved analytics"
      emptyTitle="Analysis not found"
      emptyBody="This saved analytics file is no longer available."
      isEmpty={() => false}
    >
      {(data) => <PerformanceBody data={data} />}
    </QueryPanel>
  );
}

function PerformanceBody({ data }: { data: AnalyticsAnalysis }) {
  const [videoId, setVideoId] = useState(data.summary.videos[0]?.video_id ?? "");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const selected = data.summary.videos.find((video) => video.video_id === videoId) ?? data.summary.videos[0];
  const series = useMemo(() => {
    return data.observations
      .filter((row) => row.video_id === (selected?.video_id ?? "") && row.observed_at)
      .filter((row) => (start === "" || (row.observed_at ?? "") >= start) && (end === "" || (row.observed_at ?? "") <= end))
      .slice()
      .sort((left, right) => (left.observed_at ?? "").localeCompare(right.observed_at ?? ""));
  }, [data.observations, selected, start, end]);
  const comparison = data.summary.videos
    .filter((video) => video.views !== null)
    .map((video) => ({ name: video.title.slice(0, 24), views: video.views, rate: video.engagement_rate }));

  return (
    <div className="space-y-6">
      <section className="card p-5">
        <p className="text-xs font-semibold uppercase tracking-wide text-indigo-700">Uploaded analytics</p>
        <h2 className="mt-2 text-xl font-semibold">{data.filename}</h2>
        <p className="mt-2 text-sm text-slate-600">
          {data.summary.video_count} videos · {data.summary.observation_count} rows · Saved {data.created_at}
        </p>
        <p className="mt-3 text-sm leading-6 text-slate-700">{data.summary.formula_note}</p>
        <Link to="/youtube" className="mt-4 inline-block text-sm font-semibold text-indigo-700">
          Analyze another source
        </Link>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="Latest views"
          value={data.summary.total_latest_views === null ? "Unavailable" : formatNumber(data.summary.total_latest_views)}
          detail="Sum of the latest view count for each video"
        />
        <KpiCard
          label="Average engagement"
          value={formatRate(data.summary.average_engagement_rate)}
          detail={data.summary.engagement_formula}
        />
        <KpiCard label="Videos" value={formatNumber(data.summary.video_count)} detail="Distinct video IDs or titles" />
        <KpiCard
          label="Dated rows"
          value={formatNumber(data.observations.filter((row) => row.observed_at).length)}
          detail="Rows with a usable date"
        />
      </section>

      {data.warnings.map((warning) => (
        <p key={warning} className="card p-4 text-sm text-slate-700">
          {warning}
        </p>
      ))}

      <div className="grid gap-4 xl:grid-cols-2">
        {comparison.length === 0 ? (
          <section className="card p-5">
            <h2 className="text-base font-semibold">Latest views by video</h2>
            <p className="mt-2 text-sm text-slate-600">No video in this file has a view count.</p>
          </section>
        ) : (
          <section className="card p-5">
            <h2 className="text-base font-semibold">Latest views by video</h2>
            <p className="mt-2 text-sm text-slate-600">Each bar is the newest view count in the file, not a time series.</p>
            <div className="mt-4 h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={comparison} margin={{ top: 8, right: 8, left: 0, bottom: 48 }}>
                  <CartesianGrid stroke="#e2e8f0" vertical={false} />
                  <XAxis dataKey="name" interval={0} angle={-28} textAnchor="end" height={72} tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: "#64748b", fontSize: 12 }} axisLine={false} tickLine={false} width={64} tickFormatter={(value: number) => formatNumber(value)} />
                  <Tooltip formatter={(value) => formatNumber(typeof value === "number" ? value : 0)} />
                  <Bar dataKey="views" name="Latest views" fill="#4f46e5" radius={[6, 6, 0, 0]} maxBarSize={48} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>
        )}
        <InteractionDonut likes={selected?.likes ?? null} comments={selected?.comments ?? null} shares={selected?.shares} />
      </div>

      <section className="card space-y-4 p-5">
        <h2 className="text-base font-semibold">Dated observations</h2>
        <div className="grid gap-3 sm:grid-cols-3">
          <label className="text-sm text-slate-700">
            Video
            <select className="field mt-1" value={selected?.video_id ?? ""} onChange={(event) => setVideoId(event.target.value)}>
              {data.summary.videos.map((video) => (
                <option key={video.video_id} value={video.video_id}>
                  {video.title}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm text-slate-700">
            From
            <input className="field mt-1" type="date" value={start} onChange={(event) => setStart(event.target.value)} />
          </label>
          <label className="text-sm text-slate-700">
            To
            <input className="field mt-1" type="date" value={end} onChange={(event) => setEnd(event.target.value)} />
          </label>
        </div>
        {series.filter((row) => row.views !== null).length < 2 ? (
          <p className="text-sm leading-6 text-slate-600">
            This filter has fewer than two dated view counts, so no trend line is drawn. A single row is a snapshot, not growth over time.
          </p>
        ) : (
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={series} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="observed_at" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: "#64748b", fontSize: 12 }} axisLine={false} tickLine={false} width={64} tickFormatter={(value: number) => formatNumber(value)} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="views" name="Views" stroke="#4f46e5" strokeWidth={2} dot connectNulls={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>

      <ForecastChart
        eligible={data.prediction.eligible}
        message={data.prediction.message}
        limitations={data.prediction.limitations}
        series={data.prediction.series}
        method={data.prediction.method}
      />

      <PerformanceDiagnosisPanel
        diagnosis={data.diagnosis}
        evidence={data.diagnosis_evidence}
        message={data.diagnosis_message}
      />

      {data.narrative ? (
        <section className="card space-y-4 p-5">
          <h2 className="text-base font-semibold">Suggestions</h2>
          <p className="text-sm leading-6 text-slate-700">{data.narrative.executive_summary}</p>
          <h3 className="text-sm font-semibold">Strengths</h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
            {data.narrative.strengths.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <h3 className="text-sm font-semibold">Improvements</h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
            {data.narrative.weaknesses.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <h3 className="text-sm font-semibold">Next actions</h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
            {data.narrative.next_actions.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <h3 className="text-sm font-semibold">Future video ideas</h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
            {data.narrative.content_ideas.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <p className="text-sm text-slate-600">{data.narrative.additional_data}</p>
          <p className="text-xs text-slate-500">{data.narrative.limitations}</p>
          {data.model ? <p className="text-xs text-slate-500">Suggestion model: {data.model}</p> : null}
        </section>
      ) : (
        <section className="card border-amber-200 bg-amber-50 p-5" role="status">
          <h2 className="text-base font-semibold text-amber-950">Suggestions unavailable</h2>
          <p className="mt-2 text-sm leading-6 text-amber-950">{data.narrative_message}</p>
        </section>
      )}
    </div>
  );
}
