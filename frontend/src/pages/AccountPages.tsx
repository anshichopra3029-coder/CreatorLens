import { useState } from "react";
import type { FormEvent, ReactNode } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { safeNext } from "../auth/RequireVerified.tsx";
import { useAuth } from "../auth/AuthProvider.tsx";
import { forgotPassword, registerAccount, resendVerification, resetPassword, verifyEmail } from "../services/account.ts";

function AuthCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="mx-auto max-w-md">
      <section className="card p-6">
        <p className="text-xs font-semibold uppercase tracking-wide text-indigo-700">CreatorLens</p>
        <h2 className="mt-2 text-2xl font-semibold tracking-tight">{title}</h2>
        <div className="mt-5">{children}</div>
      </section>
    </div>
  );
}

export function SignupPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await registerAccount(name.trim(), email.trim(), password);
      navigate("/verify-email", { state: { email: email.trim() } });
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "The account could not be created.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthCard title="Create your account">
      <form className="space-y-4" onSubmit={(event) => void onSubmit(event)}>
        <div>
          <label className="field-label" htmlFor="signup-name">Name</label>
          <input id="signup-name" className="field" value={name} autoComplete="name" required maxLength={80} onChange={(event) => setName(event.target.value)} />
        </div>
        <div>
          <label className="field-label" htmlFor="signup-email">Email</label>
          <input id="signup-email" className="field" type="email" value={email} autoComplete="email" required maxLength={200} onChange={(event) => setEmail(event.target.value)} />
        </div>
        <div>
          <label className="field-label" htmlFor="signup-password">Password</label>
          <input id="signup-password" className="field" type="password" value={password} autoComplete="new-password" required minLength={10} maxLength={200} onChange={(event) => setPassword(event.target.value)} />
          <p className="mt-1 text-xs leading-5 text-slate-500">At least 10 characters, with a letter and a number.</p>
        </div>
        {error ? <p className="text-sm text-red-700" role="alert">{error}</p> : null}
        <button type="submit" className="btn-primary w-full" disabled={busy}>{busy ? "Creating the account…" : "Create account"}</button>
      </form>
      <p className="mt-4 text-sm text-slate-600">
        Already registered? <Link to="/login" className="font-semibold text-indigo-700">Sign in</Link>
      </p>
    </AuthCard>
  );
}

export function LoginPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const user = await auth.login(email.trim(), password);
      if (!user.email_verified) {
        navigate("/verify-email", { state: { email: user.email } });
        return;
      }
      navigate(safeNext(params.get("next")));
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "Sign-in failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthCard title="Sign in">
      <form className="space-y-4" onSubmit={(event) => void onSubmit(event)}>
        <div>
          <label className="field-label" htmlFor="login-email">Email</label>
          <input id="login-email" className="field" type="email" value={email} autoComplete="email" required onChange={(event) => setEmail(event.target.value)} />
        </div>
        <div>
          <label className="field-label" htmlFor="login-password">Password</label>
          <input id="login-password" className="field" type="password" value={password} autoComplete="current-password" required onChange={(event) => setPassword(event.target.value)} />
        </div>
        {error ? <p className="text-sm text-red-700" role="alert">{error}</p> : null}
        <button type="submit" className="btn-primary w-full" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
      </form>
      <p className="mt-4 text-sm text-slate-600">
        <Link to="/forgot-password" className="font-semibold text-indigo-700">Forgot password</Link>
        {" · "}
        <Link to="/signup" className="font-semibold text-indigo-700">Create an account</Link>
      </p>
    </AuthCard>
  );
}

export function VerifyEmailPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const token = params.get("token") ?? "";
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(
    token === "" ? "Check your email for a verification link. It expires in 24 hours." : null,
  );
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function confirmToken() {
    setBusy(true);
    setError(null);
    try {
      await verifyEmail(token);
      await auth.refresh();
      setMessage("Email verified. You can use saved analyses now.");
      navigate("/profile");
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "That verification link could not be used.");
    } finally {
      setBusy(false);
    }
  }

  async function resend(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await resendVerification(email.trim());
      setMessage("If that account exists and is still unverified, a new link was sent.");
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "The verification email could not be sent.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthCard title="Verify your email">
      <p className="text-sm leading-6 text-slate-600">
        Saved analyses, diagnoses, and experiments stay locked until this address is verified.
      </p>
      {token !== "" ? (
        <button type="button" className="btn-primary mt-4" disabled={busy} onClick={() => void confirmToken()}>
          {busy ? "Checking the link…" : "Confirm this link"}
        </button>
      ) : null}
      <form className="mt-4 space-y-3" onSubmit={(event) => void resend(event)}>
        <label className="field-label" htmlFor="verify-email">Email</label>
        <input id="verify-email" className="field" type="email" value={email} required onChange={(event) => setEmail(event.target.value)} />
        <button type="submit" className="btn-secondary" disabled={busy}>Resend verification email</button>
      </form>
      {message ? <p className="mt-3 text-sm text-slate-700" role="status">{message}</p> : null}
      {error ? <p className="mt-3 text-sm text-red-700" role="alert">{error}</p> : null}
      <p className="mt-4 text-sm text-slate-600">
        <Link to="/login" className="font-semibold text-indigo-700">Back to sign in</Link>
      </p>
    </AuthCard>
  );
}

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await forgotPassword(email.trim());
      setMessage("If an account uses that email, a reset link was sent. It expires in one hour.");
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "The reset email could not be sent.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthCard title="Reset your password">
      <form className="space-y-4" onSubmit={(event) => void onSubmit(event)}>
        <div>
          <label className="field-label" htmlFor="forgot-email">Email</label>
          <input id="forgot-email" className="field" type="email" value={email} required onChange={(event) => setEmail(event.target.value)} />
        </div>
        {message ? <p className="text-sm text-slate-700" role="status">{message}</p> : null}
        {error ? <p className="text-sm text-red-700" role="alert">{error}</p> : null}
        <button type="submit" className="btn-primary" disabled={busy}>{busy ? "Sending…" : "Send reset link"}</button>
      </form>
    </AuthCard>
  );
}

export function ResetPasswordPage() {
  const [params] = useSearchParams();
  const token = params.get("token") ?? "";
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await resetPassword(token, password);
      setDone(true);
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "The password was not changed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthCard title="Choose a new password">
      {token === "" ? (
        <p className="text-sm text-red-700" role="alert">This page needs the reset link from your email.</p>
      ) : done ? (
        <p className="text-sm text-slate-700">
          Password updated. Existing sessions were signed out. <Link to="/login" className="font-semibold text-indigo-700">Sign in</Link>
        </p>
      ) : (
        <form className="space-y-4" onSubmit={(event) => void onSubmit(event)}>
          <div>
            <label className="field-label" htmlFor="reset-password">New password</label>
            <input id="reset-password" className="field" type="password" value={password} autoComplete="new-password" required minLength={10} onChange={(event) => setPassword(event.target.value)} />
          </div>
          {error ? <p className="text-sm text-red-700" role="alert">{error}</p> : null}
          <button type="submit" className="btn-primary" disabled={busy}>{busy ? "Updating…" : "Update password"}</button>
        </form>
      )}
    </AuthCard>
  );
}
