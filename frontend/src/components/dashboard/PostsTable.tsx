import type { PostRecord } from "../../types/api.ts";
import { formatNumber, formatRate } from "../../services/format.ts";
import { EmptyState } from "../common/StateMessage.tsx";

export function PostsTable({ posts, caption }: { posts: PostRecord[]; caption: string }) {
  if (posts.length === 0) {
    return (
      <EmptyState
        title="No posts in this view"
        body="No demo posts match the current filters."
      />
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-[760px] w-full text-left text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr className="border-b border-slate-200 text-slate-500">
            <th scope="col" className="px-3 py-2 font-medium">Post</th>
            <th scope="col" className="px-3 py-2 font-medium">Platform</th>
            <th scope="col" className="px-3 py-2 font-medium">Category</th>
            <th scope="col" className="px-3 py-2 font-medium">Date</th>
            <th scope="col" className="px-3 py-2 text-right font-medium">Views</th>
            <th
              scope="col"
              className="px-3 py-2 text-right font-medium"
              title="(likes + comments + shares) / views * 100"
            >
              Engagement rate
            </th>
          </tr>
        </thead>
        <tbody>
          {posts.map((post) => (
            <tr key={post.post_id} className="border-b border-slate-100 last:border-0">
              <th scope="row" className="px-3 py-3 font-medium text-slate-900">
                <span className="block">{post.title}</span>
                <span className="mt-0.5 block text-xs font-normal text-slate-500">{post.post_id}</span>
              </th>
              <td className="px-3 py-3 text-slate-700">{post.platform}</td>
              <td className="px-3 py-3 text-slate-700">{post.category}</td>
              <td className="px-3 py-3 text-slate-700">{post.post_datetime}</td>
              <td className="px-3 py-3 text-right tabular-nums text-slate-700">{formatNumber(post.views)}</td>
              <td className="px-3 py-3 text-right tabular-nums font-medium text-slate-900">
                {formatRate(post.engagement_rate)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
