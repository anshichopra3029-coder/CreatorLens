import { Link } from "react-router-dom";
import { QueryPanel } from "../components/common/QueryPanel.tsx";
import { useApiQuery } from "../hooks/useApiQuery.ts";
import { setActiveDocumentId } from "../services/activeDocument.ts";
import { listDocuments } from "../services/documents.ts";
import { formatBytes } from "../services/format.ts";

export function DocumentsPage() {
  const saved = useApiQuery(() => listDocuments(), "documents");
  return (
    <div className="space-y-6">
      <p className="max-w-2xl text-sm leading-6 text-slate-600">
        These analyses were saved by the server. Opening one makes it the active dataset on the dashboard.
      </p>
      <QueryPanel
        query={saved}
        loadingLabel="Loading saved analyses"
        emptyTitle="No saved analyses"
        emptyBody="Upload a CSV, PDF, or DOCX file to create the first analysis."
        isEmpty={(data) => data.documents.length === 0}
      >
        {(data) => (
          <ul className="card divide-y divide-slate-200">
            {data.documents.map((item) => (
              <li key={item.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold">{item.filename}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {item.format.toUpperCase()} · {formatBytes(item.size_bytes)} · {item.status}
                    {item.file_saved ? " · saved" : ""}
                  </p>
                  {item.summary ? <p className="mt-2 max-w-2xl text-sm text-slate-600">{item.summary}</p> : null}
                </div>
                <Link
                  to={`/analysis/${item.id}`}
                  className="btn-secondary"
                  onClick={() => setActiveDocumentId(item.id)}
                >
                  Open
                </Link>
              </li>
            ))}
          </ul>
        )}
      </QueryPanel>
      <Link to="/upload" className="btn-primary inline-flex">
        Upload another document
      </Link>
    </div>
  );
}
