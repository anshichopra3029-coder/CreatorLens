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
import { ActiveDocumentSwitch } from "../components/documents/ActiveDocumentSwitch.tsx";

export function DashboardPage() {
  return <ActiveDocumentSwitch demo={<DashboardDemo />} />;
}

function DashboardDemo() {
  const summary = useApiQuery(() => getDashboardSummary(), "summary");
  const trends = useApiQuery(() => getTrends(), "trends");
  const comparison = useApiQuery(() => getContentComparison(), "comparison");
  const posts = useApiQuery(() => getPosts(), "posts");
  const insights = useApiQuery(() => getInsights(), "insights");

  return (
    <div className="space-y-6">
      <DemoBanner>
        You're looking at sample numbers from our built-in demo data, not your own file. Upload a file to see your
        own results here.
      </DemoBanner>

      <QueryPanel
        query={summary}
        loadingLabel="Loading the demo summary…"
        emptyTitle="No demo posts"
        emptyBody="The demo data didn't return any posts."
        isEmpty={(data) => data.posts_analyzed === 0}
      >
        {(data) => (
          <div className="space-y-3">
            <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Demo summary">
              <KpiCard
                label="Posts analyzed"
                value={formatNumber(data.posts_analyzed)}
                detail="Demo data · how many posts are in the sample"
              />
              <KpiCard
                label="Avg. engagement rate"
                value={formatRate(data.avg_engagement_rate)}
                detail="Demo data · on average, likes, comments, and shares compared with views"
              />
              <KpiCard
                label="Total interactions"
                value={formatNumber(data.total_interactions)}
                detail="Demo data · all likes, comments, and shares added up"
              />
              <KpiCard
                label="Best category"
                value={data.best_category ?? "—"}
                detail="Demo data · the type of content with the most engagement"
              />
            </section>
            <MetricCaption formula={data.metric_formula} />
          </div>
        )}
      </QueryPanel>

      <section className="grid gap-4 lg:grid-cols-5">
        <div className="card p-5 lg:col-span-3">
          <h2 className="text-base font-semibold">Engagement over time</h2>
          <p className="mb-4 mt-1 text-sm text-slate-500">Average for each week, from the demo posts.</p>
          <QueryPanel
            query={trends}
            loadingLabel="Loading the demo trend…"
            emptyTitle="Nothing to chart yet"
            emptyBody="The demo data has no dated posts to chart."
            isEmpty={(data) => data.points.length === 0}
          >
            {(data) => <EngagementTrendChart points={data.points} />}
          </QueryPanel>
        </div>
        <div className="card p-5 lg:col-span-2">
          <h2 className="text-base font-semibold">Category comparison</h2>
          <p className="mb-4 mt-1 text-sm text-slate-500">Average engagement for each type of content in the demo data.</p>
          <QueryPanel
            query={comparison}
            loadingLabel="Loading the demo comparison…"
            emptyTitle="No categories"
            emptyBody="The demo data has no categories to compare."
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
          loadingLabel="Loading demo posts…"
          emptyTitle="No posts"
          emptyBody="The demo data didn't return any posts."
          isEmpty={(data) => data.posts.length === 0}
        >
          {(data) => <PostsTable posts={data.posts.slice(0, 6)} caption="Six most recent posts from the demo dataset" />}
        </QueryPanel>
      </section>

      <section className="space-y-3">
        <h2 className="text-base font-semibold">Demo insights</h2>
        <QueryPanel
          query={insights}
          loadingLabel="Loading demo insights…"
          emptyTitle="No insights"
          emptyBody="The demo data didn't produce any insights."
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
