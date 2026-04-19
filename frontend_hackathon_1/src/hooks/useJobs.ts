import { useMutation } from "@tanstack/react-query";
import { createJob } from "../api/jobs";
import type { NewJobInput, CreatedJob } from "../api/jobs";

export function useCreateJob() {
  return useMutation<CreatedJob, Error, NewJobInput>({
    mutationFn: createJob,
  });
}
