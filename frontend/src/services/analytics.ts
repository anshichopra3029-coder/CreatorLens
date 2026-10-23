import { ApiError, apiBaseUrl } from "./api.ts";
import { noteUnauthorized, sessionHeaders } from "./session.ts";
import type { AnalyticsAnalysis, AnalyticsListResponse, AnalyticsPreview } from "../types/analytics.ts";

function unavailableMessage(): string {
  return `We can't reach the CreatorLens server${apiBaseUrl() ? ` at ${apiBaseUrl()}` : ""} right now. Make sure the backend is running, then try again.`;
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

async function upload<T>(path: string, file: File): Promise<T> {
  const form = new FormData();
  form.append("file", file);
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl()}${path}`, {
      method: "POST",
      credentials: "include",
      headers: sessionHeaders("POST"),
      body: form,
    });
  } catch {
    throw new ApiError(0, unavailableMessage());
  }
  const payload: unknown = await response.json().catch(() => null);
  if (response.status === 401) {
    noteUnauthorized();
  }
  if (!response.ok) {
    throw new ApiError(response.status, detailMessage(payload, `The upload didn't work (${response.status}). Please try again.`));
  }
  return payload as T;
}

async function request<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl()}${path}`, {
      credentials: "include",
      headers: sessionHeaders("GET"),
    });
  } catch {
    throw new ApiError(0, unavailableMessage());
  }
  const payload: unknown = await response.json().catch(() => null);
  if (response.status === 401) {
    noteUnauthorized();
  }
  if (!response.ok) {
    throw new ApiError(response.status, detailMessage(payload, `Something went wrong (${response.status}). Please try again.`));
  }
  return payload as T;
}

export function previewAnalytics(file: File): Promise<AnalyticsPreview> {
  return upload<AnalyticsPreview>("/api/analytics/preview", file);
}

export function analyzeAnalytics(file: File): Promise<AnalyticsAnalysis> {
  return upload<AnalyticsAnalysis>("/api/analytics/analyses", file);
}

export function listAnalytics(): Promise<AnalyticsListResponse> {
  return request<AnalyticsListResponse>("/api/analytics/analyses");
}

export function getAnalytics(id: string): Promise<AnalyticsAnalysis> {
  return request<AnalyticsAnalysis>(`/api/analytics/analyses/${id}`);
}
