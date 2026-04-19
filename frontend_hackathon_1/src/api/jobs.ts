import { recordJobSubmission } from "./jobSubmissionLog";

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
  const id = Math.random().toString(36).slice(2, 10);

  recordJobSubmission(id, job);

  return {
    id,
    applicationLink: `${window.location.origin}/apply/${id}`,
  };
}
