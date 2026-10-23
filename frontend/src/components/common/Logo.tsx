import { Aperture } from "lucide-react";
import { Link } from "react-router-dom";

export function Logo({ className = "", onClick, light = false }: { className?: string; onClick?: () => void; light?: boolean }) {
  return (
    <Link
      to="/"
      onClick={onClick}
      className={`inline-flex items-center gap-2.5 font-normal tracking-normal ${light ? "text-white" : "text-[#16182B]"} ${className}`}
    >
      <span className={`inline-flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br shadow-[0_8px_16px_rgba(41,22,225,0.28)] ${light ? "from-white to-[#d9fff9] text-[#2916E1]" : "from-[#8B74F0] to-[#2916E1] text-white"}`}>
        <Aperture className="h-4 w-4" aria-hidden="true" />
      </span>
      CreatorLens
    </Link>
  );
}
