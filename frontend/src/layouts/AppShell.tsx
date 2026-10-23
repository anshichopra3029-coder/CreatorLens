import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { Sidebar } from "../components/layout/Sidebar.tsx";
import { TopBar } from "../components/layout/TopBar.tsx";
import { useActiveDocumentId } from "../components/documents/ActiveDocumentSwitch.tsx";

const TITLES: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/upload": "Upload Dataset",
  "/youtube": "Analyze YouTube Video",
  "/documents": "Saved analyses",
  "/analytics": "Analytics",
  "/insights": "Insights",
  "/predictions": "Predictions",
  "/settings": "Settings",
};

const BADGES: Record<string, string> = {
  "/dashboard": "Demo Mode",
  "/analytics": "Demo Mode",
  "/insights": "Demo Mode",
  "/upload": "CSV, PDF, DOCX",
  "/youtube": "Public statistics",
  "/predictions": "Dated history",
  "/settings": "Local",
};

export function AppShell() {
  const location = useLocation();
  const activeDocumentId = useActiveDocumentId();
  const [menuOpen, setMenuOpen] = useState(false);
  const onAnalysis = location.pathname.startsWith("/analysis/");
  const onYoutubeAnalysis = location.pathname.startsWith("/youtube/");
  const onPerformance = location.pathname.startsWith("/performance/");
  const title = onAnalysis
    ? "Analysis"
    : onYoutubeAnalysis
      ? "YouTube analysis"
      : onPerformance
        ? "Creator analytics"
        : (TITLES[location.pathname] ?? "CreatorLens");
  const demoPage = location.pathname === "/dashboard" || location.pathname === "/analytics" || location.pathname === "/insights";
  const badge = onAnalysis || onYoutubeAnalysis || onPerformance
    ? "Saved analysis"
    : demoPage
      ? activeDocumentId
        ? "Saved analysis"
        : "Demo Mode"
      : (BADGES[location.pathname] ?? null);

  useEffect(() => {
    document.title = `${title} · CreatorLens`;
  }, [title]);

  useEffect(() => {
    if (!menuOpen) {
      return;
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setMenuOpen(false);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [menuOpen]);

  return (
    <div className="min-h-screen text-[#16182B]">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-full focus:bg-white focus:px-3 focus:py-2"
      >
        Skip to content
      </a>
      <div className="lg:grid lg:grid-cols-[18.5rem_minmax(0,1fr)]">
        <Sidebar open={menuOpen} onClose={() => setMenuOpen(false)} />
        <div className="min-w-0">
          <TopBar title={title} badge={badge} menuOpen={menuOpen} onMenu={() => setMenuOpen(true)} />
          <main id="main" className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}
