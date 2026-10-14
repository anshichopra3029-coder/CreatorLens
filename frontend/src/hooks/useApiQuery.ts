import { useCallback, useEffect, useRef, useState } from "react";

export type QueryResult<T> =
  | { status: "loading"; data: null; error: null; reload: () => void }
  | { status: "error"; data: null; error: string; reload: () => void }
  | { status: "success"; data: T; error: null; reload: () => void };

export function useApiQuery<T>(query: () => Promise<T>, reloadKey: string): QueryResult<T> {
  const queryRef = useRef(query);
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<Omit<QueryResult<T>, "reload">>({
    status: "loading",
    data: null,
    error: null,
  });

  useEffect(() => {
    queryRef.current = query;
  }, [query]);

  const reload = useCallback(() => {
    setAttempt((value) => value + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;
    setState({ status: "loading", data: null, error: null });
    queryRef.current()
      .then((data) => {
        if (!cancelled) {
          setState({ status: "success", data, error: null });
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          const message = error instanceof Error ? error.message : "The request failed.";
          setState({ status: "error", data: null, error: message });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [attempt, reloadKey]);

  return { ...state, reload } as QueryResult<T>;
}
