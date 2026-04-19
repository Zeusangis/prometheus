import { recordJobSubmission } from "./jobSubmissionLog";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ||
  "http://localhost:5000";

export type MetricConfig = {
  enabled: boolean;
  weight: number;
};

export type NewJobInput = {
  title: string;
  jobType: string;
  description: string;
  languages: string[];
  frameworks: string[];
  scraperMetrics: Record<string, MetricConfig>;
  scraperInstructions: string;
  interviewTone: string;
  interviewFocus: string[];
  customQuestions: string[];
  interviewLength: number;
  interviewInstructions: string;
};

export type CreatedJob = {
  id: string;
  applicationLink: string;
};

export async function createJob(job: NewJobInput): Promise<CreatedJob> {
  const response = await fetch(`${API_BASE_URL}/api/jobs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      job,
      status: "open",
    }),
  });

  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message =
      (payload as { error?: string })?.error || "Failed to create job";
    throw new Error(message);
  }

  const createdJob = payload as Partial<CreatedJob>;
  const id = createdJob.id;
  const applicationLink = createdJob.applicationLink;

  if (!id || !applicationLink) {
    throw new Error("Invalid response from server while creating job");
  }

  recordJobSubmission(id, job);

  return {
    id,
    applicationLink,
  };
}
