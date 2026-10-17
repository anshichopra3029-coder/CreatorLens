import { useEffect, useState } from "react";
import { Flame, LoaderCircle, Scale } from "lucide-react";
import {
  challengeYoutubeRoast,
  fixYoutubeRoast,
  roastYoutube,
  saveYoutubeExperiment,
  updateYoutubeExperiment,
} from "../../services/youtube.ts";
import type { RoastClaimKind, RoastStyle, VideoRoast } from "../../types/roast.ts";
import type { YoutubeAnalysis } from "../../types/youtube.ts";

const STYLES: { id: RoastStyle; label: string; detail: string }[] = [
  { id: "friendly", label: "Friendly Tease", detail: "A light opening, then the actual finding." },
  { id: "savage", label: "Savage Mode", detail: "Sharper wording, same evidence." },
  { id: "brutal", label: "Brutal Honesty", detail: "The diagnosis, without a costume." },
];

const CLAIM_LABEL: Record<RoastClaimKind, string> = {
  observed: "Observed fact",
  inference: "Inference",
  hypothesis: "Hypothesis",
};

export function RoastCourt({
  analysis,
  onChange,
}: {
  analysis: YoutubeAnalysis;
  onChange: (next: YoutubeAnalysis) => void;
}) {
  const [open, setOpen] = useState(false);
  const [style, setStyle] = useState<RoastStyle>("friendly");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [explain, setExplain] = useState(true);
  const [showEvidence, setShowEvidence] = useState(false);
  const [challengeOpen, setChallengeOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [context, setContext] = useState("");
  const [outcomeNote, setOutcomeNote] = useState(analysis.experiment?.outcome_note ?? "");
  const [followUp, setFollowUp] = useState(
    analysis.experiment?.follow_up_views === null || analysis.experiment?.follow_up_views === undefined
      ? ""
      : String(analysis.experiment.follow_up_views),
  );
  const [completed, setCompleted] = useState(analysis.experiment?.completed_task ?? false);

  const roast = analysis.roasts?.[style] ?? null;

  async function run(label: string, action: () => Promise<YoutubeAnalysis>) {
    setBusy(label);
    setError(null);
    try {
      const next = await action();
      onChange(next);
      setOutcomeNote(next.experiment?.outcome_note ?? "");
      setFollowUp(next.experiment?.follow_up_views == null ? "" : String(next.experiment.follow_up_views));
      setCompleted(next.experiment?.completed_task ?? false);
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "The roast request failed.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="card overflow-hidden" aria-label="Roast My Video">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-200 px-5 py-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-indigo-700">Roast My Video</p>
          <h2 className="mt-1 text-lg font-semibold">We'll roast your content. Then help you fix it.</h2>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-600">
            The roast can joke. The investigation, X-ray, and court use this video's saved diagnosis and do not invent missing metrics.
          </p>
        </div>
        <button type="button" className="btn-primary" onClick={() => setOpen(true)} disabled={open}>
          <Flame className="h-4 w-4" aria-hidden="true" />
          Roast My Video
        </button>
      </div>

      {open ? (
        <div className="space-y-5 p-5">
          <div className="grid gap-3 sm:grid-cols-3">
            {STYLES.map((item) => (
              <button
                key={item.id}
                type="button"
                className={`rounded-lg border px-3 py-3 text-left transition ${
                  style === item.id ? "border-indigo-600 bg-indigo-50" : "border-slate-200 bg-white hover:bg-slate-50"
                }`}
                onClick={() => setStyle(item.id)}
              >
                <span className="block text-sm font-semibold">{item.label}</span>
                <span className="mt-1 block text-xs leading-5 text-slate-600">{item.detail}</span>
              </button>
            ))}
          </div>

          {roast === null && busy === null ? (
            <button
              type="button"
              className="btn-primary"
              onClick={() => void run("roast", () => roastYoutube(analysis.id, style))}
            >
              Roast in this style
            </button>
          ) : null}

          {busy === "roast" && roast === null ? <RoastSkeleton /> : null}

          {error ? (
            <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800" role="alert">
              {error}
            </p>
          ) : null}

          {roast ? (
            <RoastBody
              roast={roast}
              busy={busy}
              explain={explain}
              showEvidence={showEvidence}
              challengeOpen={challengeOpen}
              question={question}
              context={context}
              analysis={analysis}
              experiment={analysis.experiment}
              outcomeNote={outcomeNote}
              followUp={followUp}
              completed={completed}
              onExplain={() => setExplain((value) => !value)}
              onEvidence={() => setShowEvidence((value) => !value)}
              onChallenge={() => setChallengeOpen(true)}
              onQuestion={setQuestion}
              onContext={setContext}
              onOutcome={setOutcomeNote}
              onFollowUp={setFollowUp}
              onCompleted={setCompleted}
              onAnother={() => void run("another", () => roastYoutube(analysis.id, style, true))}
              onSubmitChallenge={() =>
                void run("challenge", () => challengeYoutubeRoast(analysis.id, style, question.trim(), context.trim()))
              }
              onFix={() => void run("fix", () => fixYoutubeRoast(analysis.id, style))}
              onSaveExperiment={() => void run("experiment", () => saveYoutubeExperiment(analysis.id, style))}
              onSaveResult={() => {
                const parsed = followUp.trim() === "" ? null : Number(followUp);
                if (parsed !== null && (!Number.isInteger(parsed) || parsed < 0)) {
                  setError("Follow-up views need a whole number, or leave the field empty.");
                  return;
                }
                void run("result", () =>
                  updateYoutubeExperiment(analysis.id, {
                    outcome_note: outcomeNote,
                    follow_up_views: parsed,
                    completed_task: completed,
                  }),
                );
              }}
            />
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function RoastBody({
  roast,
  busy,
  explain,
  showEvidence,
  challengeOpen,
  question,
  context,
  analysis,
  experiment,
  outcomeNote,
  followUp,
  completed,
  onExplain,
  onEvidence,
  onChallenge,
  onQuestion,
  onContext,
  onOutcome,
  onFollowUp,
  onCompleted,
  onAnother,
  onSubmitChallenge,
  onFix,
  onSaveExperiment,
  onSaveResult,
}: {
  roast: VideoRoast;
  busy: string | null;
  explain: boolean;
  showEvidence: boolean;
  challengeOpen: boolean;
  question: string;
  context: string;
  analysis: YoutubeAnalysis;
  experiment: YoutubeAnalysis["experiment"];
  outcomeNote: string;
  followUp: string;
  completed: boolean;
  onExplain: () => void;
  onEvidence: () => void;
  onChallenge: () => void;
  onQuestion: (value: string) => void;
  onContext: (value: string) => void;
  onOutcome: (value: string) => void;
  onFollowUp: (value: string) => void;
  onCompleted: (value: boolean) => void;
  onAnother: () => void;
  onSubmitChallenge: () => void;
  onFix: () => void;
  onSaveExperiment: () => void;
  onSaveResult: () => void;
}) {
  return (
    <div className="space-y-5">
      <article className="rounded-xl border border-slate-800 bg-slate-900 p-5 text-slate-100">
        <p className="text-xs font-semibold uppercase tracking-wide text-amber-300">
          {styleLabel(roast.style)} · take {roast.take}
          {roast.source === "gemini" ? " · roast written by Gemini" : " · written from the saved counts"}
        </p>
        <p className="mt-3 text-lg font-semibold leading-7">{roast.opening}</p>
        {roast.bits && roast.bits.length > 0 ? (
          <ol className="mt-4 space-y-2">
            {roast.bits.map((bit, index) => (
              <li key={`${index}-${bit.slice(0, 24)}`} className="flex gap-3 text-sm leading-6 text-slate-100">
                <Flame className="mt-1 h-3.5 w-3.5 shrink-0 text-amber-400" aria-hidden="true" />
                <span>{bit}</span>
              </li>
            ))}
          </ol>
        ) : null}
        {roast.closer ? <p className="mt-4 text-sm italic text-amber-200">{roast.closer}</p> : null}
        {explain ? (
          <div className="mt-4 space-y-3 border-t border-slate-700 pt-4 text-sm leading-6 text-slate-200">
            <p>{roast.observation}</p>
            <p>{roast.limits}</p>
            <p className="text-slate-300">{roast.bridge}</p>
          </div>
        ) : null}
      </article>

      <Investigation lines={roast.investigation ?? []} />
      <PerformanceXRay analysis={analysis} />

      <div className="flex flex-wrap gap-2">
        <button type="button" className="btn-secondary" onClick={onExplain}>
          {explain ? "Hide the explanation" : "Explain the Roast"}
        </button>
        <button type="button" className="btn-secondary" onClick={onEvidence}>
          Show the Evidence
        </button>
        <button type="button" className="btn-secondary" onClick={onChallenge}>
          Challenge This Verdict
        </button>
        <button type="button" className="btn-secondary" onClick={onFix} disabled={busy === "fix"}>
          {busy === "fix" ? "Writing a fix…" : "Give Me a Fix"}
        </button>
        <button type="button" className="btn-secondary" onClick={onAnother} disabled={busy === "another"}>
          {busy === "another" ? "Writing another take…" : "Try Another Roast"}
        </button>
      </div>

      {showEvidence ? (
        <section className="rounded-xl border border-indigo-200 bg-indigo-50 p-4" id="roast-evidence">
          <h3 className="text-sm font-semibold text-indigo-950">Evidence behind the roast</h3>
          <ul className="mt-3 space-y-3">
            {roast.clues.map((clue) => (
              <li key={clue.label} className="text-sm leading-6 text-indigo-950">
                <p className="font-medium">{clue.label}</p>
                <p>{clue.detail}</p>
                <p className="text-xs uppercase tracking-wide text-indigo-700">Source: {clue.source}</p>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {challengeOpen ? (
        <form
          className="rounded-xl border border-slate-200 p-4"
          onSubmit={(event) => {
            event.preventDefault();
            if (question.trim() !== "") {
              onSubmitChallenge();
            }
          }}
        >
          <h3 className="text-sm font-semibold">Question the verdict</h3>
          <p className="mt-1 text-sm text-slate-600">
            Add what the saved counts cannot see. The reply reassesses the claim instead of defending it.
          </p>
          <label className="field-label mt-3" htmlFor="roast-question">
            What should be reconsidered?
          </label>
          <textarea
            id="roast-question"
            className="field min-h-20"
            value={question}
            maxLength={500}
            onChange={(event) => onQuestion(event.target.value)}
          />
          <label className="field-label mt-3" htmlFor="roast-context">
            Extra context, optional
          </label>
          <textarea
            id="roast-context"
            className="field min-h-16"
            value={context}
            maxLength={500}
            onChange={(event) => onContext(event.target.value)}
          />
          <button type="submit" className="btn-primary mt-3" disabled={busy === "challenge" || question.trim() === ""}>
            {busy === "challenge" ? "Reassessing…" : "Reassess the verdict"}
          </button>
          {roast.challenge ? (
            <p className="mt-3 text-sm leading-6 text-slate-700">{roast.challenge.reply}</p>
          ) : null}
        </form>
      ) : null}

      {roast.fixes ? (
        <section className="rounded-xl border border-slate-200 p-4">
          <h3 className="text-sm font-semibold">A practical fix</h3>
          <p className="mt-2 text-sm leading-6 text-slate-600">{roast.fixes.note}</p>
          <h4 className="mt-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Title drafts</h4>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-800">
            {roast.fixes.titles.map((title) => (
              <li key={title}>{title}</li>
            ))}
          </ul>
          <h4 className="mt-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Thumbnail concepts</h4>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-800">
            {roast.fixes.thumbnail_concepts.map((concept) => (
              <li key={concept}>{concept}</li>
            ))}
          </ul>
          <h4 className="mt-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Opening hooks</h4>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-800">
            {roast.fixes.hooks.map((hook) => (
              <li key={hook}>{hook}</li>
            ))}
          </ul>
        </section>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <CourtList title="The clues" items={roast.clues.map((clue) => ({
          title: clue.label,
          detail: clue.detail,
          evidence: clue.source,
          claim_kind: clue.claim_kind,
        }))} />
        <CourtList
          title="The defence"
          items={roast.defence.map((point) => ({
            title: point.title,
            detail: point.detail,
            evidence: point.evidence,
            claim_kind: point.claim_kind,
          }))}
        />
        <CourtList
          title="The suspects"
          items={roast.suspects.map((point) => ({
            title: point.title,
            detail: point.detail,
            evidence: point.evidence,
            claim_kind: point.claim_kind,
          }))}
        />
        <section className="rounded-xl border border-slate-200 p-4">
          <h3 className="flex items-center gap-2 text-sm font-semibold">
            <Scale className="h-4 w-4 text-indigo-700" aria-hidden="true" />
            The verdict
          </h3>
          <p className="mt-3 text-sm leading-6 text-slate-800">{roast.verdict.summary}</p>
          <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{roast.verdict.confidence}</p>
          <p className="mt-2 text-sm leading-6 text-slate-600">{roast.verdict.why}</p>
          <ul className="mt-3 list-disc space-y-1 pl-5 text-sm leading-6 text-slate-600">
            {roast.verdict.missing.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
      </div>

      <section className="rounded-xl border border-slate-200 p-4">
        <h3 className="text-sm font-semibold">Next move</h3>
        <p className="mt-2 text-sm leading-6 text-slate-800">{roast.next_move.change}</p>
        <p className="mt-2 text-sm leading-6 text-slate-600">{roast.next_move.why}</p>
        <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Metric to monitor: {roast.next_move.metric}
        </p>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Saving or finishing this task does not show that the video improved. A later view count is a record, not proof of cause.
        </p>
        {experiment ? (
          <form
            className="mt-4 space-y-3 border-t border-slate-200 pt-4"
            onSubmit={(event) => {
              event.preventDefault();
              onSaveResult();
            }}
          >
            <p className="text-sm font-medium">Saved experiment · {experiment.created_at}</p>
            <p className="text-sm leading-6 text-slate-700">{experiment.proposed_change}</p>
            <p className="text-xs text-slate-500">Watch: {experiment.metric}</p>
            <label className="field-label" htmlFor="experiment-note">
              Follow-up note
            </label>
            <textarea
              id="experiment-note"
              className="field min-h-16"
              value={outcomeNote}
              maxLength={500}
              onChange={(event) => onOutcome(event.target.value)}
            />
            <label className="field-label" htmlFor="experiment-views">
              Later public view count, optional
            </label>
            <input
              id="experiment-views"
              className="field"
              inputMode="numeric"
              value={followUp}
              onChange={(event) => onFollowUp(event.target.value)}
            />
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={completed}
                onChange={(event) => onCompleted(event.target.checked)}
              />
              I did this task
            </label>
            <button type="submit" className="btn-secondary" disabled={busy === "result"}>
              {busy === "result" ? "Saving the note…" : "Save follow-up"}
            </button>
            <p className="text-sm leading-6 text-slate-600">{experiment.result_note}</p>
          </form>
        ) : (
          <button type="button" className="btn-primary mt-4" onClick={onSaveExperiment} disabled={busy === "experiment"}>
            {busy === "experiment" ? "Saving the experiment…" : "Save this as my one move"}
          </button>
        )}
      </section>
    </div>
  );
}

function CourtList({
  title,
  items,
}: {
  title: string;
  items: { title: string; detail: string; evidence: string; claim_kind: RoastClaimKind }[];
}) {
  return (
    <section className="rounded-xl border border-slate-200 p-4">
      <h3 className="text-sm font-semibold">{title}</h3>
      {items.length === 0 ? (
        <p className="mt-3 text-sm text-slate-600">Nothing in the saved data supports an item here.</p>
      ) : (
        <ul className="mt-3 space-y-3">
          {items.map((item) => (
            <li key={`${title}-${item.title}`} className="text-sm leading-6 text-slate-700">
              <p className="font-medium text-slate-900">{item.title}</p>
              <p className="mt-1">{item.detail}</p>
              <p className="mt-1 text-slate-500">{item.evidence}</p>
              <p className="mt-1 text-xs uppercase tracking-wide text-slate-500">{CLAIM_LABEL[item.claim_kind]}</p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function DetectiveMascot() {
  return (
    <svg viewBox="0 0 80 80" className="detective-bob h-16 w-16 shrink-0" role="img" aria-label="Detective mascot">
      <circle cx="40" cy="34" r="16" fill="#e2e8f0" stroke="#312e81" strokeWidth="2" />
      <path d="M24 28c4-10 28-10 32 0v4H24z" fill="#312e81" />
      <circle cx="34" cy="34" r="2" fill="#312e81" />
      <circle cx="46" cy="34" r="2" fill="#312e81" />
      <path d="M34 42c4 3 8 3 12 0" fill="none" stroke="#312e81" strokeWidth="1.5" />
      <circle cx="58" cy="52" r="9" fill="#eef2ff" stroke="#4f46e5" strokeWidth="3" />
      <path d="M64 58l8 8" stroke="#4f46e5" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

function Investigation({ lines }: { lines: string[] }) {
  const [shown, setShown] = useState(1);
  useEffect(() => {
    setShown(1);
    if (lines.length <= 1) {
      return;
    }
    const timer = window.setInterval(() => {
      setShown((count) => (count >= lines.length ? count : count + 1));
    }, 700);
    return () => window.clearInterval(timer);
  }, [lines]);

  return (
    <section className="flex gap-4 rounded-xl border border-indigo-100 bg-indigo-50 p-4" aria-label="Investigation">
      <DetectiveMascot />
      <div>
        <h3 className="text-sm font-semibold text-indigo-950">The investigation</h3>
        <ol className="mt-2 space-y-2 text-sm leading-6 text-indigo-950">
          {lines.slice(0, shown).map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ol>
      </div>
    </section>
  );
}

function PerformanceXRay({ analysis }: { analysis: YoutubeAnalysis }) {
  const evidence = analysis.diagnosis_evidence;
  const stats = analysis.statistics;
  const views = evidence?.views ?? stats.views;
  const likes = evidence?.likes ?? stats.likes;
  const comments = evidence?.comments ?? stats.comments;
  const rate = evidence?.engagement_rate ?? stats.engagement_rate;
  const likeShare = views !== null && likes !== null && views > 0 ? (likes / views) * 100 : null;
  const commentShare = views !== null && comments !== null && views > 0 ? (comments / views) * 100 : null;
  const rows: { label: string; present: boolean }[] = [
    { label: "Discovery impressions", present: analysis.analytics.impressions !== null },
    { label: "Click-through rate", present: analysis.analytics.click_through_rate !== null },
    { label: "Audience retention", present: analysis.analytics.audience_retention !== null },
  ];

  return (
    <section className="rounded-xl border border-slate-200 p-4" aria-label="Performance X-Ray">
      <h3 className="text-sm font-semibold">Performance X-Ray</h3>
      <p className="mt-1 text-sm leading-6 text-slate-600">
        {evidence?.evidence_level ?? "Limited evidence"}. These figures are the saved counts for this video.
      </p>
      <dl className="mt-4 grid gap-3 sm:grid-cols-3">
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-500">Views</dt>
          <dd className="text-lg font-semibold">{views ?? "Unavailable"}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-500">Likes</dt>
          <dd className="text-lg font-semibold">{likes ?? "Unavailable"}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-500">Comments</dt>
          <dd className="text-lg font-semibold">{comments ?? "Unavailable"}</dd>
        </div>
      </dl>
      {likeShare !== null && commentShare !== null ? (
        <div className="mt-4 space-y-3">
          <ShareBar label="Likes per 100 views" value={likeShare} />
          <ShareBar label="Comments per 100 views" value={commentShare} />
        </div>
      ) : (
        <p className="mt-3 text-sm text-slate-600">A likes or comments share was not drawn because a required count is missing.</p>
      )}
      <p className="mt-4 text-sm leading-6 text-slate-700">
        {evidence?.baseline_label || "No other saved videos from this account form a creator median."}
      </p>
      {rate !== null ? (
        <p className="mt-2 text-sm text-slate-700">
          Engagement rate {rate.toFixed(2)}% using {evidence?.engagement_formula ?? stats.engagement_formula}.
        </p>
      ) : null}
      <ul className="mt-4 space-y-2 text-sm">
        {rows.map((row) => (
          <li key={row.label} className="flex justify-between gap-3 border-t border-slate-100 pt-2">
            <span>{row.label}</span>
            <span className="text-slate-500">{row.present ? "Supplied in this file" : "Not in this snapshot"}</span>
          </li>
        ))}
      </ul>
      {evidence && evidence.limitations.length > 0 ? (
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm leading-6 text-slate-600">
          {evidence.limitations.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}

function ShareBar({ label, value }: { label: string; value: number }) {
  const width = Math.max(0, Math.min(value, 100));
  return (
    <div>
      <div className="flex justify-between text-xs text-slate-600">
        <span>{label}</span>
        <span>{value.toFixed(2)}</span>
      </div>
      <div className="mt-1 h-2 rounded-full bg-slate-100">
        <div className="h-2 rounded-full bg-indigo-600" style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}

function RoastSkeleton() {
  return (
    <div className="space-y-3" aria-busy="true" aria-label="Writing the roast">
      <div className="flex items-center gap-3">
        <DetectiveMascot />
        <p className="text-sm text-slate-600">Opening the saved snapshot and the diagnosis…</p>
      </div>
      <div className="h-24 animate-pulse rounded-xl bg-slate-200" />
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="h-28 animate-pulse rounded-xl bg-slate-100" />
        <div className="h-28 animate-pulse rounded-xl bg-slate-100" />
      </div>
      <p className="flex items-center gap-2 text-sm text-slate-600">
        <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" />
        Reading the saved counts…
      </p>
    </div>
  );
}

function styleLabel(style: RoastStyle): string {
  return STYLES.find((item) => item.id === style)?.label ?? style;
}
