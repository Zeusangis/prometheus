import type { NewJobInput } from "./jobs";

type JobSubmissionRecord = {
  id: string;
  submittedAt: string;
  payload: NewJobInput;
};

const submissions: JobSubmissionRecord[] = [];

export function recordJobSubmission(id: string, payload: NewJobInput) {
  const entry: JobSubmissionRecord = {
    id,
    submittedAt: new Date().toISOString(),
    payload,
  };

  submissions.unshift(entry);

  // Keep recent history lightweight for local mock usage.
  if (submissions.length > 25) {
    submissions.length = 25;
  }

  return entry;
}

export function getLatestJobSubmission() {
  return submissions[0] ?? null;
}

export function getAllJobSubmissions() {
  return submissions;
}
