import { useMemo, useState } from "react";
import { CategoryComparisonChart } from "../components/charts/CategoryComparisonChart.tsx";
import { EngagementTrendChart } from "../components/charts/EngagementTrendChart.tsx";
import { DemoBanner, MetricCaption } from "../components/common/DemoBanner.tsx";
import { QueryPanel } from "../components/common/QueryPanel.tsx";
import { KpiCard } from "../components/dashboard/KpiCard.tsx";
import { PostsTable } from "../components/dashboard/PostsTable.tsx";
import { useApiQuery } from "../hooks/useApiQuery.ts";
import { getContentComparison, getDashboardSummary, getPosts, getTrends } from "../services/api.ts";
import { formatNumber, formatRate, startDateForRange } from "../services/format.ts";
import type { DemoFilters, TimeRange } from "../types/api.ts";

export function AnalyticsPage() {
  const [category, setCategory] = useState("all");
  const [platform, setPlatform] = useState("all");
  const [range, setRange] = useState<TimeRange>("all");
  const catalog = useApiQuery(() => getPosts(), "catalog");

  const filters = useMemo<DemoFilters>(
    () => ({
      category: category === "all" ? undefined : category,
      platform: platform === "all" ? undefined : platform,
      startDate: startDateForRange(range),
    }),
    [category, platform, range],
  );
  const filterKey = `${filters.category ?? ""}|${filters.platform ?? ""}|${filters.startDate ?? ""}`;

  const summary = useApiQuery(() => getDashboardSummary(filters), filterKey);
  const trends = useApiQuery(() => getTrends(filters), `trends-${filterKey}`);
  const comparison = useApiQuery(() => getContentComparison(filters), `comparison-${filterKey}`);
  const posts = useApiQuery(() => getPosts(filters), `posts-${filterKey}`);

  const categories = catalog.status === "success"
    ? [...new Set(catalog.data.posts.map((post) => post.category))].sort()
    : [];
  const platforms = catalog.status === "success"
    ? [...new Set(catalog.data.posts.map((post) => post.platform))].sort()
    : [];

  function resetFilters() {
    setCategory("all");
    setPlatform("all");
    setRange("all");
  }

  return (
    <div className="space-y-6">
      <DemoBanner>
        Filters reload demo figures from the API. They do not analyze an uploaded file in this phase.
      </DemoBanner>

      <QueryPanel
        query={catalog}
        loadingLabel="Loading demo filter options"
        emptyTitle="No demo posts to filter"
        emptyBody="The demo dataset did not return any posts, so there are no categories or platforms to choose."
        isEmpty={(data) => data.posts.length === 0}
      >
        {() => (
          <form className="card grid gap-4 p-5 md:grid-cols-3" aria-label="Demo filters">
            <div>
              <label className="field-label" htmlFor="category-filter">Category</label>
              <select
                id="category-filter"
                className="field"
                value={category}
                onChange={(event) => setCategory(event.target.value)}
              >
                <option value="all">All categories</option>
                {categories.map((name) => (
                  <option key={name} value={name}>{name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="field-label" htmlFor="platform-filter">Platform</label>
              <select
                id="platform-filter"
                className="field"
                value={platform}
                onChange={(event) => setPlatform(event.target.value)}
              >
                <option value="all">All platforms</option>
                {platforms.map((name) => (
                  <option key={name} value={name}>{name}</option>
                ))}
              </select>
            </div>
            <fieldset>
              <legend className="field-label">Time range</legend>
              <div className="flex flex-wrap gap-2">
                {(
                  [
                    ["all", "All time"],
                    ["90", "Last 90 days"],
                    ["30", "Last 30 days"],
                  ] as const
                ).map(([value, label]) => (
                  <label key={value} className="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm">
                    <input
                      type="radio"
                      name="time-range"
                      value={value}
                      checked={range === value}
                      onChange={() => setRange(value)}
                    />
                    {label}
                  </label>
                ))}
              </div>
              <p className="mt-2 text-xs text-slate-500">Counted back from today using each post date.</p>
            </fieldset>
            <div className="md:col-span-3">
              <button type="button" className="btn-secondary" onClick={resetFilters}>
                Reset filters
              </button>
            </div>
          </form>
        )}
      </QueryPanel>

      <div aria-busy={summary.status === "loading"}>
        <QueryPanel
          query={summary}
          loadingLabel="Loading filtered demo summary"
          emptyTitle="No demo posts match these filters"
          emptyBody="Try a wider time range, or reset the category and platform."
          isEmpty={(data) => data.posts_analyzed === 0}
        >
          {(data) => (
            <div className="space-y-3">
              <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Filtered demo summary">
                <KpiCard label="Posts" value={formatNumber(data.posts_analyzed)} detail="Demo data · posts in this filter" />
                <KpiCard label="Avg. engagement rate" value={formatRate(data.avg_engagement_rate)} detail="Demo data · mean of per-post rates" />
                <KpiCard label="Total interactions" value={formatNumber(data.total_interactions)} detail="Demo data · likes + comments + shares" />
                <KpiCard label="Best category" value={data.best_category ?? "—"} detail="Demo data · highest average rate in this filter" />
              </section>
              <MetricCaption formula={data.metric_formula} />
            </div>
          )}
        </QueryPanel>
      </div>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="card p-5">
          <h2 className="mb-4 text-base font-semibold">Trend</h2>
          <QueryPanel
            query={trends}
            loadingLabel="Loading filtered trend"
            emptyTitle="No trend for this filter"
            emptyBody="None of the demo posts in this filter have a date to chart."
            isEmpty={(data) => data.points.length === 0}
          >
            {(data) => <EngagementTrendChart points={data.points} />}
          </QueryPanel>
        </div>
        <div className="card p-5">
          <h2 className="mb-4 text-base font-semibold">Content type</h2>
          <QueryPanel
            query={comparison}
            loadingLabel="Loading filtered comparison"
            emptyTitle="No categories for this filter"
            emptyBody="None of the demo posts in this filter have a category to compare."
            isEmpty={(data) => data.categories.length === 0}
          >
            {(data) => <CategoryComparisonChart categories={data.categories} />}
          </QueryPanel>
        </div>
      </section>

      <section className="card p-5">
        <h2 className="mb-4 text-base font-semibold">Posts in this filter</h2>
        <QueryPanel
          query={posts}
          loadingLabel="Loading filtered posts"
          emptyTitle="No posts in this filter"
          emptyBody="Reset the filters to see the full demo dataset."
          isEmpty={(data) => data.posts.length === 0}
        >
          {(data) => <PostsTable posts={data.posts} caption="Demo posts matching the selected filters" />}
        </QueryPanel>
      </section>
    </div>
  );
}
