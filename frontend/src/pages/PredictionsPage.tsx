import { useState, type FormEvent } from "react";

const PLATFORMS = ["Instagram", "YouTube", "TikTok", "Other"];
const CATEGORIES = ["Tutorial", "Short-form", "Behind the Scenes", "Product Update", "Community", "Other"];

export function PredictionsPage() {
  const [platform, setPlatform] = useState(PLATFORMS[0]);
  const [category, setCategory] = useState(CATEGORIES[0]);
  const [note, setNote] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(
      `No trained model is available, so CreatorLens did not calculate a prediction for ${platform} / ${category}. ${
        note.trim() ? "Your note was not sent anywhere." : "Nothing was estimated."
      }`,
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
      <section className="card p-6">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Model status</p>
        <h2 className="mt-2 text-2xl font-semibold tracking-tight">Engagement prediction is not available yet</h2>
        <p className="mt-4 text-sm leading-7 text-slate-600">
          A future version may estimate the view-based engagement rate, (likes + comments + shares) / views × 100,
          using only information that would be known before a post goes live. That requires a defined target, a
          train/test split, a simple baseline, and an evaluation that is good enough to show.
        </p>
        <p className="mt-3 text-sm leading-7 text-slate-600">
          No model has been trained or saved in this build. This page will not invent a percentage.
        </p>
      </section>

      <section className="card p-6">
        <h2 className="text-base font-semibold">Future prediction inputs</h2>
        <p className="mt-1 text-sm text-slate-600">
          You can fill these in to see the shape of the later form. Submitting only confirms that no model exists.
        </p>
        <form className="mt-5 space-y-4" onSubmit={onSubmit}>
          <div>
            <label className="field-label" htmlFor="prediction-platform">Platform</label>
            <select
              id="prediction-platform"
              className="field"
              value={platform}
              onChange={(event) => {
                setPlatform(event.target.value);
                setMessage(null);
              }}
            >
              {PLATFORMS.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="field-label" htmlFor="prediction-category">Category</label>
            <select
              id="prediction-category"
              className="field"
              value={category}
              onChange={(event) => {
                setCategory(event.target.value);
                setMessage(null);
              }}
            >
              {CATEGORIES.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="field-label" htmlFor="prediction-note">Note</label>
            <textarea
              id="prediction-note"
              className="field min-h-24"
              value={note}
              onChange={(event) => {
                setNote(event.target.value);
                setMessage(null);
              }}
              placeholder="Optional context. It is not stored."
            />
          </div>
          <button type="submit" className="btn-primary">Request a prediction</button>
        </form>
        {message ? (
          <p className="mt-4 rounded-lg border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-800" role="status">
            {message}
          </p>
        ) : null}
      </section>
    </div>
  );
}
