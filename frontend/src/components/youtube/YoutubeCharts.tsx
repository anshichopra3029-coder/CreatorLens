import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatNumber, formatRate } from "../../services/format.ts";
import type { ForecastPoint } from "../../types/prediction.ts";
import type { AnalyticsAvailability, PublicStatistics, YoutubeListItem } from "../../types/youtube.ts";

function UnavailableChart({ title, body }: { title: string; body: string }) {
  return (
    <section className="card p-5">
      <h2 className="text-base font-semibold">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-slate-600">{body}</p>
    </section>
  );
}

export function EngagementCountsChart({
  statistics,
  shares,
}: {
  statistics: PublicStatistics;
  shares?: number | null;
}) {
  const rows = [
    statistics.views_available && statistics.views !== null && statistics.views > 0
      ? { name: "Views", value: statistics.views }
      : null,
    statistics.likes_available && statistics.likes !== null && statistics.likes > 0
      ? { name: "Likes", value: statistics.likes }
      : null,
    statistics.comments_available && statistics.comments !== null && statistics.comments > 0
      ? { name: "Comments", value: statistics.comments }
      : null,
    shares !== undefined && shares !== null ? { name: "Shares", value: shares } : null,
  ].filter((row): row is { name: string; value: number } => row !== null);

  if (rows.length === 0) {
    return (
      <UnavailableChart
        title="Views, likes, and comments"
        body="Those counts were not available, so this comparison is empty."
      />
    );
  }
  const logScale = rows.every((row) => row.value > 0) && rows.length > 1;

  return (
    <section className="card p-5">
      <h2 className="text-base font-semibold">Views, likes, and comments</h2>
      <p className="mt-2 text-sm text-slate-600">
        {logScale
          ? "The axis uses a log scale because views are usually much larger than likes and comments. Tooltip values are the exact counts."
          : "Exact public or uploaded counts. A missing count is omitted rather than drawn as zero."}
      </p>
      <div className="mt-4 h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#e2e8f0" vertical={false} />
            <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis
              scale={logScale ? "log" : "auto"}
              domain={logScale ? ["auto", "auto"] : [0, "auto"]}
              tick={{ fill: "#64748b", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              width={64}
              allowDecimals={false}
              tickFormatter={(value: number) => formatNumber(value)}
            />
            <Tooltip formatter={(value) => [formatNumber(typeof value === "number" ? value : 0), "Count"]} />
            <Legend />
            <Bar dataKey="value" name="Count" fill="#4f46e5" radius={[6, 6, 0, 0]} maxBarSize={72} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

const SLICE_COLORS = ["#4f46e5", "#0f766e", "#b45309"];

export function InteractionDonut({
  likes,
  comments,
  shares,
}: {
  likes: number | null;
  comments: number | null;
  shares?: number | null;
}) {
  const slices = [
    likes !== null ? { name: "Likes", value: likes } : null,
    comments !== null ? { name: "Comments", value: comments } : null,
    shares !== undefined && shares !== null ? { name: "Shares", value: shares } : null,
  ].filter((slice): slice is { name: string; value: number } => slice !== null && slice.value > 0);
  if (slices.length < 2) {
    return (
      <UnavailableChart
        title="Interaction mix"
        body="A mix chart needs at least two positive interaction counts, such as likes and comments. Missing counts are not drawn as zero."
      />
    );
  }
  return (
    <section className="card p-5">
      <h2 className="text-base font-semibold">Interaction mix</h2>
      <p className="mt-2 text-sm text-slate-600">
        Share of the available interaction counts. Views are excluded because they are not an interaction.
      </p>
      <div className="mt-4 h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={slices} dataKey="value" nameKey="name" innerRadius={58} outerRadius={84} paddingAngle={2}>
              {slices.map((slice, index) => (
                <Cell key={slice.name} fill={SLICE_COLORS[index % SLICE_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(value) => [formatNumber(typeof value === "number" ? value : 0), "Count"]} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

export function ForecastChart({
  eligible,
  message,
  limitations,
  series,
  method,
}: {
  eligible: boolean;
  message: string;
  limitations: string;
  series: ForecastPoint[];
  method: string | null;
}) {
  if (!eligible || series.length === 0) {
    return <UnavailableChart title="View forecast" body={message} />;
  }
  return (
    <section className="card p-5">
      <h2 className="text-base font-semibold">View forecast</h2>
      <p className="mt-2 text-sm text-slate-600">
        {message} Method: {method ?? "not recorded"}. The solid line is observed. The dashed line is predicted.
      </p>
      <div className="mt-4 h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={series} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#e2e8f0" vertical={false} />
            <XAxis dataKey="observed_at" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis
              tick={{ fill: "#64748b", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              width={64}
              tickFormatter={(value: number) => formatNumber(value)}
            />
            <Tooltip formatter={(value) => [formatNumber(typeof value === "number" ? value : 0), "Views"]} />
            <Legend />
            <Line type="monotone" dataKey="views" name="Observed views" stroke="#4f46e5" strokeWidth={2} dot={false} connectNulls={false} />
            <Line type="monotone" dataKey="predicted" name="Predicted views" stroke="#b45309" strokeDasharray="6 4" strokeWidth={2} dot={false} connectNulls />
            <Line type="monotone" dataKey="lower" name="Lower interval" stroke="#94a3b8" strokeDasharray="2 4" dot={false} connectNulls />
            <Line type="monotone" dataKey="upper" name="Upper interval" stroke="#94a3b8" strokeDasharray="2 4" dot={false} connectNulls />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-3 text-xs leading-5 text-slate-500">{limitations}</p>
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
        body="Insufficient data. A public URL returns the current totals, not a view history. A trend appears only after this video is analysed again and a second snapshot is saved."
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
