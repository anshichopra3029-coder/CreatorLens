import { FileSpreadsheet, Trash2 } from "lucide-react";
import { useRef, useState } from "react";
import { uploadCsv } from "../services/api.ts";
import { formatBytes, formatNumber } from "../services/format.ts";
import { MAX_UPLOAD_BYTES } from "../services/limits.ts";
import type { UploadResponse } from "../types/api.ts";

type UploadState =
  | { phase: "idle" }
  | { phase: "ready"; file: File }
  | { phase: "invalid"; file: File; message: string }
  | { phase: "uploading"; file: File; progress: number }
  | { phase: "success"; file: File; result: UploadResponse }
  | { phase: "error"; file: File; message: string };

function validateClientFile(file: File): string | null {
  if (!file.name.toLowerCase().endsWith(".csv")) {
    return "Only .csv files are accepted.";
  }
  if (file.size === 0) {
    return "That file is empty.";
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    return "That file is larger than 5 MB. Choose a smaller CSV.";
  }
  return null;
}

export function UploadPage() {
  const inputRef = useRef<HTMLInputElement>(null);
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

  async function checkFile() {
    if (state.phase === "idle" || state.phase === "invalid" || state.phase === "uploading") {
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
      const result = await uploadCsv(file, (progress) => {
        setState({ phase: "uploading", file, progress });
      });
      setState({ phase: "success", file, result });
    } catch (error: unknown) {
      const text = error instanceof Error ? error.message : "The upload failed.";
      setState({ phase: "error", file, message: text });
    }
  }

  const selected = state.phase === "idle" ? null : state.file;
  const canSubmit = state.phase === "ready" || state.phase === "error" || state.phase === "success";

  return (
    <div className="space-y-6">
      <p className="max-w-2xl text-sm leading-6 text-slate-600">
        This check confirms that the file is a CSV the server can read. It returns metadata only. The file is not
        saved, and the dashboard keeps showing the demo dataset.
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
        aria-label="CSV upload"
      >
        <div className="flex flex-col items-start gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-base font-semibold">Choose a CSV</h2>
            <p className="mt-1 text-sm text-slate-600">Drag a file here or browse. Limit: 5 MB. CSV only.</p>
          </div>
          <label htmlFor="dataset-file" className="btn-secondary cursor-pointer">
            Browse files
          </label>
          <input
            ref={inputRef}
            id="dataset-file"
            className="sr-only"
            type="file"
            accept=".csv,text/csv"
            onChange={(event) => takeFile(event.target.files?.[0])}
          />
        </div>

        {selected ? (
          <div className="mt-5 flex items-center justify-between gap-3 rounded-lg border border-slate-200 bg-slate-50 px-3 py-3">
            <div className="flex min-w-0 items-center gap-3">
              <FileSpreadsheet className="h-5 w-5 shrink-0 text-indigo-700" aria-hidden="true" />
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-slate-900">{selected.name}</p>
                <p className="text-xs text-slate-500">{formatBytes(selected.size)}</p>
              </div>
            </div>
            <button type="button" className="btn-secondary px-3" onClick={clearFile}>
              <Trash2 className="h-4 w-4" aria-hidden="true" />
              Remove file
            </button>
          </div>
        ) : null}

        {state.phase === "invalid" ? (
          <p className="mt-4 text-sm text-red-700" role="alert">
            {state.message}
          </p>
        ) : null}

        {state.phase === "uploading" ? (
          <div className="mt-4">
            <div
              className="h-2 overflow-hidden rounded-full bg-slate-100"
              role="progressbar"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={state.progress}
              aria-label="Upload progress"
            >
              <div className="h-full bg-indigo-600" style={{ width: `${state.progress}%` }} />
            </div>
            <p className="mt-2 text-sm text-slate-600" role="status">
              {state.progress >= 100 ? "Checking the file…" : `Uploading… ${state.progress}%`}
            </p>
          </div>
        ) : null}

        <div className="mt-5">
          <button type="button" className="btn-primary" onClick={() => void checkFile()} disabled={!canSubmit}>
            {state.phase === "uploading" ? "Checking…" : "Check CSV"}
          </button>
        </div>
      </section>

      {state.phase === "error" ? (
        <div className="card border-red-200 bg-red-50 p-5" role="alert">
          <h2 className="font-semibold text-red-950">The file was not accepted</h2>
          <p className="mt-2 text-sm text-red-900">{state.message}</p>
        </div>
      ) : null}

      {state.phase === "success" ? <UploadResult result={state.result} /> : null}
    </div>
  );
}

function UploadResult({ result }: { result: UploadResponse }) {
  return (
    <section className="card p-5" aria-live="polite">
      <h2 className="text-base font-semibold text-slate-900">Validation result</h2>
      <p className="mt-2 text-sm leading-6 text-slate-700">{result.validation_message}</p>
      <dl className="mt-4 grid gap-4 sm:grid-cols-3">
        <div>
          <dt className="text-xs font-medium text-slate-500">Filename</dt>
          <dd className="mt-1 text-sm font-medium text-slate-900">{result.filename}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium text-slate-500">Size</dt>
          <dd className="mt-1 text-sm font-medium text-slate-900">{formatBytes(result.size_bytes)}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium text-slate-500">Rows</dt>
          <dd className="mt-1 text-sm font-medium text-slate-900">{formatNumber(result.row_count)}</dd>
        </div>
      </dl>
      <div className="mt-4">
        <h3 className="text-sm font-medium text-slate-700">Columns found</h3>
        <ul className="mt-2 flex flex-wrap gap-2">
          {result.column_names.map((column) => (
            <li key={column} className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700">
              {column}
            </li>
          ))}
        </ul>
      </div>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <div>
          <h3 className="text-sm font-medium text-slate-700">Expected columns present</h3>
          <p className="mt-1 text-sm text-slate-600">
            {result.expected_columns.present.length > 0 ? result.expected_columns.present.join(", ") : "None"}
          </p>
        </div>
        <div>
          <h3 className="text-sm font-medium text-slate-700">Expected columns missing</h3>
          <p className="mt-1 text-sm text-slate-600">
            {result.expected_columns.missing.length > 0 ? result.expected_columns.missing.join(", ") : "None"}
          </p>
        </div>
      </div>
      {result.warnings.length > 0 ? (
        <div className="mt-4">
          <h3 className="text-sm font-medium text-slate-700">Warnings</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-600">
            {result.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      ) : null}
      <p className="mt-4 text-sm text-slate-600">
        Analysis performed: {result.analysis_performed ? "yes" : "no"}. File saved: {result.file_saved ? "yes" : "no"}.
        Source: {result.data_source}.
      </p>
    </section>
  );
}
