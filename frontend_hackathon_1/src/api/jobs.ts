import { recordJobSubmission } from "./jobSubmissionLog";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:5000";

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

export type CompanyJob = {
  id: string;
  title: string;
  description: string;
  jobType: string;
  languages: string[];
  frameworks: string[];
  location: string | null;
  posted_date: string;
  status: "open" | "closed" | "draft";
  total_applicants: number;
  company: string;
};

type CompanyJobsResponse = {
  success: boolean;
  jobs: CompanyJob[];
};

export type JobDetail = {
  id: number;
  title: string;
  description: string;
  jobType: string;
  status: "open" | "closed" | "draft";
  location: string | null;
  company: string;
  posted_date: string;
  languages: string[];
  frameworks: string[];
  interviewTone?: string;
  interviewLength?: number;
};

export type JobApplicant = {
  id: number;
  job_id: number;
  full_name: string;
  email: string;
  github_username: string | null;
  filename: string | null;
  raw_text: string | null;
  status: string;
  uploaded_at: string;
};

type JobDetailResponse = {
  success: boolean;
  job: JobDetail;
};

type JobApplicantsResponse = {
  success: boolean;
  applicants: JobApplicant[];
};

type MoveCandidateNextStepResponse = {
  success: boolean;
  candidateId: number;
  jobId: number;
  status: string;
  meeting_id: string | null;
};

type TotalJobsResponse = {
  success: boolean;
  total_jobs: number;
};

export function normalizeJobId(rawJobId: string) {
  return rawJobId.startsWith("job_") ? rawJobId.slice(4) : rawJobId;
}

export async function moveCandidateToNextStep(params: {
  jobId: string;
  candidateId: number;
  nextStatus: string;
}): Promise<MoveCandidateNextStepResponse> {
  const normalizedJobId = normalizeJobId(params.jobId);
  const parsedJobId = Number(normalizedJobId);

  if (!Number.isInteger(parsedJobId)) {
    throw new Error("Invalid job id");
  }

  const response = await fetch(
    `${API_BASE_URL}/api/jobs/${parsedJobId}/candidates/${params.candidateId}/next-step`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ next_status: params.nextStatus }),
    },
  );

  const payload = (await response
    .json()
    .catch(() => ({}))) as Partial<MoveCandidateNextStepResponse> & {
    error?: string;
  };

  if (!response.ok) {
    throw new Error(payload.error || "Failed to move candidate to next step");
  }

  if (!payload.success) {
    throw new Error("Invalid response while moving candidate to next step");
  }

  return {
    success: true,
    candidateId: payload.candidateId ?? params.candidateId,
    jobId: payload.jobId ?? parsedJobId,
    status: payload.status ?? params.nextStatus,
    meeting_id: payload.meeting_id ?? null,
  };
}

export async function getJobById(jobId: string): Promise<JobDetail> {
  const normalizedJobId = normalizeJobId(jobId);
  const response = await fetch(`${API_BASE_URL}/api/jobs/${normalizedJobId}`);
  const payload = (await response
    .json()
    .catch(() => ({}))) as Partial<JobDetailResponse> & {
    error?: string;
  };

  if (!response.ok) {
    throw new Error(payload.error || "Failed to fetch job details");
  }

  if (!payload.job) {
    throw new Error("Invalid response while fetching job details");
  }

  return payload.job;
}

export async function getJobApplicants(jobId: string): Promise<JobApplicant[]> {
  const normalizedJobId = normalizeJobId(jobId);
  const response = await fetch(
    `${API_BASE_URL}/api/jobs/${normalizedJobId}/applicants`,
  );
  const payload = (await response
    .json()
    .catch(() => ({}))) as Partial<JobApplicantsResponse> & {
    error?: string;
  };

  if (!response.ok) {
    throw new Error(payload.error || "Failed to fetch applicants");
  }

  return payload.applicants ?? [];
}

export async function getCompanyJobs(): Promise<CompanyJob[]> {
  const response = await fetch(`${API_BASE_URL}/api/jobs/my-company`);
  const payload = (await response
    .json()
    .catch(() => ({}))) as Partial<CompanyJobsResponse> & {
    error?: string;
  };

  if (!response.ok) {
    throw new Error(payload.error || "Failed to fetch jobs");
  }

  return payload.jobs ?? [];
}

export async function getTotalJobs(): Promise<number> {
  const endpoints = ["/api/jobs/total", "/api/jobs/count"];

  for (const endpoint of endpoints) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    const payload = (await response
      .json()
      .catch(() => ({}))) as Partial<TotalJobsResponse> & {
      error?: string;
    };

    if (!response.ok) {
      if (response.status === 404) {
        continue;
      }

      throw new Error(payload.error || "Failed to fetch total jobs count");
    }

    return payload.total_jobs ?? 0;
  }

  throw new Error("Jobs count endpoint not found");
}

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
