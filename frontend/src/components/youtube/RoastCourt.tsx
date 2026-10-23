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
  { id: "friendly", label: "Friendly Tease", detail: "Light, playful jokes, then the real takeaways." },
  { id: "savage", label: "Savage Mode", detail: "Sharper jokes, same honest numbers." },
  { id: "brutal", label: "Brutal Honesty", detail: "Straight talk about the numbers, no sugar-coating." },
];

const CLAIM_LABEL: Record<RoastClaimKind, string> = {
  observed: "Fact from your numbers",
  inference: "Likely, based on a comparison",
  hypothesis: "Possible reason (a guess)",
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
      setError(caught instanceof Error ? caught.message : "The roast didn't work this time. Please try again.");
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
            The roast is just for fun. Everything after the jokes sticks to this video's real saved numbers and never makes
            up missing ones.
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
                  setError("Please enter the later view count as a whole number, or leave it empty.");
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
          {roast.source === "gemini" ? " · jokes written by AI" : " · written from your saved numbers"}
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
          Show the Numbers Behind It
        </button>
        <button type="button" className="btn-secondary" onClick={onChallenge}>
          I Disagree
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
          <h3 className="text-sm font-semibold text-indigo-950">The numbers behind the roast</h3>
          <ul className="mt-3 space-y-3">
            {roast.clues.map((clue) => (
              <li key={clue.label} className="text-sm leading-6 text-indigo-950">
                <p className="font-medium">{clue.label}</p>
                <p>{clue.detail}</p>
                <p className="text-xs uppercase tracking-wide text-indigo-700">From: {clue.source}</p>
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
          <h3 className="text-sm font-semibold">Tell us what we missed</h3>
          <p className="mt-1 text-sm text-slate-600">
            Share anything the numbers can't show. We'll take another honest look instead of just defending the verdict.
          </p>
          <label className="field-label mt-3" htmlFor="roast-question">
            What do you disagree with?
          </label>
          <textarea
            id="roast-question"
            className="field min-h-20"
            value={question}
            maxLength={500}
            onChange={(event) => onQuestion(event.target.value)}
          />
          <label className="field-label mt-3" htmlFor="roast-context">
            Anything else we should know? (optional)
          </label>
          <textarea
            id="roast-context"
            className="field min-h-16"
            value={context}
            maxLength={500}
            onChange={(event) => onContext(event.target.value)}
          />
          <button type="submit" className="btn-primary mt-3" disabled={busy === "challenge" || question.trim() === ""}>
            {busy === "challenge" ? "Taking another look…" : "Take another look"}
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
          <h4 className="mt-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Title ideas</h4>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-800">
            {roast.fixes.titles.map((title) => (
              <li key={title}>{title}</li>
            ))}
          </ul>
          <h4 className="mt-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Thumbnail ideas</h4>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-800">
            {roast.fixes.thumbnail_concepts.map((concept) => (
              <li key={concept}>{concept}</li>
            ))}
          </ul>
          <h4 className="mt-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Opening lines</h4>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-800">
            {roast.fixes.hooks.map((hook) => (
              <li key={hook}>{hook}</li>
            ))}
          </ul>
        </section>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <CourtList title="The clues (what we know)" items={roast.clues.map((clue) => ({
          title: clue.label,
          detail: clue.detail,
          evidence: clue.source,
          claim_kind: clue.claim_kind,
        }))} />
        <CourtList
          title="The defence (what's going well)"
          items={roast.defence.map((point) => ({
            title: point.title,
            detail: point.detail,
            evidence: point.evidence,
            claim_kind: point.claim_kind,
          }))}
        />
        <CourtList
          title="The suspects (possible problems)"
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
        <h3 className="text-sm font-semibold">Your next move</h3>
        <p className="mt-2 text-sm leading-6 text-slate-800">{roast.next_move.change}</p>
        <p className="mt-2 text-sm leading-6 text-slate-600">{roast.next_move.why}</p>
        <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
          What to watch: {roast.next_move.metric}
        </p>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Doing this task doesn't by itself mean the video got better. A later view count is a useful record, but it
          doesn't prove what caused a change.
        </p>
        {experiment ? (
          <form
            className="mt-4 space-y-3 border-t border-slate-200 pt-4"
            onSubmit={(event) => {
              event.preventDefault();
              onSaveResult();
            }}
          >
            <p className="text-sm font-medium">Your saved plan · {experiment.created_at}</p>
            <p className="text-sm leading-6 text-slate-700">{experiment.proposed_change}</p>
            <p className="text-xs text-slate-500">What to watch: {experiment.metric}</p>
            <label className="field-label" htmlFor="experiment-note">
              How did it go? (notes)
            </label>
            <textarea
              id="experiment-note"
              className="field min-h-16"
              value={outcomeNote}
              maxLength={500}
              onChange={(event) => onOutcome(event.target.value)}
            />
            <label className="field-label" htmlFor="experiment-views">
              View count now (optional)
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
              {busy === "result" ? "Saving…" : "Save my update"}
            </button>
            <p className="text-sm leading-6 text-slate-600">{experiment.result_note}</p>
          </form>
        ) : (
          <button type="button" className="btn-primary mt-4" onClick={onSaveExperiment} disabled={busy === "experiment"}>
            {busy === "experiment" ? "Saving…" : "Save this as my next move"}
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
        <p className="mt-3 text-sm text-slate-600">Nothing to add here based on the saved numbers.</p>
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
      <circle cx="40" cy="34" r="16" fill="#E4E2EE" stroke="#2916E1" strokeWidth="2" />
      <path d="M24 28c4-10 28-10 32 0v4H24z" fill="#2916E1" />
      <circle cx="34" cy="34" r="2" fill="#2916E1" />
      <circle cx="46" cy="34" r="2" fill="#2916E1" />
      <path d="M34 42c4 3 8 3 12 0" fill="none" stroke="#2916E1" strokeWidth="1.5" />
      <circle cx="58" cy="52" r="9" fill="#F3F0FF" stroke="#5848D2" strokeWidth="3" />
      <path d="M64 58l8 8" stroke="#5848D2" strokeWidth="3" strokeLinecap="round" />
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
        <h3 className="text-sm font-semibold text-indigo-950">Looking into it</h3>
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
    { label: "Impressions (how often YouTube showed it)", present: analysis.analytics.impressions !== null },
    { label: "Click-through rate (how often people clicked)", present: analysis.analytics.click_through_rate !== null },
    { label: "Audience retention (how long people watched)", present: analysis.analytics.audience_retention !== null },
  ];

  return (
    <section className="rounded-xl border border-slate-200 p-4" aria-label="Performance X-Ray">
      <h3 className="text-sm font-semibold">Performance X-Ray</h3>
      <p className="mt-1 text-sm leading-6 text-slate-600">
        {evidence?.evidence_level ?? "Limited evidence"}. These are the saved numbers for this video.
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
        <p className="mt-3 text-sm text-slate-600">We couldn't draw these bars because a like or comment count is missing.</p>
      )}
      <p className="mt-4 text-sm leading-6 text-slate-700">
        {evidence?.baseline_label || "Not enough of your other videos are saved yet to compare with."}
      </p>
      {rate !== null ? (
        <p className="mt-2 text-sm text-slate-700">
          Engagement rate: {rate.toFixed(2)}% (likes and comments compared with views:{" "}
          {evidence?.engagement_formula ?? stats.engagement_formula}).
        </p>
      ) : null}
      <ul className="mt-4 space-y-2 text-sm">
        {rows.map((row) => (
          <li key={row.label} className="flex justify-between gap-3 border-t border-slate-100 pt-2">
            <span>{row.label}</span>
            <span className="text-slate-500">{row.present ? "Included" : "Not available"}</span>
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
        <p className="text-sm text-slate-600">Looking at your saved numbers…</p>
      </div>
      <div className="h-24 animate-pulse rounded-xl bg-slate-200" />
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="h-28 animate-pulse rounded-xl bg-slate-100" />
        <div className="h-28 animate-pulse rounded-xl bg-slate-100" />
      </div>
      <p className="flex items-center gap-2 text-sm text-slate-600">
        <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" />
        Writing the jokes…
      </p>
    </div>
  );
}

function styleLabel(style: RoastStyle): string {
  return STYLES.find((item) => item.id === style)?.label ?? style;
}
