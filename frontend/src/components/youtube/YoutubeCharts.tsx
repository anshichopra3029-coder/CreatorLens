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
        body="These counts weren't available, so there's nothing to compare."
      />
    );
  }
  const logScale = rows.every((row) => row.value > 0) && rows.length > 1;

  return (
    <section className="card p-5">
      <h2 className="text-base font-semibold">Views, likes, and comments</h2>
      <p className="mt-2 text-sm text-slate-600">
        {logScale
          ? "Views are usually much bigger than likes and comments, so the scale is stretched (log scale) to fit them all. Hover a bar to see the exact count."
          : "Exact counts. A missing count is left out instead of being shown as zero."}
      </p>
      <div className="mt-4 h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#E4E2EE" vertical={false} />
            <XAxis dataKey="name" tick={{ fill: "#4D535D", fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis
              scale={logScale ? "log" : "auto"}
              domain={logScale ? ["auto", "auto"] : [0, "auto"]}
              tick={{ fill: "#4D535D", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              width={64}
              allowDecimals={false}
              tickFormatter={(value: number) => formatNumber(value)}
            />
            <Tooltip formatter={(value) => [formatNumber(typeof value === "number" ? value : 0), "Count"]} />
            <Legend />
            <Bar dataKey="value" name="Count" fill="#5848D2" radius={[6, 6, 0, 0]} maxBarSize={72} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

const SLICE_COLORS = ["#5848D2", "#12B5A8", "#EF9620"];

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
        title="Likes vs. comments"
        body="This chart needs at least two kinds of interaction above zero, such as likes and comments. Missing counts aren't shown as zero."
      />
    );
  }
  return (
    <section className="card p-5">
      <h2 className="text-base font-semibold">Likes vs. comments</h2>
      <p className="mt-2 text-sm text-slate-600">
        How the reactions split up. Views aren't included, because watching isn't a reaction.
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
  const rows = series
    .map((point) => ({ ...point, t: Date.parse(point.observed_at) }))
    .filter((point) => Number.isFinite(point.t))
    .sort((first, second) => first.t - second.t);
  const hasInterval = series.some((point) => point.lower !== null || point.upper !== null);
  const formatTime = (value: number) =>
    new Date(value).toLocaleDateString(undefined, { month: "short", day: "numeric" });
  return (
    <section className="card p-5">
      <h2 className="text-base font-semibold">View forecast</h2>
      <p className="mt-2 text-sm text-slate-600">
        {message} The solid line with dots shows real recorded views. The dashed line shows the forecast. (Method: {method ?? "not recorded"}.)
      </p>
      <div className="mt-4 h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#E4E2EE" vertical={false} />
            <XAxis
              dataKey="t"
              type="number"
              scale="time"
              domain={["dataMin", "dataMax"]}
              tickFormatter={formatTime}
              tick={{ fill: "#4D535D", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: "#4D535D", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              width={72}
              domain={["auto", "auto"]}
              tickFormatter={(value: number) => formatNumber(value)}
            />
            <Tooltip
              labelFormatter={(value) => new Date(Number(value)).toLocaleString()}
              formatter={(value, name) => [formatNumber(typeof value === "number" ? value : 0), String(name)]}
            />
            <Legend />
            <Line type="linear" dataKey="views" name="Recorded views" stroke="#5848D2" strokeWidth={2} dot={{ r: 3 }} connectNulls />
            <Line type="linear" dataKey="predicted" name="Predicted views" stroke="#EF9620" strokeDasharray="6 4" strokeWidth={2} dot={{ r: 3 }} connectNulls />
            {hasInterval ? (
              <Line type="linear" dataKey="lower" name="Lower interval" stroke="#B6A9E0" strokeDasharray="2 4" dot={false} connectNulls />
            ) : null}
            {hasInterval ? (
              <Line type="linear" dataKey="upper" name="Upper interval" stroke="#B6A9E0" strokeDasharray="2 4" dot={false} connectNulls />
            ) : null}
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
        body="Not enough data yet. This comparison appears once at least two of your saved videos have public views, likes, and comments."
      />
    );
  }
  return (
    <section className="card p-5">
      <h2 className="text-base font-semibold">Engagement across saved videos</h2>
      <p className="mt-2 text-sm text-slate-600">
        Each bar shows how many people liked or commented compared with how many viewed, for one of your saved videos.
        (Worked out as likes plus comments, divided by views, × 100.)
      </p>
      <div className="mt-4 h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} margin={{ top: 8, right: 8, left: 0, bottom: 48 }}>
            <CartesianGrid stroke="#E4E2EE" vertical={false} />
            <XAxis
              dataKey="name"
              tick={{ fill: "#4D535D", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              interval={0}
              angle={-28}
              textAnchor="end"
              height={72}
            />
            <YAxis
              tick={{ fill: "#4D535D", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              width={48}
              tickFormatter={(value: number) => `${value}%`}
            />
            <Tooltip formatter={(value) => [formatRate(typeof value === "number" ? value : null), "Engagement rate"]} />
            <Bar dataKey="rate" name="Engagement rate" fill="#12B5A8" radius={[6, 6, 0, 0]} maxBarSize={48} />
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
        body="Not enough data yet. A YouTube link only gives today's totals, not past views. A trend line appears after you analyse this video again and a second snapshot is saved."
      />
    );
  }
  return (
    <section className="card p-5">
      <h2 className="text-base font-semibold">Saved view snapshots</h2>
      <p className="mt-2 text-sm text-slate-600">
        Each point is the public view total at the time you saved an analysis. It's not YouTube Studio's own history.
      </p>
      <div className="mt-4 h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#E4E2EE" vertical={false} />
            <XAxis dataKey="label" tick={{ fill: "#4D535D", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis
              tick={{ fill: "#4D535D", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              width={64}
              allowDecimals={false}
              tickFormatter={(value: number) => formatNumber(value)}
            />
            <Tooltip formatter={(value) => [formatNumber(typeof value === "number" ? value : 0), "Views"]} />
            <Line type="monotone" dataKey="views" name="Views" stroke="#5848D2" strokeWidth={2} dot />
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
        body={analytics.reason || "We don't have data on how long people kept watching, so no chart is shown."}
      />
    );
  }
  const rows = points.map((value, index) => ({ point: index + 1, retention: value }));
  return (
    <section className="card p-5">
      <h2 className="text-base font-semibold">Audience retention</h2>
      <p className="mt-2 text-sm text-slate-600">How long people kept watching, from your connected YouTube Analytics.</p>
      <div className="mt-4 h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#E4E2EE" vertical={false} />
            <XAxis dataKey="point" tick={{ fill: "#4D535D", fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#4D535D", fontSize: 12 }} axisLine={false} tickLine={false} width={48} />
            <Tooltip formatter={(value) => [typeof value === "number" ? value : "—", "Retention"]} />
            <Line type="monotone" dataKey="retention" name="Retention" stroke="#EF9620" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
