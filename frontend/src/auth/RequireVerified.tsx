import { Link, Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "./AuthProvider.tsx";

export function RequireVerified() {
  const auth = useAuth();
  const location = useLocation();
  if (auth.status === "loading") {
    return <p className="text-sm text-slate-600">Checking your session…</p>;
  }
  if (!auth.user) {
    const next = `${location.pathname}${location.search}`;
    return <Navigate to={`/login?next=${encodeURIComponent(next)}`} replace />;
  }
  if (!auth.user.email_verified) {
    return <Navigate to="/verify-email" replace />;
  }
  return <Outlet />;
}

export function SignInPrompt({ body }: { body: string }) {
  return (
    <section className="card p-5">
      <h2 className="text-base font-semibold">Sign in to use your private history</h2>
      <p className="mt-2 text-sm leading-6 text-slate-600">{body}</p>
      <div className="mt-4 flex flex-wrap gap-3">
        <Link to="/login" className="btn-primary">
          Sign in
        </Link>
        <Link to="/signup" className="btn-secondary">
          Create an account
        </Link>
      </div>
    </section>
  );
}

export function safeNext(value: string | null): string {
  if (!value || !value.startsWith("/") || value.startsWith("//") || value.includes("://")) {
    return "/profile";
  }
  return value;
}
