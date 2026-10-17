import { useState } from "react";
import { Link } from "react-router-dom";
import { ForecastChart } from "../components/youtube/YoutubeCharts.tsx";
import { QueryPanel } from "../components/common/QueryPanel.tsx";
import { useApiQuery } from "../hooks/useApiQuery.ts";
import { getAnalytics, listAnalytics } from "../services/analytics.ts";
import { getYoutubeAnalysis, listYoutubeAnalyses } from "../services/youtube.ts";
import type { PredictionResult } from "../types/prediction.ts";

export function PredictionsPage() {
  const videos = useApiQuery(() => listYoutubeAnalyses(), "prediction-videos");
  const files = useApiQuery(() => listAnalytics(), "prediction-files");
  const [choice, setChoice] = useState("");
  const detail = useApiQuery(() => loadChoice(choice), choice || "none");

  return (
    <div className="space-y-6">
      <section className="card p-6">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Forecast status</p>
        <h2 className="mt-2 text-2xl font-semibold tracking-tight">Forecasts use dated view counts only</h2>
        <p className="mt-4 text-sm leading-7 text-slate-600">
          A model is trained when one video has at least eight view counts on different dates. The latest observations
          are held out, a last-value baseline is compared with a straight line, and the better method is refit for the
          chart. A single public YouTube snapshot does not train a model.
        </p>
      </section>

      <section className="card space-y-4 p-5">
        <h2 className="text-base font-semibold">Saved sources</h2>
        <QueryPanel
          query={videos}
          loadingLabel="Loading video analyses"
          emptyTitle="No YouTube analyses"
          emptyBody="Analyze a public video to store a snapshot. One snapshot will be marked as not forecastable."
          isEmpty={() => false}
        >
          {(data) => (
            <ul className="divide-y divide-slate-200 text-sm">
              {data.analyses.length === 0 ? <li className="py-2 text-slate-600">No YouTube analyses yet.</li> : null}
              {data.analyses.map((item) => (
                <li key={item.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                  <div>
                    <p className="font-medium">{item.title}</p>
                    <p className="text-xs text-slate-500">{item.prediction_eligible ? "Forecast stored" : item.prediction_message}</p>
                  </div>
                  <button type="button" className="btn-secondary" onClick={() => setChoice(`youtube:${item.id}`)}>
                    Show forecast
                  </button>
                </li>
              ))}
            </ul>
          )}
        </QueryPanel>
        <QueryPanel
          query={files}
          loadingLabel="Loading analytics files"
          emptyTitle="No analytics files"
          emptyBody="Upload a dated analytics CSV from Analyze YouTube."
          isEmpty={() => false}
        >
          {(data) => (
            <ul className="divide-y divide-slate-200 text-sm">
              {data.analyses.length === 0 ? <li className="py-2 text-slate-600">No analytics files yet.</li> : null}
              {data.analyses.map((item) => (
                <li key={item.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                  <div>
                    <p className="font-medium">{item.filename}</p>
                    <p className="text-xs text-slate-500">{item.prediction_eligible ? "Forecast stored" : item.prediction_message}</p>
                  </div>
                  <button type="button" className="btn-secondary" onClick={() => setChoice(`analytics:${item.id}`)}>
                    Show forecast
                  </button>
                </li>
              ))}
            </ul>
          )}
        </QueryPanel>
      </section>

      {choice === "" ? (
        <p className="text-sm text-slate-600">Choose a saved analysis to see whether a forecast was trained.</p>
      ) : (
        <QueryPanel
          query={detail}
          loadingLabel="Loading forecast"
          emptyTitle="Forecast unavailable"
          emptyBody="That saved analysis could not be loaded."
          isEmpty={() => false}
        >
          {(prediction) => (
            <div className="space-y-3">
              <ForecastChart
                eligible={prediction.eligible}
                message={prediction.message}
                limitations={prediction.limitations}
                series={prediction.series}
                method={prediction.method}
              />
              {prediction.trained ? (
                <p className="text-xs text-slate-500">
                  Model {prediction.model_version}
                  {prediction.generated_at ? ` · generated ${prediction.generated_at}` : ""}
                  {prediction.baseline_mae !== null ? ` · baseline MAE ${prediction.baseline_mae}` : ""}
                  {prediction.model_mae !== null ? ` · line MAE ${prediction.model_mae}` : ""}
                  {prediction.holdout_start ? ` · holdout starts ${prediction.holdout_start}` : ""}
                </p>
              ) : null}
              <Link to={choice.startsWith("youtube:") ? `/youtube/${choice.slice(8)}` : `/performance/${choice.slice(10)}`} className="text-sm font-semibold text-indigo-700">
                Open the full analysis
              </Link>
            </div>
          )}
        </QueryPanel>
      )}
    </div>
  );
}

function loadChoice(choice: string): Promise<PredictionResult> {
  if (choice.startsWith("youtube:")) {
    return getYoutubeAnalysis(choice.slice(8)).then((record) => record.prediction);
  }
  if (choice.startsWith("analytics:")) {
    return getAnalytics(choice.slice(10)).then((record) => record.prediction);
  }
  return Promise.reject(new Error("Choose a saved analysis."));
}
