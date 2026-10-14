import { Aperture } from "lucide-react";
import { Link } from "react-router-dom";

export function Logo({ className = "", onClick }: { className?: string; onClick?: () => void }) {
  return (
    <Link
      to="/"
      onClick={onClick}
      className={`inline-flex items-center gap-2 font-semibold tracking-tight text-slate-900 ${className}`}
    >
      <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white">
        <Aperture className="h-4 w-4" aria-hidden="true" />
      </span>
      CreatorLens
    </Link>
  );
}
