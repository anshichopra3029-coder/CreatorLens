const STORAGE_KEY = "creatorlens.activeDocumentId";
const EVENT_NAME = "creatorlens-document";

export function getActiveDocumentId(): string | null {
  const value = localStorage.getItem(STORAGE_KEY);
  return value && value.trim() !== "" ? value : null;
}

export function setActiveDocumentId(id: string): void {
  localStorage.setItem(STORAGE_KEY, id);
  window.dispatchEvent(new Event(EVENT_NAME));
}

export function clearActiveDocumentId(): void {
  localStorage.removeItem(STORAGE_KEY);
  window.dispatchEvent(new Event(EVENT_NAME));
}

export const activeDocumentEvent = EVENT_NAME;
