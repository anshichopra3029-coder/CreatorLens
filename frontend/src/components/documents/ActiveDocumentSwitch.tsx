import { useEffect, useState, type ReactNode } from "react";
import { DocumentResults } from "./DocumentResults.tsx";
import { activeDocumentEvent, clearActiveDocumentId, getActiveDocumentId } from "../../services/activeDocument.ts";

export function useActiveDocumentId(): string | null {
  const [id, setId] = useState<string | null>(() => getActiveDocumentId());

  useEffect(() => {
    function sync() {
      setId(getActiveDocumentId());
    }
    window.addEventListener(activeDocumentEvent, sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener(activeDocumentEvent, sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  return id;
}

export function ActiveDocumentSwitch({ demo }: { demo: ReactNode }) {
  const id = useActiveDocumentId();
  if (!id) {
    return demo;
  }
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-slate-600">These results come from your saved document, not the demo dataset.</p>
        <button type="button" className="btn-secondary" onClick={clearActiveDocumentId}>
          Show demo data
        </button>
      </div>
      <DocumentResults documentId={id} />
    </div>
  );
}
