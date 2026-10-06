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

/**
 * Organization-wide counts, independent of the current filters and page, so the
 * dashboard metric cards keep describing the whole organization while a recruiter
 * narrows or pages the queue.
 */
export type ScreeningSummary = {
  total_applicants: number;
  stage_counts: Record<string, number>;
  analysis_counts: Record<string, number>;
};

export type ScreeningQueue = {
  candidates: ScreeningCandidate[];
  page: number;
  pageSize: number;
  total: number;
  summary: ScreeningSummary;
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
  page?: number;
  pageSize?: number;
};

type ScreeningResponse = {
  success?: boolean;
  candidates?: ScreeningCandidate[];
  page?: unknown;
  page_size?: unknown;
  total?: unknown;
  summary?: {
    total_applicants?: unknown;
    stage_counts?: unknown;
    analysis_counts?: unknown;
  };
  error?: string;
};

export const DEFAULT_PAGE_SIZE = 10;
export const PAGE_SIZE_OPTIONS = [10, 25, 50, 100] as const;

function toCount(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) && value >= 0
    ? value
    : 0;
}

function toCounts(value: unknown): Record<string, number> {
  if (!value || typeof value !== "object") return {};
  return Object.fromEntries(
    Object.entries(value as Record<string, unknown>).map(([key, count]) => [
      key,
      toCount(count),
    ]),
  );
}

export async function getScreeningQueue(
  filters: ScreeningFilters = {},
): Promise<ScreeningQueue> {
  const params = new URLSearchParams();
  if (filters.stage) params.set("stage", filters.stage);
  if (filters.analysisStatus)
    params.set("analysis_status", filters.analysisStatus);
  if (filters.attention) params.set("attention", "1");
  if (filters.running) params.set("running", "1");
  if (filters.jobId !== undefined && filters.jobId !== "")
    params.set("job_id", String(filters.jobId));
  if (filters.q) params.set("q", filters.q);
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.pageSize ?? DEFAULT_PAGE_SIZE));

  const response = await recruiterFetch(
    `${API_BASE_URL}/api/candidates?${params.toString()}`,
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

  return {
    candidates: payload.candidates,
    page: toCount(payload.page) || 1,
    pageSize: toCount(payload.page_size) || DEFAULT_PAGE_SIZE,
    total: toCount(payload.total),
    summary: {
      total_applicants: toCount(payload.summary?.total_applicants),
      stage_counts: toCounts(payload.summary?.stage_counts),
      analysis_counts: toCounts(payload.summary?.analysis_counts),
    },
  };
}
