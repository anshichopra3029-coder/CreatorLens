import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatRate } from "../../services/format.ts";
import type { GroupMetric } from "../../types/api.ts";

export function CategoryComparisonChart({
  categories,
  caption: captionOverride,
}: {
  categories: GroupMetric[];
  caption?: string;
}) {
  const leader = categories.find((item) => item.avg_engagement_rate !== null) ?? null;
  const caption =
    captionOverride ??
    (leader
      ? `${leader.name} leads this demo comparison at ${formatRate(leader.avg_engagement_rate)} across ${leader.post_count} posts.`
      : "No category rate is available.");

  return (
    <figure>
      <figcaption className="mb-3 text-sm text-slate-600">{caption}</figcaption>
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={categories} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey="name"
              tick={{ fill: "#64748b", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              interval={0}
              angle={-28}
              textAnchor="end"
              height={68}
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
            <Bar dataKey="avg_engagement_rate" name="Engagement rate" fill="#4f46e5" radius={[6, 6, 0, 0]} maxBarSize={48} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </figure>
  );
}
