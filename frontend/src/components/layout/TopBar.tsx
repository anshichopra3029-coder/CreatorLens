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
    <header className="sticky top-0 z-20 px-4 pt-4 sm:px-6">
      <div className="flex items-center justify-between gap-3 rounded-full border border-white/80 bg-gradient-to-r from-white/95 via-[#f4f0ff]/95 to-[#e9fffb]/95 px-3 py-2.5 shadow-[0_10px_30px_rgba(41,22,225,0.07)] backdrop-blur sm:px-5">
        <div className="flex min-w-0 items-center gap-3">
          <button
            type="button"
            className="rounded-full border border-[#e4e2ee] p-2 text-[#16182B] lg:hidden"
            aria-expanded={menuOpen}
            aria-controls="app-sidebar"
            onClick={onMenu}
          >
            <Menu className="h-4 w-4" aria-hidden="true" />
            <span className="sr-only">Open navigation</span>
          </button>
          <h1 className="truncate text-lg font-normal tracking-normal text-[#16182B]">{title}</h1>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {badge ? (
            <span
              className={`rounded-full px-3 py-1 text-xs font-semibold ${
                demoBadge ? "bg-[#FFF4DE] text-[#8A5206]" : "bg-[#F3F0FF] text-[#2916E1]"
              }`}
            >
              {badge}
            </span>
          ) : null}
        </div>
      </div>
    </header>
  );
}
