let csrfToken = "";
const sessionLostListeners = new Set<() => void>();

export function onSessionLost(listener: () => void): () => void {
  sessionLostListeners.add(listener);
  return () => {
    sessionLostListeners.delete(listener);
  };
}

export function noteUnauthorized(): void {
  csrfToken = "";
  sessionLostListeners.forEach((listener) => listener());
}

export function rememberCsrf(token: string): void {
  csrfToken = token;
}

export function clearCsrf(): void {
  csrfToken = "";
}

export function sessionHeaders(method: string, headers?: HeadersInit): Headers {
  const next = new Headers(headers);
  if (!next.has("Accept")) {
    next.set("Accept", "application/json");
  }
  const verb = method.toUpperCase();
  if (csrfToken !== "" && verb !== "GET" && verb !== "HEAD" && verb !== "OPTIONS") {
    next.set("X-CSRF-Token", csrfToken);
  }
  return next;
}

export function applyXhrSession(request: XMLHttpRequest): void {
  request.withCredentials = true;
  if (csrfToken !== "") {
    request.setRequestHeader("X-CSRF-Token", csrfToken);
  }
}
