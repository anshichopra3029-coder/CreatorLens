import { useState } from "react";
import { Link } from "react-router-dom";
import { apiBaseUrl, getHealth } from "../services/api.ts";

export function SettingsPage() {
  const [healthState, setHealthState] = useState<"idle" | "loading" | "ok" | "error">("idle");
  const [healthMessage, setHealthMessage] = useState("");

  async function checkConnection() {
    setHealthState("loading");
    setHealthMessage("");
    try {
      const health = await getHealth();
      setHealthState("ok");
      setHealthMessage(`${health.service} responded with status “${health.status}”.`);
    } catch (error: unknown) {
      setHealthState("error");
      setHealthMessage(error instanceof Error ? error.message : "The API could not be reached.");
    }
  }

  return (
    <div className="space-y-4">
      <p className="max-w-2xl text-sm leading-6 text-slate-600">
        Account features arrive in a later phase. Nothing on this page is saved to a profile or a database.
      </p>

      <section className="card p-5">
        <h2 className="text-base font-semibold">App preferences</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Appearance stays light in this phase. The API address comes from <code>VITE_API_BASE_URL</code>.
        </p>
        <p className="mt-3 text-sm text-slate-800">
          Current API base URL: <span className="font-medium">{apiBaseUrl()}</span>
        </p>
        <button
          type="button"
          className="btn-primary mt-4"
          onClick={() => void checkConnection()}
          disabled={healthState === "loading"}
        >
          {healthState === "loading" ? "Checking…" : "Check API connection"}
        </button>
        {healthMessage ? (
          <p
            className={`mt-3 text-sm ${healthState === "error" ? "text-red-700" : "text-slate-700"}`}
            role={healthState === "error" ? "alert" : "status"}
          >
            {healthMessage}
          </p>
        ) : null}
      </section>

      <section className="card p-5">
        <h2 className="text-base font-semibold">Dataset preferences</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Uploaded files are validated in memory and then discarded. There is no saved dataset to configure, and the
          charts continue to use the built-in demo file.
        </p>
        <Link to="/upload" className="btn-secondary mt-4">
          Go to upload
        </Link>
      </section>

      <section className="card p-5">
        <h2 className="text-base font-semibold">Profile and account</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Sign-in, profiles, and saved preferences are not part of this build. The fields below are disabled on purpose.
        </p>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <div>
            <label className="field-label" htmlFor="display-name">Display name</label>
            <input id="display-name" className="field" value="" disabled placeholder="Available in a later phase" />
          </div>
          <div>
            <label className="field-label" htmlFor="account-email">Email</label>
            <input id="account-email" className="field" value="" disabled placeholder="Available in a later phase" />
          </div>
        </div>
      </section>
    </div>
  );
}
