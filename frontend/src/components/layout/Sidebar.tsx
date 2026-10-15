import { Files, LayoutDashboard, Lightbulb, LineChart, Settings, Sparkles, Upload, Video, X } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { NavLink } from "react-router-dom";
import { Logo } from "../common/Logo.tsx";

const NAV_ITEMS: { to: string; label: string; icon: LucideIcon }[] = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/upload", label: "Upload Dataset", icon: Upload },
  { to: "/youtube", label: "Analyze YouTube", icon: Video },
  { to: "/documents", label: "Saved analyses", icon: Files },
  { to: "/analytics", label: "Analytics", icon: LineChart },
  { to: "/insights", label: "Insights", icon: Lightbulb },
  { to: "/predictions", label: "Predictions", icon: Sparkles },
  { to: "/settings", label: "Settings", icon: Settings },
];

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

export function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {open ? (
        <button
          type="button"
          className="fixed inset-0 z-30 bg-slate-900/40 lg:hidden"
          aria-label="Close navigation"
          onClick={onClose}
        />
      ) : null}
      <aside
        id="app-sidebar"
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-200 bg-white transition-transform lg:sticky lg:top-0 lg:z-auto lg:h-screen lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between px-4 py-4">
          <Logo onClick={onClose} />
          <button type="button" className="rounded-lg p-2 text-slate-600 lg:hidden" onClick={onClose}>
            <X className="h-4 w-4" aria-hidden="true" />
            <span className="sr-only">Close navigation</span>
          </button>
        </div>
        <nav className="flex-1 space-y-1 px-3" aria-label="Application">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium ${
                    isActive ? "bg-indigo-50 text-indigo-700" : "text-slate-700 hover:bg-slate-100"
                  }`
                }
              >
                <Icon className="h-4 w-4" aria-hidden="true" />
                {item.label}
              </NavLink>
            );
          })}
        </nav>
        <p className="px-4 py-4 text-xs leading-5 text-slate-500">
          Saved document analyses replace the demo charts until you choose demo data again. YouTube analyses stay on their own page.
        </p>
      </aside>
    </>
  );
}
