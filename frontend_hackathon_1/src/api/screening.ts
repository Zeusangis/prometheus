import { apiErrorMessage } from "./errors";
import { recruiterFetch } from "./auth";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "";

export type ScreeningCandidate = {
  id: number;
  full_name: string;
  email: string;
  github_username: string | null;
  filename: string;
  status: string;
  analysis_status: string;
  analysis_error: string | null;
  ats_score: number | null;
  allowed_actions: string[];
  uploaded_at: string;
  job_id: number | null;
  job_title: string;
};

export type ScreeningFilters = {
  stage?: string;
  analysisStatus?: string;
  /** Only applicants whose analysis can be retried (failed, enqueue_failed, partial). */
  attention?: boolean;
  /** Only analysis work that is still queued or running. */
  running?: boolean;
  jobId?: string | number;
  q?: string;
};

type ScreeningResponse = {
  success?: boolean;
  candidates?: ScreeningCandidate[];
  error?: string;
};

export async function getScreeningQueue(
  filters: ScreeningFilters = {},
): Promise<ScreeningCandidate[]> {
  const params = new URLSearchParams();
  if (filters.stage) params.set("stage", filters.stage);
  if (filters.analysisStatus)
    params.set("analysis_status", filters.analysisStatus);
  if (filters.attention) params.set("attention", "1");
  if (filters.running) params.set("running", "1");
  if (filters.jobId !== undefined && filters.jobId !== "")
    params.set("job_id", String(filters.jobId));
  if (filters.q) params.set("q", filters.q);

  const query = params.toString();
  const response = await recruiterFetch(
    `${API_BASE_URL}/api/candidates${query ? `?${query}` : ""}`,
  );
  const payload = (await response
    .json()
    .catch(() => ({}))) as ScreeningResponse;

  if (!response.ok) {
    throw new Error(
      apiErrorMessage(payload, "Failed to load the screening queue"),
    );
  }

  if (!Array.isArray(payload.candidates)) {
    throw new Error("Invalid screening queue data");
  }

  return payload.candidates;
}
