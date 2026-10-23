import { applyXhrSession, noteUnauthorized } from "./session.ts";
import type {
  ContentComparisonResponse,
  DashboardSummary,
  DemoFilters,
  HealthResponse,
  InsightsResponse,
  PostsResponse,
  TrendsResponse,
  UploadResponse,
} from "../types/api.ts";

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function apiBaseUrl(): string {
  const configured = import.meta.env.VITE_API_BASE_URL;
  if (typeof configured === "string" && configured.trim() !== "") {
    return configured.trim().replace(/\/$/, "");
  }
  return "";
}

function unavailableMessage(): string {
  const base = apiBaseUrl();
  if (base === "") {
    return "CreatorLens can't reach its server right now. If you run it yourself, start the backend on port 8000 and try again.";
  }
  return `CreatorLens can't reach its server at ${base}. Start the backend and try again.`;
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

function withFilters(path: string, filters?: DemoFilters): string {
  const search = new URLSearchParams();
  if (filters?.category) {
    search.set("category", filters.category);
  }
  if (filters?.platform) {
    search.set("platform", filters.platform);
  }
  if (filters?.startDate) {
    search.set("start_date", filters.startDate);
  }
  if (filters?.endDate) {
    search.set("end_date", filters.endDate);
  }
  const query = search.toString();
  return query ? `${path}?${query}` : path;
}

async function request<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl()}${path}`, {
      credentials: "include",
      headers: { Accept: "application/json" },
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

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/api/health");
}

export function getDashboardSummary(filters?: DemoFilters): Promise<DashboardSummary> {
  return request<DashboardSummary>(withFilters("/api/dashboard/summary", filters));
}

export function getTrends(filters?: DemoFilters): Promise<TrendsResponse> {
  return request<TrendsResponse>(withFilters("/api/dashboard/trends", filters));
}

export function getContentComparison(filters?: DemoFilters): Promise<ContentComparisonResponse> {
  return request<ContentComparisonResponse>(withFilters("/api/dashboard/content-comparison", filters));
}

export function getPosts(filters?: DemoFilters): Promise<PostsResponse> {
  return request<PostsResponse>(withFilters("/api/posts", filters));
}

export function getInsights(): Promise<InsightsResponse> {
  return request<InsightsResponse>("/api/insights");
}

export function uploadCsv(file: File, onProgress: (percent: number) => void): Promise<UploadResponse> {
  return new Promise((resolve, reject) => {
    const requestBody = new XMLHttpRequest();
    requestBody.open("POST", `${apiBaseUrl()}/api/upload`);
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
      if (requestBody.status >= 200 && requestBody.status < 300) {
        resolve(payload as UploadResponse);
        return;
      }
      reject(
        new ApiError(
          requestBody.status,
          detailMessage(payload, `The upload didn't work (${requestBody.status}). Please try again.`),
        ),
      );
    };
    const form = new FormData();
    form.append("file", file);
    requestBody.send(form);
  });
}
