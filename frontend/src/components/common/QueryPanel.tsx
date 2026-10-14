import type { ReactNode } from "react";
import type { QueryResult } from "../../hooks/useApiQuery.ts";
import { EmptyState, ErrorState, LoadingState } from "./StateMessage.tsx";

interface QueryPanelProps<T> {
  query: QueryResult<T>;
  loadingLabel: string;
  emptyTitle: string;
  emptyBody: string;
  isEmpty?: (data: T) => boolean;
  children: (data: T) => ReactNode;
}

export function QueryPanel<T>({
  query,
  loadingLabel,
  emptyTitle,
  emptyBody,
  isEmpty,
  children,
}: QueryPanelProps<T>) {
  if (query.status === "loading") {
    return <LoadingState label={loadingLabel} />;
  }
  if (query.status === "error") {
    return <ErrorState message={query.error} onRetry={query.reload} />;
  }
  if (isEmpty?.(query.data)) {
    return <EmptyState title={emptyTitle} body={emptyBody} />;
  }
  return <>{children(query.data)}</>;
}
