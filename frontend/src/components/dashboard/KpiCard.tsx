interface KpiCardProps {
  label: string;
  value: string;
  detail: string;
}

export function KpiCard({ label, value, detail }: KpiCardProps) {
  return (
    <article className="card relative overflow-hidden p-5">
      <span className="absolute right-5 top-5 h-2.5 w-2.5 rounded-full bg-[#EF9620]" aria-hidden="true" />
      <h3 className="pr-6 text-sm font-medium text-slate-500">{label}</h3>
      <p className="mt-3 text-3xl font-normal tracking-normal text-[#16182B]">{value}</p>
      <p className="mt-2 text-xs leading-5 text-slate-500">{detail}</p>
    </article>
  );
}
