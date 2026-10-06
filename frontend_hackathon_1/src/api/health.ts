import { apiErrorMessage } from "./errors";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "";

export type AnalysisReadiness = {
  resume_provider_configured: boolean;
  resume_model: string;
};

/**
 * Public endpoint: reports only whether the server can run resume analysis.
 * It never carries a credential.
 */
export async function getAnalysisReadiness(): Promise<AnalysisReadiness> {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      apiErrorMessage(payload, "Could not read server readiness"),
    );
  }

  return {
    resume_provider_configured: Boolean(payload.resume_provider_configured),
    resume_model: typeof payload.resume_model === "string" ? payload.resume_model : "",
  };
}
