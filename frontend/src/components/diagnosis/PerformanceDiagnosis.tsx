import type { ReactNode } from "react";
import type { DiagnosisEvidence, PerformanceDiagnosis as Diagnosis } from "../../types/diagnosis.ts";

const PRIORITY_CLASS = {
  High: "bg-rose-50 text-rose-800",
  Medium: "bg-amber-50 text-amber-900",
  Low: "bg-slate-100 text-slate-700",
} as const;

const CLAIM_LABEL = {
  observed: "Observed fact",
  inference: "Inference",
  hypothesis: "Hypothesis",
} as const;

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
            Understand what's working, identify opportunities, and discover your next best move.
          </p>
        </div>
        {onRetry ? (
          <button type="button" className="btn-secondary" onClick={onRetry} disabled={retrying}>
            {retrying ? "Updating the diagnosis…" : "Retry diagnosis"}
          </button>
        ) : null}
      </div>

      {retrying ? (
        <p className="text-sm text-slate-600" role="status">
          Updating the diagnosis…
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
          <h3 className="text-sm font-semibold text-amber-950">Diagnosis unavailable</h3>
          <p className="mt-2 text-sm leading-6 text-amber-950">{message}</p>
          {evidence ? (
            <div className="mt-4">
              <h4 className="text-sm font-semibold text-slate-800">Measured evidence</h4>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-6 text-slate-700">
                {evidence.observations.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="mt-2 text-sm leading-6 text-amber-950">
              This saved analysis has no calculated diagnosis evidence yet.
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
      <p className="text-sm font-semibold text-slate-800">{evidence.evidence_level}</p>
      <p className="mt-1 text-xs leading-5 text-slate-500">
        Engagement rate by views uses {evidence.engagement_formula}. This is a calculated rate, not YouTube's official analytics metric.
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
        <h3 className="text-sm font-semibold">Performance summary</h3>
        <p className="mt-2 text-sm leading-6 text-slate-700">{diagnosis.summary}</p>
      </div>
      <InsightGrid
        title="What's working"
        empty="No measured strength is available for this evidence."
        items={diagnosis.strengths.map((item) => (
          <article key={`${item.title}-${item.evidence}`} className="rounded-lg border border-slate-200 p-4">
            <ClaimBadge kind={item.claim_kind} />
            <h4 className="mt-2 text-sm font-semibold">{item.title}</h4>
            <p className="mt-2 text-sm leading-6 text-slate-700">{item.explanation}</p>
            <p className="mt-2 text-xs leading-5 text-slate-500">Evidence: {item.evidence}</p>
            {item.baseline ? <p className="mt-1 text-xs leading-5 text-slate-500">Baseline: {item.baseline}</p> : null}
          </article>
        ))}
      />
      <InsightGrid
        title="Improvement opportunities"
        empty="No measured improvement opportunity is available for this evidence."
        items={diagnosis.improvements.map((item) => (
          <article key={`${item.title}-${item.evidence}`} className="rounded-lg border border-slate-200 p-4">
            <ClaimBadge kind={item.claim_kind} />
            <h4 className="mt-2 text-sm font-semibold">{item.title}</h4>
            <p className="mt-2 text-sm leading-6 text-slate-700">{item.explanation}</p>
            <p className="mt-2 text-xs leading-5 text-slate-500">Evidence: {item.evidence}</p>
          </article>
        ))}
      />
      <InsightGrid
        title="Possible reasons"
        empty="No hypothesis was supported by the available evidence."
        items={(diagnosis.reasons ?? []).map((item) => (
          <article key={item.statement} className="rounded-lg border border-slate-200 p-4">
            <ClaimBadge kind="hypothesis" />
            <p className="mt-2 text-sm leading-6 text-slate-700">{item.statement}</p>
            <p className="mt-2 text-xs leading-5 text-slate-500">Evidence: {item.evidence}</p>
          </article>
        ))}
      />
      <InsightGrid
        title="Recommended action plan"
        empty="No testable action was returned."
        items={diagnosis.actions.map((item) => (
          <article key={`${item.priority}-${item.action}`} className="rounded-lg border border-slate-200 p-4">
            <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ${PRIORITY_CLASS[item.priority]}`}>
              {item.priority}
            </span>
            <h4 className="mt-2 text-sm font-semibold">{item.action}</h4>
            <p className="mt-2 text-sm leading-6 text-slate-700">{item.reason}</p>
            <p className="mt-2 text-xs leading-5 text-slate-500">Evidence: {item.evidence}</p>
            <p className="mt-1 text-xs leading-5 text-slate-500">Test: {item.success_measure}</p>
          </article>
        ))}
      />
      <div>
        <h3 className="text-sm font-semibold">Evidence and confidence</h3>
        <p className="mt-2 text-sm font-medium text-slate-800">{diagnosis.evidence_quality.level}</p>
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
