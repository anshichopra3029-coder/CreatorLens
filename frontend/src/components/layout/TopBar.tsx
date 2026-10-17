import { Menu } from "lucide-react";

interface TopBarProps {
  title: string;
  badge: string | null;
  menuOpen: boolean;
  onMenu: () => void;
}

export function TopBar({ title, badge, menuOpen, onMenu }: TopBarProps) {
  const demoBadge = badge === "Demo Mode";
  return (
    <header className="sticky top-0 z-20 flex items-center justify-between gap-3 border-b border-slate-200 bg-white/95 px-4 py-3 backdrop-blur sm:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <button
          type="button"
          className="rounded-lg border border-slate-200 p-2 text-slate-700 lg:hidden"
          aria-expanded={menuOpen}
          aria-controls="app-sidebar"
          onClick={onMenu}
        >
          <Menu className="h-4 w-4" aria-hidden="true" />
          <span className="sr-only">Open navigation</span>
        </button>
        <h1 className="truncate text-lg font-semibold tracking-tight text-slate-900">{title}</h1>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {badge ? (
          <span
            className={`rounded-full border px-2.5 py-1 text-xs font-medium ${
              demoBadge
                ? "border-amber-200 bg-amber-50 text-amber-900"
                : "border-slate-200 bg-slate-50 text-slate-600"
            }`}
          >
            {badge}
          </span>
        ) : null}
      </div>
    </header>
  );
}
