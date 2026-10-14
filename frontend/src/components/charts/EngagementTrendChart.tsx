import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatRate } from "../../services/format.ts";
import type { TrendPoint } from "../../types/api.ts";

function peakPoint(points: TrendPoint[]): TrendPoint | null {
  return points.reduce<TrendPoint | null>((best, point) => {
    if (point.avg_engagement_rate === null) {
      return best;
    }
    if (best === null || best.avg_engagement_rate === null) {
      return point;
    }
    return point.avg_engagement_rate > best.avg_engagement_rate ? point : best;
  }, null);
}

export function EngagementTrendChart({ points }: { points: TrendPoint[] }) {
  const peak = peakPoint(points);
  const caption = peak
    ? `Highest weekly average in this demo series is ${formatRate(peak.avg_engagement_rate)} in the week of ${peak.label}.`
    : "No engagement rate is available for this series.";

  return (
    <figure>
      <figcaption className="mb-3 text-sm text-slate-600">{caption}</figcaption>
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={points} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fill: "#64748b", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: "#64748b", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              width={48}
              tickFormatter={(value: number) => `${value}%`}
            />
            <Tooltip
              formatter={(value) => [formatRate(typeof value === "number" ? value : null), "Engagement rate"]}
            />
            <Line
              type="monotone"
              dataKey="avg_engagement_rate"
              name="Engagement rate"
              stroke="#4f46e5"
              strokeWidth={2}
              dot={{ r: 3, fill: "#4f46e5" }}
              connectNulls={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </figure>
  );
}
