import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatNumber, formatRate } from "../../services/format.ts";
import type { AnalyticsAvailability, PublicStatistics, YoutubeListItem } from "../../types/youtube.ts";

function UnavailableChart({ title, body }: { title: string; body: string }) {
  return (
    <section className="card p-5">
      <h2 className="text-base font-semibold">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-slate-600">{body}</p>
    </section>
  );
}

export function EngagementCountsChart({ statistics }: { statistics: PublicStatistics }) {
  const rows = [
    statistics.likes_available && statistics.likes !== null ? { name: "Likes", value: statistics.likes } : null,
    statistics.comments_available && statistics.comments !== null
      ? { name: "Comments", value: statistics.comments }
      : null,
  ].filter((row): row is { name: string; value: number } => row !== null);

  if (rows.length === 0) {
    return (
      <UnavailableChart
        title="Public likes and comments"
        body="Likes and comments are not in the public statistics for this video. Views, when present, stay on the summary cards because they use a different scale."
      />
    );
  }

  return (
    <section className="card p-5">
      <h2 className="text-base font-semibold">Public likes and comments</h2>
      <p className="mt-2 text-sm text-slate-600">
        Counts returned by the YouTube Data API. Views stay on the summary cards because they use a different scale.
      </p>
      <div className="mt-4 h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#e2e8f0" vertical={false} />
            <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis
              tick={{ fill: "#64748b", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              width={56}
              allowDecimals={false}
              tickFormatter={(value: number) => formatNumber(value)}
            />
            <Tooltip formatter={(value) => [formatNumber(typeof value === "number" ? value : 0), "Count"]} />
            <Bar dataKey="value" name="Count" fill="#4f46e5" radius={[6, 6, 0, 0]} maxBarSize={72} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

export function CrossVideoEngagementChart({
  currentId,
  analyses,
}: {
  currentId: string;
  analyses: YoutubeListItem[];
}) {
  const rows = analyses
    .filter((item) => item.engagement_rate !== null)
    .map((item) => ({
      name: item.id === currentId ? "This video" : item.title.slice(0, 28),
      rate: item.engagement_rate,
    }));
  if (rows.length < 2) {
    return (
      <UnavailableChart
        title="Engagement across saved videos"
        body="Insufficient data. This comparison appears after at least two saved videos have public views, likes, and comments."
      />
    );
  }
  return (
    <section className="card p-5">
      <h2 className="text-base font-semibold">Engagement across saved videos</h2>
      <p className="mt-2 text-sm text-slate-600">
        Each bar is (likes + comments) / views × 100 from the public statistics saved with that analysis.
      </p>
      <div className="mt-4 h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} margin={{ top: 8, right: 8, left: 0, bottom: 48 }}>
            <CartesianGrid stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey="name"
              tick={{ fill: "#64748b", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              interval={0}
              angle={-28}
              textAnchor="end"
              height={72}
            />
            <YAxis
              tick={{ fill: "#64748b", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              width={48}
              tickFormatter={(value: number) => `${value}%`}
            />
            <Tooltip formatter={(value) => [formatRate(typeof value === "number" ? value : null), "Engagement rate"]} />
            <Bar dataKey="rate" name="Engagement rate" fill="#0f766e" radius={[6, 6, 0, 0]} maxBarSize={48} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

export function SnapshotTrendChart({
  videoId,
  analyses,
}: {
  videoId: string;
  analyses: YoutubeListItem[];
}) {
  const rows = analyses
    .filter((item) => item.video_id === videoId)
    .slice()
    .reverse()
    .map((item) => ({
      label: item.created_at.slice(0, 16).replace("T", " "),
      views: item.views,
      rate: item.engagement_rate,
    }));
  const hasSeries = rows.filter((row) => row.views !== null).length >= 2;
  if (!hasSeries) {
    return (
      <UnavailableChart
        title="Saved view snapshots"
        body="Insufficient data. The Data API returns the current public totals, not a view history. A trend appears only after this video is analysed again and a second snapshot is saved."
      />
    );
  }
  return (
    <section className="card p-5">
      <h2 className="text-base font-semibold">Saved view snapshots</h2>
      <p className="mt-2 text-sm text-slate-600">
        These points are public totals saved at each analysis. They are not a YouTube Analytics time series.
      </p>
      <div className="mt-4 h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#e2e8f0" vertical={false} />
            <XAxis dataKey="label" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis
              tick={{ fill: "#64748b", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              width={64}
              allowDecimals={false}
              tickFormatter={(value: number) => formatNumber(value)}
            />
            <Tooltip formatter={(value) => [formatNumber(typeof value === "number" ? value : 0), "Views"]} />
            <Line type="monotone" dataKey="views" name="Views" stroke="#4f46e5" strokeWidth={2} dot />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

export function RetentionChart({ analytics }: { analytics: AnalyticsAvailability }) {
  const points = analytics.audience_retention;
  if (!analytics.connected || !points || points.length === 0) {
    return (
      <UnavailableChart
        title="Audience retention"
        body={analytics.reason || "Audience retention is unavailable. No curve is shown."}
      />
    );
  }
  const rows = points.map((value, index) => ({ point: index + 1, retention: value }));
  return (
    <section className="card p-5">
      <h2 className="text-base font-semibold">Audience retention</h2>
      <p className="mt-2 text-sm text-slate-600">Points returned by an authorized YouTube Analytics report for this video.</p>
      <div className="mt-4 h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#e2e8f0" vertical={false} />
            <XAxis dataKey="point" tick={{ fill: "#64748b", fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#64748b", fontSize: 12 }} axisLine={false} tickLine={false} width={48} />
            <Tooltip formatter={(value) => [typeof value === "number" ? value : "—", "Retention"]} />
            <Line type="monotone" dataKey="retention" name="Retention" stroke="#b45309" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
