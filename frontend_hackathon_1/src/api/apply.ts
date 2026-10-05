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

type CandidateProfile = {
  id: number;
  full_name?: string;
  name?: string;
  email?: string;
  github_username?: string;
  status?: string;
  filename?: string;
  job_id?: number;
  uploaded_at?: string;
  [key: string]: any;
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

  if (!response.ok) {
    throw new Error("Failed to load candidate profile");
  }

  const payload = (await response
    .json()
    .catch(() => ({}))) as CandidateApiResponse;

  if (!payload.candidate) {
    throw new Error("Invalid candidate data");
  }

  return payload.candidate;
}
