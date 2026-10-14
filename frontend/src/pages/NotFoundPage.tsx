import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-lg flex-col justify-center px-4">
      <h1 className="text-2xl font-semibold">That page is not part of CreatorLens</h1>
      <p className="mt-2 text-sm text-slate-600">Use the landing page or the dashboard to continue.</p>
      <div className="mt-6 flex gap-3">
        <Link to="/" className="btn-primary">Landing</Link>
        <Link to="/dashboard" className="btn-secondary">Dashboard</Link>
      </div>
    </main>
  );
}
