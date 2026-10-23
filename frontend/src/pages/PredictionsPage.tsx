import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { EngagementModelPanel } from "../components/predictions/EngagementModelPanel.tsx";
import { ForecastSummary, VideoForecastPanel } from "../components/predictions/VideoForecastPanel.tsx";
import { ForecastChart } from "../components/youtube/YoutubeCharts.tsx";
import { QueryPanel } from "../components/common/QueryPanel.tsx";
import { useApiQuery } from "../hooks/useApiQuery.ts";
import { getAnalytics, listAnalytics } from "../services/analytics.ts";
import { formatNumber } from "../services/format.ts";
import { listTrackedVideos } from "../services/youtube.ts";

export function PredictionsPage() {
  const [listVersion, setListVersion] = useState(0);
  const videos = useApiQuery(() => listTrackedVideos(), `prediction-videos-${listVersion}`);
  const files = useApiQuery(() => listAnalytics(), "prediction-files");
  const [choice, setChoice] = useState("");
  const resultRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const marker = resultRef.current;
    if (!choice || !marker) {
      return;
    }
    const frame = window.requestAnimationFrame(() => {
      const top = marker.getBoundingClientRect().top + window.scrollY - 80;
      window.scrollTo({ top: Math.max(0, top), behavior: "smooth" });
    });
    return () => window.cancelAnimationFrame(frame);
  }, [choice]);
  const analyticsId = choice.startsWith("analytics:") ? choice.slice(10) : "";
  const analyticsDetail = useApiQuery(
    () => (analyticsId ? getAnalytics(analyticsId) : Promise.reject(new Error("Choose a saved analysis."))),
    analyticsId || "none",
  );

  return (
    <div className="space-y-6">
      <section className="card p-6">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">How predictions work</p>
        <h2 className="mt-2 text-2xl font-semibold tracking-tight">Forecasts are based on your saved view counts</h2>
        <p className="mt-4 text-sm leading-7 text-slate-600">
          To forecast a video's views, we need its view count saved at a few different times. A forecast appears once a
          video has three saved counts. From six, we also test our forecast on your real past counts, and only use the
          trend-following method if it beats a simple guess (that views stay the same). One snapshot only shows today's
          total, not whether views are going up. (Technical: the trend method is Holt's linear exponential smoothing,
          checked against a last-value baseline in a rolling back-test.)
        </p>
      </section>

      <EngagementModelPanel />

      <section className="card space-y-4 p-5">
        <h2 className="text-base font-semibold">Your saved videos and files</h2>
        <QueryPanel
          query={videos}
          loadingLabel="Loading your saved videos…"
          emptyTitle="No YouTube videos yet"
          emptyBody="Analyze a public video to save its first view count."
          isEmpty={() => false}
        >
          {(data) => (
            <ul className="divide-y divide-slate-200 text-sm">
              {data.videos.length === 0 ? <li className="py-2 text-slate-600">No YouTube videos yet.</li> : null}
              {data.videos.map((item) => (
                <li key={item.video_id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                  <div>
                    <p className="font-medium">{item.title}</p>
                    <p className="text-xs text-slate-500">
                      {item.observations} saved view count{item.observations === 1 ? "" : "s"}
                      {item.latest_views !== null ? ` · latest ${formatNumber(item.latest_views)}` : ""}
                      {item.analyses > 1 ? ` · ${item.analyses} saved analyses` : ""}
                    </p>
                  </div>
                  <button
                    type="button"
                    className={choice === `youtube:${item.video_id}` ? "btn-primary" : "btn-secondary"}
                    onClick={() => setChoice(`youtube:${item.video_id}`)}
                  >
                    Show forecast
                  </button>
                </li>
              ))}
            </ul>
          )}
        </QueryPanel>
        {files.status === "error" ? (
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm leading-6 text-amber-950" role="status">
            <p className="font-medium">We couldn't load your saved analytics files.</p>
            {files.error.includes("(500)") ? (
              <p>
                Something went wrong on the server while reading them. Your video forecasts above still work. If this
                keeps happening, the analytics file <code>backend/data/analytics.sqlite</code> may be damaged.
              </p>
            ) : (
              <p>{files.error} Your video forecasts above still work.</p>
            )}
            <button type="button" className="btn-secondary mt-2 bg-white" onClick={files.reload}>
              Try again
            </button>
          </div>
        ) : (
        <QueryPanel
          query={files}
          loadingLabel="Loading your analytics files…"
          emptyTitle="No analytics files"
          emptyBody="Upload an analytics CSV with dates on the Analyze YouTube page."
          isEmpty={() => false}
        >
          {(data) => (
            <ul className="divide-y divide-slate-200 text-sm">
              {data.analyses.length === 0 ? <li className="py-2 text-slate-600">No analytics files yet.</li> : null}
              {data.analyses.map((item) => (
                <li key={item.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                  <div>
                    <p className="font-medium">{item.filename}</p>
                    <p className="text-xs text-slate-500">{item.prediction_eligible ? "Forecast ready" : item.prediction_message}</p>
                  </div>
                  <button type="button" className="btn-secondary" onClick={() => setChoice(`analytics:${item.id}`)}>
                    Show forecast
                  </button>
                </li>
              ))}
            </ul>
          )}
        </QueryPanel>
        )}
      </section>

      <div ref={resultRef} className={choice ? "min-h-[80vh] space-y-6" : ""}>
      {choice === "" ? (
        <p className="text-sm text-slate-600">Pick a saved video or file above and click Show forecast.</p>
      ) : choice.startsWith("youtube:") ? (
        <VideoForecastPanel
          key={choice}
          videoId={choice.slice(8)}
          onChanged={() => setListVersion((value) => value + 1)}
        />
      ) : (
        <QueryPanel
          query={analyticsDetail}
          loadingLabel="Loading the forecast…"
          emptyTitle="Forecast not available"
          emptyBody="We couldn't load that saved analysis."
          isEmpty={() => false}
        >
          {(record) => (
            <div className="space-y-3">
              <ForecastSummary title={record.filename} prediction={record.prediction} />
              <ForecastChart
                eligible={record.prediction.eligible}
                message={record.prediction.message}
                limitations={record.prediction.limitations}
                series={record.prediction.series}
                method={record.prediction.model_label ?? record.prediction.method}
              />
              <Link to={`/performance/${record.id}`} className="text-sm font-semibold text-indigo-700">
                Open the full analysis
              </Link>
            </div>
          )}
        </QueryPanel>
      )}
      </div>
    </div>
  );
}
