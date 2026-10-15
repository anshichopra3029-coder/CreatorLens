import { ApiError, apiBaseUrl } from "./api.ts";
import type { OauthStatus, YoutubeAnalysis, YoutubeListResponse, YoutubePreview } from "../types/youtube.ts";

function unavailableMessage(): string {
  return `The API is unavailable at ${apiBaseUrl()}. Start the backend and try again.`;
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
      headers: {
        Accept: "application/json",
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...(init?.headers ?? {}),
      },
    });
  } catch {
    throw new ApiError(0, unavailableMessage());
  }
  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(response.status, detailMessage(payload, `Request failed (${response.status}).`));
  }
  return payload as T;
}

export function previewYoutube(url: string): Promise<YoutubePreview> {
  return request<YoutubePreview>("/api/youtube/preview", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

export function analyzeYoutube(url: string): Promise<YoutubeAnalysis> {
  return request<YoutubeAnalysis>("/api/youtube/analyses", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

export function listYoutubeAnalyses(): Promise<YoutubeListResponse> {
  return request<YoutubeListResponse>("/api/youtube/analyses");
}

export function getYoutubeAnalysis(id: string): Promise<YoutubeAnalysis> {
  return request<YoutubeAnalysis>(`/api/youtube/analyses/${id}`);
}

export function getYoutubeOauthStatus(): Promise<OauthStatus> {
  return request<OauthStatus>("/api/youtube/oauth/status");
}
