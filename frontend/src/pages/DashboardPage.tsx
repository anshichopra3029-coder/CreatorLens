import { Link } from "react-router-dom";
import { CategoryComparisonChart } from "../components/charts/CategoryComparisonChart.tsx";
import { EngagementTrendChart } from "../components/charts/EngagementTrendChart.tsx";
import { DemoBanner, MetricCaption } from "../components/common/DemoBanner.tsx";
import { QueryPanel } from "../components/common/QueryPanel.tsx";
import { KpiCard } from "../components/dashboard/KpiCard.tsx";
import { PostsTable } from "../components/dashboard/PostsTable.tsx";
import { useApiQuery } from "../hooks/useApiQuery.ts";
import { getContentComparison, getDashboardSummary, getInsights, getPosts, getTrends } from "../services/api.ts";
import { formatNumber, formatRate } from "../services/format.ts";

export function DashboardPage() {
  const summary = useApiQuery(() => getDashboardSummary(), "summary");
  const trends = useApiQuery(() => getTrends(), "trends");
  const comparison = useApiQuery(() => getContentComparison(), "comparison");
  const posts = useApiQuery(() => getPosts(), "posts");
  const insights = useApiQuery(() => getInsights(), "insights");

  return (
    <div className="space-y-6">
      <DemoBanner>
        Sample metrics below come from the built-in demo dataset. They are not results from a file you upload.
      </DemoBanner>

      <QueryPanel
        query={summary}
        loadingLabel="Loading demo summary"
        emptyTitle="No demo posts"
        emptyBody="The demo dataset did not return any posts."
        isEmpty={(data) => data.posts_analyzed === 0}
      >
        {(data) => (
          <div className="space-y-3">
            <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Demo summary">
              <KpiCard
                label="Posts analyzed"
                value={formatNumber(data.posts_analyzed)}
                detail="Demo data · count of posts in the sample"
              />
              <KpiCard
                label="Avg. engagement rate"
                value={formatRate(data.avg_engagement_rate)}
                detail="Demo data · mean of per-post view-based rates"
              />
              <KpiCard
                label="Total interactions"
                value={formatNumber(data.total_interactions)}
                detail="Demo data · likes + comments + shares"
              />
              <KpiCard
                label="Best category"
                value={data.best_category ?? "—"}
                detail="Demo data · highest average engagement rate"
              />
            </section>
            <MetricCaption formula={data.metric_formula} />
          </div>
        )}
      </QueryPanel>

      <section className="grid gap-4 lg:grid-cols-5">
        <div className="card p-5 lg:col-span-3">
          <h2 className="text-base font-semibold">Engagement over time</h2>
          <p className="mb-4 mt-1 text-sm text-slate-500">Weekly average from the demo posts.</p>
          <QueryPanel
            query={trends}
            loadingLabel="Loading demo trend"
            emptyTitle="No trend points"
            emptyBody="The demo dataset has no dated posts to chart."
            isEmpty={(data) => data.points.length === 0}
          >
            {(data) => <EngagementTrendChart points={data.points} />}
          </QueryPanel>
        </div>
        <div className="card p-5 lg:col-span-2">
          <h2 className="text-base font-semibold">Category comparison</h2>
          <p className="mb-4 mt-1 text-sm text-slate-500">Average rate by category in the demo set.</p>
          <QueryPanel
            query={comparison}
            loadingLabel="Loading demo comparison"
            emptyTitle="No categories"
            emptyBody="The demo dataset has no categories to compare."
            isEmpty={(data) => data.categories.length === 0}
          >
            {(data) => <CategoryComparisonChart categories={data.categories} />}
          </QueryPanel>
        </div>
      </section>

      <section className="card p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="text-base font-semibold">Recent demo posts</h2>
          <Link to="/analytics" className="text-sm font-semibold text-indigo-700">
            Filter in Analytics
          </Link>
        </div>
        <QueryPanel
          query={posts}
          loadingLabel="Loading demo posts"
          emptyTitle="No posts"
          emptyBody="The demo dataset did not return any posts."
          isEmpty={(data) => data.posts.length === 0}
        >
          {(data) => <PostsTable posts={data.posts.slice(0, 6)} caption="Six most recent posts from the demo dataset" />}
        </QueryPanel>
      </section>

      <section className="space-y-3">
        <h2 className="text-base font-semibold">Demo insights</h2>
        <QueryPanel
          query={insights}
          loadingLabel="Loading demo insights"
          emptyTitle="No insights"
          emptyBody="The demo dataset did not produce any insight cards."
          isEmpty={(data) => data.cards.length === 0}
        >
          {(data) => (
            <div className="space-y-3">
              <p className="text-sm text-slate-600">{data.disclaimer}</p>
              <div className="grid gap-4 md:grid-cols-2">
                {data.cards.slice(0, 2).map((card) => (
                  <article key={card.id} className="card p-5">
                    <h3 className="font-semibold">{card.title}</h3>
                    <p className="mt-2 text-sm leading-6 text-slate-600">{card.summary}</p>
                  </article>
                ))}
              </div>
              <Link to="/insights" className="inline-flex text-sm font-semibold text-indigo-700">
                Read all demo insights
              </Link>
            </div>
          )}
        </QueryPanel>
      </section>
    </div>
  );
}
