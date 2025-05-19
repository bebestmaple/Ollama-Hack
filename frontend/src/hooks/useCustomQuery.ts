import {
  useQuery,
  UseQueryOptions,
  UseQueryResult,
} from "@tanstack/react-query";

import { ApiError } from "@/types";

type QueryFn<T> = () => Promise<T>;

export function useCustomQuery<T>(
  queryKey: readonly unknown[],
  queryFn: QueryFn<T>,
  options?: Omit<
    UseQueryOptions<T, ApiError, T, readonly unknown[]>,
    "queryKey" | "queryFn"
  >,
): UseQueryResult<T, ApiError> {
  return useQuery<T, ApiError, T>({
    queryKey,
    queryFn,
    ...options,
  });
}

export default useCustomQuery;
