import { apiErrorMessage } from "./errors";
import { recruiterFetch } from "./auth";

type JobInfo = {
  id: string;
  title: string;
  company: string;
  location: string | null;
  type: string;
  description: string;
};

type ApplyResponse = {
  success: boolean;
  message?: string;
};

type JobDetailPayload = {
  success?: boolean;
  job?: {
    id: number | string;
    title?: string;
    company?: string;
    location?: string | null;
    jobType?: string;
    description?: string;
  };
  error?: string;
};

type ApplyApiResponse = {
  success?: boolean;
  message?: string;
  error?: string;
};

export type CandidateProfile = {
  id: number;
  full_name: string;
  email: string;
  github_username: string | null;
  status: string;
  analysis_status: string;
  analysis_error: string | null;
  ats_score: number | null;
  allowed_actions: string[];
  filename: string;
  job_id: number | null;
  uploaded_at: string | null;
};

export type ComponentStatus = "pending" | "running" | "complete" | "partial" | "failed";
export type ResumeAnalysis = {
  status: ComponentStatus;
  ats_score: number | null;
  breakdown: Record<string, number> | null;
  final_verdict: string | null;
  missing_keywords: string[] | null;
  weak_areas: string[] | null;
  top_improvements: string[] | null;
  projects: string[] | null;
  model_name: string | null;
  error_message: string | null;
  updated_at: string | null;
};
export type EvidenceDimension = {
  score: number | null;
  reasoning: string;
  evidence_paths: string[];
};
export type RepositoryAnalysis = {
  repo_name: string;
  repo_url: string;
  primary_language: string | null;
  pushed_at: string | null;
  score: number | null;
  metrics: {
    dimensions?: Record<string, EvidenceDimension>;
    aggregation?: { weight_coverage: number | null; available_weight: number; enabled_weight: number };
    languages?: Record<string, number>;
    stars?: number;
    fork?: boolean;
  } | null;
  strengths: string[] | null;
  red_flags: string[] | null;
  recruiter_summary: string | null;
  evidence_metadata: {
    source?: string;
    tree_sha?: string;
    tree_truncated?: boolean;
    files?: { path: string; sha: string; size: number; truncated: boolean }[];
    commits?: { sha: string; date: string; url: string }[];
    commit_sample_truncated?: boolean;
    commit_scope?: string;
    authorship_caveat?: string;
    model_name?: string | null;
    review_error?: string | null;
  } | null;
};
export type GitHubAnalysis = {
  status: ComponentStatus;
  username: string;
  total_public_repos: number | null;
  total_stars: number | null;
  candidate_attributed_commits: number | null;
  error_message: string | null;
  updated_at: string | null;
  repositories: RepositoryAnalysis[];
  summary: {
    collected_at?: string;
    listed_repos?: number;
    analyzed_repos?: number;
    repository_listing_truncated?: boolean;
    repository_analysis_sampled?: boolean;
    sample_stars?: number;
    sample_mean_score?: number | null;
    scored_repositories?: number;
    commit_scope?: string;
    score_scope?: string;
    unsupported_metrics?: string[];
    errors?: { repo_name: string; message: string }[];
    /** Repositories whose qualitative AI review failed while evidence was still saved. */
    review_failures?: { repo_name: string; message: string }[];
  } | null;
};
export type CandidateAnalysis = {
  status: string;
  error_message: string | null;
  /** Text extracted from the stored PDF; used for analysis and visible for review. */
  resume_text: string | null;
  resume: ResumeAnalysis | null;
  github: GitHubAnalysis | null;
};

type CandidateApiResponse = {
  success?: boolean;
  candidate?: CandidateProfile;
  error?: string;
};

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ||
  "";

function normalizeJobId(rawJobId: string) {
  return rawJobId.startsWith("job_") ? rawJobId.slice(4) : rawJobId;
}

export async function getJobInfo(jobId: string): Promise<JobInfo> {
  const normalizedJobId = normalizeJobId(jobId);
  const response = await fetch(`${API_BASE_URL}/api/public/jobs/${normalizedJobId}`);
  const payload = (await response.json().catch(() => ({}))) as JobDetailPayload;

  if (!response.ok) {
    throw new Error(apiErrorMessage(payload, "Failed to load job details"));
  }

  if (!payload.job?.title) throw new Error("Invalid public job data");
  return {
    id: String(payload.job.id),
    title: payload.job.title,
    company: payload.job.company || "Company not specified",
    location: payload.job.location ?? null,
    type: payload.job.jobType || "Job type not specified",
    description: payload.job.description || "",
  };
}

export async function submitApplication(
  jobId: string,
  formData: FormData,
): Promise<ApplyResponse> {
  const normalizedJobId = normalizeJobId(jobId);
  const response = await fetch(
    `${API_BASE_URL}/api/public/jobs/${normalizedJobId}/apply`,
    {
      method: "POST",
      body: formData,
    },
  );

  const payload = (await response.json().catch(() => ({}))) as ApplyApiResponse;

  if (!response.ok) {
    throw new Error(apiErrorMessage(payload, "Failed to submit application"));
  }

  return {
    success: payload.success ?? true,
    message: payload.message,
  };
}

export async function getCandidateProfile(
  candidateId: number | string,
): Promise<CandidateProfile> {
  const response = await recruiterFetch(`${API_BASE_URL}/api/candidates/${candidateId}`);

  const payload = (await response
    .json()
    .catch(() => ({}))) as CandidateApiResponse;

  if (!response.ok) {
    throw new Error(apiErrorMessage(payload, "Failed to load candidate profile"));
  }

  if (!payload.candidate) {
    throw new Error("Invalid candidate data");
  }

  return payload.candidate;
}

export async function getCandidateAnalysis(candidateId: number | string): Promise<CandidateAnalysis> {
  const response = await recruiterFetch(`${API_BASE_URL}/api/candidates/${candidateId}/analysis`);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(apiErrorMessage(payload, "Failed to load candidate analysis"));
  if (typeof payload.status !== "string" || !("resume" in payload) || !("github" in payload)) {
    throw new Error("Invalid candidate analysis data");
  }
  return payload as CandidateAnalysis;
}

export async function retryCandidateAnalysis(candidateId: number | string): Promise<void> {
  const response = await recruiterFetch(`${API_BASE_URL}/api/candidates/${candidateId}/analysis/retry`, { method: "POST" });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(apiErrorMessage(payload, "Analysis could not be queued. Refresh the saved status and retry later."));
}
