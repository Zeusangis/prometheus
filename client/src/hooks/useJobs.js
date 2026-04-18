// src/hooks/useJobs.js
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createJob, getJobs, getJob } from "../api/jobs";

export const jobKeys = {
  all: ["jobs"],
  detail: (id) => ["jobs", id],
};

export function useJobs() {
  return useQuery({
    queryKey: jobKeys.all,
    queryFn: getJobs,
  });
}

export function useJob(id) {
  return useQuery({
    queryKey: jobKeys.detail(id),
    queryFn: () => getJob(id),
    enabled: !!id,
  });
}

export function useCreateJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createJob,
    onSuccess: (newJob) => {
      queryClient.invalidateQueries({ queryKey: jobKeys.all });
      queryClient.setQueryData(jobKeys.detail(newJob.id), newJob);
    },
  });
}