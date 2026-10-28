import { ChartSkeleton } from "@/components/ui/skeleton";
import { EmptyState, type UnavailableLike } from "@/components/EmptyState";

interface Props<T> {
  loading: boolean;
  error: string | null;
  data: T | null | undefined;
  height?: number;
  /** Treat a payload with available:false as an empty state. */
  children: (data: T) => React.ReactNode;
}

interface MaybeAvailable {
  available?: boolean;
}

/**
 * One place where loading, transport failure and the API's structured
 * `available: false` contract are handled. Prevents a page from ever
 * rendering a chart with no data behind it.
 */
export function QueryBoundary<T>({
  loading,
  error,
  data,
  height = 280,
  children,
}: Props<T>) {
  if (loading) return <ChartSkeleton height={height} />;

  if (error) {
    return (
      <EmptyState
        title="Could not reach the API"
        message={`${error}. Start the backend with: python -m uvicorn app.main:app --reload --port 8000`}
      />
    );
  }

  if (!data) {
    return <EmptyState title="Research artifact unavailable" />;
  }

  const payload = data as MaybeAvailable;
  if (payload.available === false) {
    return <EmptyState payload={data as UnavailableLike} />;
  }

  return <>{children(data)}</>;
}
