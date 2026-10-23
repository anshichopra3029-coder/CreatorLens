import { useEffect, useState, type ReactNode } from "react";
import { DocumentResults } from "./DocumentResults.tsx";
import { activeDocumentEvent, clearActiveDocumentId, getActiveDocumentId } from "../../services/activeDocument.ts";
import { getDocument } from "../../services/documents.ts";
import { useApiQuery } from "../../hooks/useApiQuery.ts";

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
  return <OwnedDocument id={id} demo={demo} />;
}

function OwnedDocument({ id, demo }: { id: string; demo: ReactNode }) {
  const query = useApiQuery(() => getDocument(id), id);
  useEffect(() => {
    if (query.status === "error" && query.error.toLowerCase().includes("not found")) {
      clearActiveDocumentId();
    }
  }, [query]);

  if (query.status === "error") {
    const missing = query.error.toLowerCase().includes("not found");
    if (missing) {
      return demo;
    }
    return (
      <p className="card border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
        {query.error}
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-slate-600">You're seeing results from your own saved file, not the demo data.</p>
        <button type="button" className="btn-secondary" onClick={clearActiveDocumentId}>
          Show demo data
        </button>
      </div>
      <DocumentResults documentId={id} />
    </div>
  );
}
