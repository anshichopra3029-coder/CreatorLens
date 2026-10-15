import { useEffect } from "react";
import { useParams } from "react-router-dom";
import { DocumentResults } from "../components/documents/DocumentResults.tsx";
import { setActiveDocumentId } from "../services/activeDocument.ts";

export function DocumentAnalysisPage() {
  const { documentId } = useParams();
  useEffect(() => {
    if (documentId) {
      setActiveDocumentId(documentId);
    }
  }, [documentId]);

  if (!documentId) {
    return <p className="text-sm text-slate-600">Choose a saved analysis.</p>;
  }
  return <DocumentResults documentId={documentId} />;
}
