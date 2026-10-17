import type { ProfileResponse, PublicUser, SessionResponse } from "../types/account.ts";
import { ApiError, apiBaseUrl } from "./api.ts";
import { clearCsrf, noteUnauthorized, rememberCsrf, sessionHeaders } from "./session.ts";

function unavailableMessage(): string {
  return "The API is unavailable. Start the backend so this app can reach /api.";
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
  if (response.status === 204) {
    return undefined as T;
  }
  const payload: unknown = await response.json().catch(() => null);
  if (response.status === 401) {
    noteUnauthorized();
  }
  if (!response.ok) {
    throw new ApiError(response.status, detailMessage(payload, `Request failed (${response.status}).`));
  }
  return payload as T;
}

function remember(session: SessionResponse): SessionResponse {
  rememberCsrf(session.csrf_token);
  return session;
}

export function getSession(): Promise<SessionResponse> {
  return request<SessionResponse>("/api/auth/session").then(remember);
}

export function registerAccount(name: string, email: string, password: string): Promise<void> {
  return request("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ name, email, password }),
  });
}

export function loginAccount(email: string, password: string): Promise<SessionResponse> {
  return request<SessionResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  }).then(remember);
}

export function logoutAccount(): Promise<void> {
  return request<void>("/api/auth/logout", { method: "POST" }).finally(() => {
    clearCsrf();
  });
}

export function resendVerification(email: string): Promise<void> {
  return request("/api/auth/resend", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function verifyEmail(token: string): Promise<void> {
  return request("/api/auth/verify", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
}

export function forgotPassword(email: string): Promise<void> {
  return request("/api/auth/forgot", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function resetPassword(token: string, password: string): Promise<void> {
  return request("/api/auth/reset", {
    method: "POST",
    body: JSON.stringify({ token, password }),
  });
}

export function getProfile(): Promise<ProfileResponse> {
  return request<ProfileResponse>("/api/account");
}

export function updateDisplayName(displayName: string): Promise<PublicUser> {
  return request<PublicUser>("/api/account", {
    method: "PATCH",
    body: JSON.stringify({ display_name: displayName }),
  });
}
