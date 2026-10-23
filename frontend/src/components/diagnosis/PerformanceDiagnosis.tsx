import type { ReactNode } from "react";
import type { DiagnosisEvidence, PerformanceDiagnosis as Diagnosis } from "../../types/diagnosis.ts";

const PRIORITY_CLASS = {
  High: "bg-rose-50 text-rose-800",
  Medium: "bg-amber-50 text-amber-900",
  Low: "bg-slate-100 text-slate-700",
} as const;

const CLAIM_LABEL = {
  observed: "Fact from your numbers",
  inference: "Likely, based on a comparison",
  hypothesis: "Possible reason (a guess)",
} as const;

const LEVEL_HINT: Record<string, string> = {
  "Limited evidence": "Based on very little data so far, so treat this as a first look.",
  "Moderate evidence": "Based on some saved data. Useful, but more data would help.",
  "Stronger evidence": "Based on plenty of saved data, so you can lean on it more.",
};

function levelText(level: string): string {
  const hint = LEVEL_HINT[level];
  return hint ? `${level}: ${hint}` : level;
}

export function PerformanceDiagnosisPanel({
  diagnosis,
  evidence,
  message,
  retrying = false,
  onRetry,
}: {
  diagnosis: Diagnosis | null;
  evidence: DiagnosisEvidence | null;
  message: string;
  retrying?: boolean;
  onRetry?: () => void;
}) {
  return (
    <section className="card space-y-5 p-5" aria-labelledby="performance-diagnosis-title">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 id="performance-diagnosis-title" className="text-base font-semibold">
            AI Performance Diagnosis
          </h2>
          <p className="mt-1 text-sm leading-6 text-slate-600">
            See what's working, what could be better, and what to try next.
          </p>
        </div>
        {onRetry ? (
          <button type="button" className="btn-secondary" onClick={onRetry} disabled={retrying}>
            {retrying ? "Updating…" : "Run the check again"}
          </button>
        ) : null}
      </div>

      {retrying ? (
        <p className="text-sm text-slate-600" role="status">
          Getting fresh numbers and updating the check…
        </p>
      ) : null}

      {evidence ? <EvidenceNote evidence={evidence} /> : null}

      {diagnosis ? (
        <>
          <p className="text-sm leading-6 text-slate-600">{message}</p>
          <DiagnosisBody diagnosis={diagnosis} />
        </>
      ) : (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4" role="status">
          <h3 className="text-sm font-semibold text-amber-950">Check-up not available</h3>
          <p className="mt-2 text-sm leading-6 text-amber-950">{message}</p>
          {evidence ? (
            <div className="mt-4">
              <h4 className="text-sm font-semibold text-slate-800">What we measured</h4>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-6 text-slate-700">
                {evidence.observations.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="mt-2 text-sm leading-6 text-amber-950">
              This saved analysis doesn't have any measured numbers for a check-up yet.
            </p>
          )}
        </div>
      )}
    </section>
  );
}

function EvidenceNote({ evidence }: { evidence: DiagnosisEvidence }) {
  return (
    <div className="rounded-lg bg-slate-50 p-4">
      <p className="text-sm font-semibold text-slate-800">{levelText(evidence.evidence_level)}</p>
      <p className="mt-1 text-xs leading-5 text-slate-500">
        Engagement shows how many people liked or commented compared with how many viewed. It's our own calculation
        ({evidence.engagement_formula}), not an official YouTube number.
      </p>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-6 text-slate-700">
        {evidence.evidence_reasons.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function DiagnosisBody({ diagnosis }: { diagnosis: Diagnosis }) {
  return (
    <div className="space-y-5">
      <div>
        <h3 className="text-sm font-semibold">In short</h3>
        <p className="mt-2 text-sm leading-6 text-slate-700">{diagnosis.summary}</p>
      </div>
      <InsightGrid
        title="What's working"
        empty="Nothing stands out as a clear strength in the numbers we have yet."
        items={diagnosis.strengths.map((item) => (
          <article key={`${item.title}-${item.evidence}`} className="rounded-lg border border-slate-200 p-4">
            <ClaimBadge kind={item.claim_kind} />
            <h4 className="mt-2 text-sm font-semibold">{item.title}</h4>
            <p className="mt-2 text-sm leading-6 text-slate-700">{item.explanation}</p>
            <p className="mt-2 text-xs leading-5 text-slate-500">Based on: {item.evidence}</p>
            {item.baseline ? <p className="mt-1 text-xs leading-5 text-slate-500">Compared with: {item.baseline}</p> : null}
          </article>
        ))}
      />
      <InsightGrid
        title="What could be better"
        empty="Nothing in the numbers we have points to a clear problem."
        items={diagnosis.improvements.map((item) => (
          <article key={`${item.title}-${item.evidence}`} className="rounded-lg border border-slate-200 p-4">
            <ClaimBadge kind={item.claim_kind} />
            <h4 className="mt-2 text-sm font-semibold">{item.title}</h4>
            <p className="mt-2 text-sm leading-6 text-slate-700">{item.explanation}</p>
            <p className="mt-2 text-xs leading-5 text-slate-500">Based on: {item.evidence}</p>
          </article>
        ))}
      />
      <InsightGrid
        title="Possible reasons"
        empty="The numbers don't point to any likely reason yet."
        items={(diagnosis.reasons ?? []).map((item) => (
          <article key={item.statement} className="rounded-lg border border-slate-200 p-4">
            <ClaimBadge kind="hypothesis" />
            <p className="mt-2 text-sm leading-6 text-slate-700">{item.statement}</p>
            <p className="mt-2 text-xs leading-5 text-slate-500">Based on: {item.evidence}</p>
          </article>
        ))}
      />
      <InsightGrid
        title="What to try next"
        empty="No next step was suggested."
        items={diagnosis.actions.map((item) => (
          <article key={`${item.priority}-${item.action}`} className="rounded-lg border border-slate-200 p-4">
            <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ${PRIORITY_CLASS[item.priority]}`}>
              {item.priority}
            </span>
            <h4 className="mt-2 text-sm font-semibold">{item.action}</h4>
            <p className="mt-2 text-sm leading-6 text-slate-700">{item.reason}</p>
            <p className="mt-2 text-xs leading-5 text-slate-500">Based on: {item.evidence}</p>
            <p className="mt-1 text-xs leading-5 text-slate-500">How to check if it worked: {item.success_measure}</p>
          </article>
        ))}
      />
      <div>
        <h3 className="text-sm font-semibold">How sure we are</h3>
        <p className="mt-2 text-sm font-medium text-slate-800">{levelText(diagnosis.evidence_quality.level)}</p>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-6 text-slate-700">
          {diagnosis.evidence_quality.limitations.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function ClaimBadge({ kind }: { kind: keyof typeof CLAIM_LABEL }) {
  return (
    <span className="inline-flex rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-700">
      {CLAIM_LABEL[kind]}
    </span>
  );
}

function InsightGrid({ title, empty, items }: { title: string; empty: string; items: ReactNode[] }) {
  return (
    <div>
      <h3 className="text-sm font-semibold">{title}</h3>
      {items.length === 0 ? (
        <p className="mt-2 text-sm text-slate-600">{empty}</p>
      ) : (
        <div className="mt-3 grid gap-3 md:grid-cols-2">{items}</div>
      )}
    </div>
  );
}
