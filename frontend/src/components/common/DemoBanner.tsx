export function DemoBanner({ children }: { children: string }) {
  return (
    <p className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950" role="note">
      {children}
    </p>
  );
}

export function MetricCaption({ formula }: { formula: string }) {
  return (
    <p className="text-xs leading-5 text-slate-500">
      Demo data. Engagement rate shows how many people liked, commented, or shared compared with how many viewed
      ({formula}). Posts with no views are left out of the average.
    </p>
  );
}
