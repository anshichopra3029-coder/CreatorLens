import { ApiError, apiBaseUrl } from "./api.ts";
import { noteUnauthorized, sessionHeaders } from "./session.ts";
import type {
  EngagementModelInfo,
  EngagementModelList,
  EngagementPrediction,
  PredictionInput,
  TrainingDatasetList,
} from "../types/engagement.ts";

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
    throw new ApiError(
      0,
      `We can't reach the CreatorLens server${apiBaseUrl() ? ` at ${apiBaseUrl()}` : ""} right now. Make sure the backend is running, then try again.`,
    );
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

function post<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function listTrainingDatasets(): Promise<TrainingDatasetList> {
  return request<TrainingDatasetList>("/api/predictions/datasets");
}

export function listEngagementModels(): Promise<EngagementModelList> {
  return request<EngagementModelList>("/api/predictions/models");
}

export function trainFromDocument(documentId: string): Promise<EngagementModelInfo> {
  return post<EngagementModelInfo>("/api/predictions/train", { source: "document", document_id: documentId });
}

export function trainFromDemo(): Promise<EngagementModelInfo> {
  return post<EngagementModelInfo>("/api/predictions/train", { source: "demo" });
}

export function predictEngagement(modelId: string, input: PredictionInput): Promise<EngagementPrediction> {
  return post<EngagementPrediction>(`/api/predictions/models/${encodeURIComponent(modelId)}/predict`, input);
}
