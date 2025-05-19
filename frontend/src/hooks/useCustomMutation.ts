import {
  useMutation,
  UseMutationOptions,
  UseMutationResult,
} from "@tanstack/react-query";

import { ApiError } from "@/types";

type MutationFn<TVariables, TData> = (variables: TVariables) => Promise<TData>;

export function useCustomMutation<TData, TVariables = void>(
  mutationFn: MutationFn<TVariables, TData>,
  options?: Omit<
    UseMutationOptions<TData, ApiError, TVariables, unknown>,
    "mutationFn"
  >,
): UseMutationResult<TData, ApiError, TVariables, unknown> {
  return useMutation<TData, ApiError, TVariables, unknown>({
    mutationFn,
    ...options,
  });
}

export default useCustomMutation;
