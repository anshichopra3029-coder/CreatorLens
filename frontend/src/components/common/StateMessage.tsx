import { AlertCircle, Inbox, LoaderCircle } from "lucide-react";

export function LoadingState({ label }: { label: string }) {
  return (
    <div className="card flex items-center gap-3 p-5 text-sm text-slate-600" role="status" aria-live="polite">
      <LoaderCircle className="h-4 w-4 animate-spin text-indigo-600" aria-hidden="true" />
      {label}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="card border-red-200 bg-red-50 p-5" role="alert">
      <div className="flex items-start gap-3">
        <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-700" aria-hidden="true" />
        <div>
          <p className="font-medium text-red-950">We couldn't load this</p>
          <p className="mt-1 text-sm text-red-900">{message}</p>
          {onRetry ? (
            <button type="button" className="btn-secondary mt-3 bg-white" onClick={onRetry}>
              Try again
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="card flex items-start gap-3 p-5">
      <Inbox className="mt-0.5 h-5 w-5 shrink-0 text-slate-500" aria-hidden="true" />
      <div>
        <p className="font-medium text-slate-900">{title}</p>
        <p className="mt-1 text-sm text-slate-600">{body}</p>
      </div>
    </div>
  );
}
