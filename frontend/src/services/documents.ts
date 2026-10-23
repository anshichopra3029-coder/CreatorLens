import { ApiError, apiBaseUrl } from "./api.ts";
import { applyXhrSession, noteUnauthorized, sessionHeaders } from "./session.ts";
import type { DocumentAnalysis, DocumentListResponse } from "../types/documents.ts";

function unavailableMessage(): string {
  return `CreatorLens can't reach its server${apiBaseUrl() ? ` at ${apiBaseUrl()}` : ""}. Start the backend and try again.`;
}

function detailMessage(payload: unknown, fallback: string): string {
  if (payload && typeof payload === "object" && "detail" in payload) {
    const detail = (payload as { detail: unknown }).detail;
    if (typeof detail === "string" && detail.trim() !== "") {
      return detail;
    }
  }
  return fallback;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl()}${path}`, {
      ...init,
      credentials: "include",
      headers: sessionHeaders(init?.method ?? "GET", init?.headers),
    });
  } catch {
    throw new ApiError(0, unavailableMessage());
  }
  const payload: unknown = await response.json().catch(() => null);
  if (response.status === 401) {
    noteUnauthorized();
  }
  if (!response.ok) {
    throw new ApiError(response.status, detailMessage(payload, `Something went wrong on the server (${response.status}). Please try again.`));
  }
  return payload as T;
}

export function listDocuments(): Promise<DocumentListResponse> {
  return request<DocumentListResponse>("/api/documents");
}

export function getDocument(id: string): Promise<DocumentAnalysis> {
  return request<DocumentAnalysis>(`/api/documents/${id}`);
}

export function askDocument(id: string, question: string): Promise<DocumentAnalysis> {
  return request<DocumentAnalysis>(`/api/documents/${id}/questions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
}

export function uploadDocument(file: File, onProgress: (percent: number) => void): Promise<DocumentAnalysis> {
  return new Promise((resolve, reject) => {
    const requestBody = new XMLHttpRequest();
    requestBody.open("POST", `${apiBaseUrl()}/api/documents`);
    requestBody.setRequestHeader("Accept", "application/json");
    applyXhrSession(requestBody);
    requestBody.upload.onprogress = (event) => {
      if (event.lengthComputable && event.total > 0) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };
    requestBody.onerror = () => {
      reject(new ApiError(0, unavailableMessage()));
    };
    requestBody.onload = () => {
      let payload: unknown = null;
      if (requestBody.responseText) {
        try {
          payload = JSON.parse(requestBody.responseText) as unknown;
        } catch {
          reject(new ApiError(requestBody.status, "The server sent back an answer we couldn't read. Please try again."));
          return;
        }
      }
      if (requestBody.status === 401) {
        noteUnauthorized();
      }
      if (requestBody.status >= 200 && requestBody.status < 300) {
        resolve(payload as DocumentAnalysis);
        return;
      }
      reject(new ApiError(requestBody.status, detailMessage(payload, `The upload didn't work (${requestBody.status}). Please try again.`)));
    };
    const form = new FormData();
    form.append("file", file);
    requestBody.send(form);
  });
}
