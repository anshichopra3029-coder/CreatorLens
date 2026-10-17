import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider.tsx";
import { getProfile, updateDisplayName } from "../services/account.ts";
import type { ProfileResponse } from "../types/account.ts";

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  const letters = parts.slice(0, 2).map((part) => part[0]?.toUpperCase() ?? "");
  return letters.join("") || "CL";
}

function activityPath(kind: string, id: string): string | null {
  if (kind === "youtube") {
    return `/youtube/${id}`;
  }
  if (kind === "document") {
    return `/analysis/${id}`;
  }
  if (kind === "analytics") {
    return `/performance/${id}`;
  }
  return null;
}

export function ProfilePage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    getProfile()
      .then((next) => {
        if (!cancelled) {
          setProfile(next);
          setName(next.user.display_name);
        }
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "The profile could not be loaded.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function onSave(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setSaved(null);
    try {
      const user = await updateDisplayName(name.trim());
      await auth.refresh();
      setProfile((current) => (current ? { ...current, user } : current));
      setSaved("Display name updated.");
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "The profile was not updated.");
    } finally {
      setBusy(false);
    }
  }

  async function onLogout() {
    await auth.logout();
    navigate("/login");
  }

  if (!profile) {
    return error ? (
      <p className="text-sm text-red-700" role="alert">{error}</p>
    ) : (
      <p className="text-sm text-slate-600">Loading your profile…</p>
    );
  }

  const counts = [
    ["Videos analyzed", profile.videos_analyzed],
    ["Diagnoses saved", profile.diagnoses_saved],
    ["Experiments saved", profile.experiments_saved],
    ["Other saved files", profile.documents_saved],
  ] as const;

  return (
    <div className="space-y-6">
      <section className="card flex flex-wrap items-center gap-4 p-5">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-indigo-600 text-lg font-semibold text-white" aria-hidden="true">
          {initials(profile.user.display_name)}
        </div>
        <div>
          <h2 className="text-xl font-semibold">{profile.user.display_name}</h2>
          <p className="text-sm text-slate-600">{profile.user.email}</p>
          <p className="mt-1 text-xs font-semibold uppercase tracking-wide text-emerald-700">
            {profile.user.email_verified ? "Email verified" : "Email not verified"}
          </p>
        </div>
      </section>

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {counts.map(([label, value]) => (
          <article key={label} className="card p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
            <p className="mt-2 text-2xl font-semibold">{value}</p>
          </article>
        ))}
      </section>

      <section className="card p-5">
        <h2 className="text-base font-semibold">Account settings</h2>
        <form className="mt-4 max-w-md space-y-3" onSubmit={(event) => void onSave(event)}>
          <div>
            <label className="field-label" htmlFor="profile-name">Display name</label>
            <input id="profile-name" className="field" value={name} required maxLength={80} onChange={(event) => setName(event.target.value)} />
          </div>
          <div>
            <label className="field-label" htmlFor="profile-email">Email</label>
            <input id="profile-email" className="field" value={profile.user.email} disabled />
          </div>
          {saved ? <p className="text-sm text-slate-700" role="status">{saved}</p> : null}
          {error ? <p className="text-sm text-red-700" role="alert">{error}</p> : null}
          <div className="flex flex-wrap gap-3">
            <button type="submit" className="btn-primary" disabled={busy}>{busy ? "Saving…" : "Save name"}</button>
            <button type="button" className="btn-secondary" onClick={() => void onLogout()}>Log out</button>
          </div>
        </form>
      </section>

      <section className="card p-5">
        <h2 className="text-base font-semibold">Recent activity</h2>
        {profile.recent.length === 0 ? (
          <p className="mt-2 text-sm text-slate-600">No saved analyses yet. A public YouTube preview can be saved after you analyze it.</p>
        ) : (
          <ul className="mt-3 divide-y divide-slate-200">
            {profile.recent.map((item) => {
              const path = activityPath(item.kind, item.id);
              return (
                <li key={`${item.kind}-${item.id}`} className="flex flex-wrap items-center justify-between gap-3 py-3">
                  <div>
                    <p className="text-sm font-medium">{item.title}</p>
                    <p className="text-xs text-slate-500">{item.kind} · {item.created_at}</p>
                  </div>
                  {path ? <Link to={path} className="btn-secondary">Open</Link> : null}
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}
