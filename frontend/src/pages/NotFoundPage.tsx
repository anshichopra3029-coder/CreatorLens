import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-lg flex-col justify-center px-4 py-10">
      <section className="card p-8">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#5848D2]">404</p>
        <h1 className="mt-2 text-3xl font-normal tracking-normal text-[#16182B]">We couldn't find that page</h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">Go back to the home page or the dashboard to keep going.</p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link to="/" className="btn-primary">Landing</Link>
          <Link to="/dashboard" className="btn-secondary">Dashboard</Link>
        </div>
      </section>
    </main>
  );
}
