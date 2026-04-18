// src/hooks/useCandidates.js
import { useQuery } from "@tanstack/react-query";
import { getJobs, getCandidates, getCandidate } from "../api/candidates";

export const candidateKeys = {
  jobs: ["dashboard-jobs"],
  candidates: (jobId) => ["candidates", jobId],
  candidate: (id) => ["candidate", id],
};

/** Fetch all jobs for the dashboard */
export function useDashboardJobs() {
  return useQuery({
    queryKey: candidateKeys.jobs,
    queryFn: getJobs,
  });
}

/** Fetch all candidates for a specific job */
export function useCandidates(jobId) {
  return useQuery({
    queryKey: candidateKeys.candidates(jobId),
    queryFn: () => getCandidates(jobId),
    enabled: !!jobId,
  });
}

/** Fetch a single candidate */
export function useCandidate(id) {
  return useQuery({
    queryKey: candidateKeys.candidate(id),
    queryFn: () => getCandidate(id),
    enabled: !!id,
  });
}