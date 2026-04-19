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

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:5000";

export async function getJobInfo(jobId: string): Promise<JobInfo> {
  const response = await fetch(`${API_BASE_URL}/api/jobs/${jobId}`);
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
  const payloadForLog: Record<string, unknown> = { jobId };

  for (const [key, value] of formData.entries()) {
    if (value instanceof File) {
      payloadForLog[key] = {
        name: value.name,
        type: value.type,
        size: value.size,
      };
      continue;
    }

    payloadForLog[key] = value;
  }

  console.log("[Apply] Submission captured (local mode):", payloadForLog);

  return {
    success: true,
    message: "Logged locally",
  };
}
