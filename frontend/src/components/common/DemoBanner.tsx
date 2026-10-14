export function DemoBanner({ children }: { children: string }) {
  return (
    <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-950" role="note">
      {children}
    </p>
  );
}

export function MetricCaption({ formula }: { formula: string }) {
  return (
    <p className="text-xs leading-5 text-slate-500">
      Demo data. View-based engagement rate = {formula}. Posts without a positive view count are left out of the average.
    </p>
  );
}
