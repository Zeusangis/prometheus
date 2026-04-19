// src/api/jobs.js
const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

async function safeJson(res) {
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return { error: text };
  }
}

function errorMessage(defaultMessage, body) {
  if (body && typeof body.error === "string" && body.error) return body.error;
  return defaultMessage;
}

/**
 * Orchestrates three sequential/parallel calls to create a job:
 *   1. POST /api/jobs           → job details (returns jobId)
 *   2. POST /api/jobs/:id/scraper    → GitHub scraper config
 *   3. POST /api/jobs/:id/interview  → AI interview config
 */
export async function createJob(jobData) {
  const {
    title,
    jobType,
    description,
    languages,
    frameworks,
    company,
    status,
    scraperMetrics,
    scraperInstructions,
    interviewTone,
    interviewFocus,
    customQuestions,
    interviewLength,
    interviewInstructions,
  } = jobData;

  const payload = {
    job: {
      title,
      jobType,
      description,
      languages,
      frameworks,
      ...(company ? { company } : {}),
    },
    scraper: {
      scraperMetrics,
      scraperInstructions,
    },
    interview: {
      interviewTone,
      interviewFocus,
      customQuestions,
      interviewLength,
      interviewInstructions,
    },
    ...(status ? { status } : {}),
  };

  const jobRes = await fetch(`${API_URL}/api/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const jobBody = await safeJson(jobRes);
  if (!jobRes.ok) {
    throw new Error(errorMessage("Failed to create job", jobBody));
  }

  const newJob = jobBody || {};

  const [scraperRes, interviewRes] = await Promise.all([
    fetch(`${API_URL}/api/jobs/${newJob.id}/scraper`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scraperMetrics, scraperInstructions }),
    }),
    fetch(`${API_URL}/api/jobs/${newJob.id}/interview`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        interviewTone,
        interviewFocus,
        customQuestions,
        interviewLength,
        interviewInstructions,
      }),
    }),
  ]);

  if (!scraperRes.ok) {
    const scraperBody = await safeJson(scraperRes);
    throw new Error(errorMessage("Failed to save scraper config", scraperBody));
  }

  if (!interviewRes.ok) {
    const interviewBody = await safeJson(interviewRes);
    throw new Error(
      errorMessage("Failed to save interview config", interviewBody),
    );
  }

  return {
    ...newJob,
    title,
    jobType,
  };
}

/**
 * GET /api/jobs
 * Returns: Array<{ id, title, createdAt, applicantCount, applicationLink }>
 */
export async function getJobs() {
  const res = await fetch(`${API_URL}/api/jobs`);
  const body = await safeJson(res);
  if (!res.ok) throw new Error(errorMessage("Failed to fetch jobs", body));
  return body?.jobs || [];
}

/**
 * GET /api/jobs/:id
 * Returns: full job object
 */
export async function getJob(id) {
  const res = await fetch(`${API_URL}/api/jobs/${id}`);
  const body = await safeJson(res);
  if (!res.ok) throw new Error(errorMessage("Failed to fetch job", body));
  return body?.job || null;
}
