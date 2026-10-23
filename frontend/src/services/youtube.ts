import { ApiError, apiBaseUrl } from "./api.ts";
import { noteUnauthorized, sessionHeaders } from "./session.ts";
import type { ObservationImportResult, TrackedVideoList, VideoForecastResponse } from "../types/prediction.ts";
import type { RoastStyle } from "../types/roast.ts";
import type { OauthStatus, YoutubeAnalysis, YoutubeListResponse, YoutubePreview } from "../types/youtube.ts";

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
      headers: sessionHeaders(init?.method ?? "GET", {
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...(init?.headers ?? {}),
      }),
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

export function refreshYoutube(id: string): Promise<YoutubeAnalysis> {
  return request<YoutubeAnalysis>(`/api/youtube/analyses/${id}/refresh`, { method: "POST" });
}

export function roastYoutube(id: string, style: RoastStyle, force = false): Promise<YoutubeAnalysis> {
  return request<YoutubeAnalysis>(`/api/youtube/analyses/${id}/roast`, {
    method: "POST",
    body: JSON.stringify({ style, force }),
  });
}

export function challengeYoutubeRoast(
  id: string,
  style: RoastStyle,
  question: string,
  context: string,
): Promise<YoutubeAnalysis> {
  return request<YoutubeAnalysis>(`/api/youtube/analyses/${id}/roast/challenge`, {
    method: "POST",
    body: JSON.stringify({ style, question, context }),
  });
}

export function fixYoutubeRoast(id: string, style: RoastStyle): Promise<YoutubeAnalysis> {
  return request<YoutubeAnalysis>(`/api/youtube/analyses/${id}/roast/fix`, {
    method: "POST",
    body: JSON.stringify({ style, force: false }),
  });
}

export function saveYoutubeExperiment(id: string, style: RoastStyle): Promise<YoutubeAnalysis> {
  return request<YoutubeAnalysis>(`/api/youtube/analyses/${id}/experiment`, {
    method: "POST",
    body: JSON.stringify({ style, force: false }),
  });
}

export function updateYoutubeExperiment(
  id: string,
  body: { outcome_note: string; follow_up_views: number | null; completed_task: boolean },
): Promise<YoutubeAnalysis> {
  return request<YoutubeAnalysis>(`/api/youtube/analyses/${id}/experiment/result`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getYoutubeOauthStatus(): Promise<OauthStatus> {
  return request<OauthStatus>("/api/youtube/oauth/status");
}

export function listTrackedVideos(): Promise<TrackedVideoList> {
  return request<TrackedVideoList>("/api/youtube/videos");
}

export function getVideoForecast(videoId: string): Promise<VideoForecastResponse> {
  return request<VideoForecastResponse>(`/api/youtube/videos/${encodeURIComponent(videoId)}/forecast`);
}

export function recordVideoSnapshot(videoId: string): Promise<VideoForecastResponse> {
  return request<VideoForecastResponse>(`/api/youtube/videos/${encodeURIComponent(videoId)}/snapshot`, { method: "POST" });
}

export async function importVideoHistory(videoId: string, file: File): Promise<ObservationImportResult> {
  const form = new FormData();
  form.append("file", file);
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl()}/api/youtube/videos/${encodeURIComponent(videoId)}/observations`, {
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
    throw new ApiError(response.status, detailMessage(payload, `The import didn't work (${response.status}). Please try again.`));
  }
  return payload as ObservationImportResult;
}
