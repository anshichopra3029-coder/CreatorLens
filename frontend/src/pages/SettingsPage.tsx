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
      setHealthMessage(`Connected. ${health.service} is running (status: “${health.status}”).`);
    } catch (error: unknown) {
      setHealthState("error");
      setHealthMessage(error instanceof Error ? error.message : "We couldn't reach the CreatorLens server.");
    }
  }

  return (
    <div className="space-y-4">
      <p className="max-w-2xl text-sm leading-6 text-slate-600">
        Your saved analyses stay on this computer.
      </p>

      <section className="card p-5">
        <h2 className="text-base font-semibold">App preferences</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Use the button below to check that the app can talk to the CreatorLens server.
        </p>
        <p className="mt-3 text-sm text-slate-800">
          Server address (technical, set by <code>VITE_API_BASE_URL</code>):{" "}
          <span className="font-medium">{apiBaseUrl() || "same origin (/api)"}</span>
        </p>
        <button
          type="button"
          className="btn-primary mt-4"
          onClick={() => void checkConnection()}
          disabled={healthState === "loading"}
        >
          {healthState === "loading" ? "Checking…" : "Check connection"}
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
          Files you upload are saved and analysed. When you open one of them, the Dashboard, Analytics, and Insights
          pages show your data instead of the demo. There's nothing else to set up here.
        </p>
        <Link to="/upload" className="btn-secondary mt-4">
          Go to upload
        </Link>
      </section>

      <section className="card p-5">
        <h2 className="text-base font-semibold">Saved work</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Your YouTube analyses, documents, and analytics files are saved without needing an account. Sign-in is
          paused for now.
        </p>
      </section>
    </div>
  );
}
