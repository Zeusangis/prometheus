type JobInfo = {
  id: string;
  title: string;
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

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:5000";

function normalizeJobId(rawJobId: string) {
  return rawJobId.startsWith("job_") ? rawJobId.slice(4) : rawJobId;
}

export async function getJobInfo(jobId: string): Promise<JobInfo> {
  const normalizedJobId = normalizeJobId(jobId);
  const response = await fetch(`${API_BASE_URL}/api/jobs/${normalizedJobId}`);
  const payload = (await response.json().catch(() => ({}))) as JobDetailPayload;

  if (!response.ok) {
    throw new Error(payload.error || "Failed to load job details");
  }

  return {
    id: String(payload.job?.id ?? jobId),
    title: payload.job?.title || "Job Application",
    type: payload.job?.jobType || "Role",
    description: payload.job?.description || "",
  };
}

export async function submitApplication(
  jobId: string,
  formData: FormData,
): Promise<ApplyResponse> {
  const normalizedJobId = normalizeJobId(jobId);
  const response = await fetch(
    `${API_BASE_URL}/api/jobs/${normalizedJobId}/apply`,
    {
      method: "POST",
      body: formData,
    },
  );

  const payload = (await response.json().catch(() => ({}))) as ApplyApiResponse;

  if (!response.ok) {
    throw new Error(payload.error || "Failed to submit application");
  }

  return {
    success: payload.success ?? true,
    message: payload.message,
  };
}
