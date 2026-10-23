import { FileText, Trash2 } from "lucide-react";
import { useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useApiQuery } from "../hooks/useApiQuery.ts";
import { setActiveDocumentId } from "../services/activeDocument.ts";
import { listDocuments, uploadDocument } from "../services/documents.ts";
import { formatBytes } from "../services/format.ts";
import { MAX_DOCUMENT_BYTES } from "../services/limits.ts";

const ACCEPT = ".csv,.pdf,.docx,text/csv,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document";

type UploadState =
  | { phase: "idle" }
  | { phase: "ready"; file: File }
  | { phase: "invalid"; file: File; message: string }
  | { phase: "uploading"; file: File; progress: number }
  | { phase: "error"; file: File; message: string };

function extension(name: string): string {
  const index = name.lastIndexOf(".");
  return index === -1 ? "" : name.slice(index).toLowerCase();
}

function validateClientFile(file: File): string | null {
  const suffix = extension(file.name);
  if (suffix !== ".csv" && suffix !== ".pdf" && suffix !== ".docx") {
    return "Please choose a CSV, PDF, or Word (.docx) file. Other file types aren't supported.";
  }
  if (file.size === 0) {
    return "That file is empty.";
  }
  if (file.size > MAX_DOCUMENT_BYTES) {
    return "That file is bigger than 15 MB. Please choose a smaller file.";
  }
  return null;
}

export function UploadPage() {
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const saved = useApiQuery(() => listDocuments(), "documents");
  const [dragging, setDragging] = useState(false);
  const [state, setState] = useState<UploadState>({ phase: "idle" });

  function takeFile(file: File | undefined) {
    if (!file) {
      return;
    }
    const message = validateClientFile(file);
    setState(message ? { phase: "invalid", file, message } : { phase: "ready", file });
  }

  function clearFile() {
    setState({ phase: "idle" });
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }

  async function analyseFile() {
    if (state.phase !== "ready" && state.phase !== "error") {
      return;
    }
    const file = state.file;
    const message = validateClientFile(file);
    if (message) {
      setState({ phase: "invalid", file, message });
      return;
    }
    setState({ phase: "uploading", file, progress: 0 });
    try {
      const result = await uploadDocument(file, (progress) => {
        setState({ phase: "uploading", file, progress });
      });
      setActiveDocumentId(result.id);
      navigate(`/analysis/${result.id}`);
    } catch (error: unknown) {
          const text = error instanceof Error ? error.message : "The upload didn't work. Please try again.";
      setState({ phase: "error", file, message: text });
    }
  }

  const selected = state.phase === "idle" ? null : state.file;
  const canSubmit = state.phase === "ready" || state.phase === "error";

  return (
    <div className="space-y-6">
      <p className="max-w-2xl text-sm leading-6 text-slate-600">
        Upload a CSV of your posts, or a PDF or Word file. For a CSV, we work out the numbers for you. For a PDF or
        Word file, we read the text and write a short summary. Your file is saved so you can come back to it.
      </p>

      <section
        className={`card border-dashed p-6 ${dragging ? "border-indigo-400 bg-indigo-50" : "border-slate-300"}`}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          takeFile(event.dataTransfer.files[0]);
        }}
        aria-label="Document upload"
      >
        <div className="flex flex-col items-start gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-base font-semibold">Choose a document</h2>
            <p className="mt-1 text-sm text-slate-600">Drag a file here, or click Browse. CSV, PDF, or Word (.docx), up to 15 MB.</p>
          </div>
          <label htmlFor="dataset-file" className="btn-secondary cursor-pointer">
            Browse files
          </label>
          <input
            ref={inputRef}
            id="dataset-file"
            className="sr-only"
            type="file"
            accept={ACCEPT}
            onChange={(event) => takeFile(event.target.files?.[0])}
          />
        </div>

        {selected ? (
          <div className="mt-5 flex items-center justify-between gap-3 rounded-lg border border-slate-200 bg-slate-50 px-3 py-3">
            <div className="flex min-w-0 items-center gap-3">
              <FileText className="h-5 w-5 shrink-0 text-indigo-700" aria-hidden="true" />
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-slate-900">{selected.name}</p>
                <p className="text-xs text-slate-500">
                  {extension(selected.name).replace(".", "").toUpperCase() || "File"} · {formatBytes(selected.size)}
                </p>
              </div>
            </div>
            <button type="button" className="rounded-lg p-2 text-slate-500 hover:bg-white" onClick={clearFile}>
              <Trash2 className="h-4 w-4" aria-hidden="true" />
              <span className="sr-only">Remove file</span>
            </button>
          </div>
        ) : (
          <p className="mt-5 text-sm text-slate-500">No file selected.</p>
        )}

        {state.phase === "invalid" || state.phase === "error" ? (
          <p className="mt-4 text-sm text-red-700" role="alert">
            {state.message}
          </p>
        ) : null}
        {state.phase === "uploading" ? (
          <p className="mt-4 text-sm text-slate-600" role="status">
            Analysing {selected?.name}… {state.progress}% uploaded.
          </p>
        ) : null}

        <div className="mt-5">
          <button type="button" className="btn-primary" disabled={!canSubmit} onClick={analyseFile}>
            Analyse document
          </button>
        </div>
      </section>

      <section className="card p-5">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-base font-semibold">Previously saved analyses</h2>
          <Link to="/documents" className="text-sm font-semibold text-indigo-700">
            Open the list
          </Link>
        </div>
        {saved.status === "loading" ? <p className="mt-3 text-sm text-slate-500">Loading your saved files…</p> : null}
        {saved.status === "error" ? <p className="mt-3 text-sm text-red-700">{saved.error}</p> : null}
        {saved.status === "success" && saved.data.documents.length === 0 ? (
          <p className="mt-3 text-sm text-slate-500">You haven't saved any files yet.</p>
        ) : null}
        {saved.status === "success" && saved.data.documents.length > 0 ? (
          <ul className="mt-4 divide-y divide-slate-200">
            {saved.data.documents.slice(0, 5).map((item) => (
              <li key={item.id} className="flex flex-wrap items-center justify-between gap-2 py-3">
                <div>
                  <p className="text-sm font-medium">{item.filename}</p>
                  <p className="text-xs text-slate-500">
                    {item.format.toUpperCase()} · {item.status}
                  </p>
                </div>
                <Link
                  to={`/analysis/${item.id}`}
                  className="text-sm font-semibold text-indigo-700"
                  onClick={() => setActiveDocumentId(item.id)}
                >
                  View
                </Link>
              </li>
            ))}
          </ul>
        ) : null}
      </section>
    </div>
  );
}
