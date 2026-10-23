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
          className="fixed inset-0 z-30 bg-[#16182B]/45 lg:hidden"
          aria-label="Close navigation"
          onClick={onClose}
        />
      ) : null}
      <aside
        id="app-sidebar"
        className={`fixed inset-y-0 left-0 z-40 w-72 transition-transform lg:sticky lg:top-0 lg:z-auto lg:h-screen lg:w-auto lg:translate-x-0 lg:p-4 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-full flex-col bg-gradient-to-b from-white via-[#f6f2ff] to-[#f3fffc] lg:rounded-[1.75rem] lg:border lg:border-white/80 lg:shadow-[0_18px_50px_rgba(41,22,225,0.08)]">
          <div className="flex items-center justify-between px-4 py-5">
            <Logo onClick={onClose} />
            <button type="button" className="rounded-full p-2 text-[#4D535D] hover:bg-[#F3F0FF] lg:hidden" onClick={onClose}>
              <X className="h-4 w-4" aria-hidden="true" />
              <span className="sr-only">Close navigation</span>
            </button>
          </div>
          <nav className="flex-1 space-y-1 overflow-y-auto px-3" aria-label="Application">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={onClose}
                  className={({ isActive }) =>
                    `flex items-center gap-3 rounded-full px-3 py-2.5 text-sm font-normal transition ${
                      isActive
                        ? "bg-gradient-to-r from-[#8B74F0] to-[#2916E1] text-white shadow-[0_8px_18px_rgba(41,22,225,0.28)]"
                        : "text-[#4D535D] hover:bg-gradient-to-r hover:from-[#F3F0FF] hover:to-[#E9FFFB] hover:text-[#2916E1]"
                    }`
                  }
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  {item.label}
                </NavLink>
              );
            })}
          </nav>
          <p className="px-5 py-5 text-xs leading-5 text-[#6A7180]">
            When you open one of your saved files, the charts show your data instead of the demo. YouTube analyses have their own page.
          </p>
        </div>
      </aside>
    </>
  );
}
