// src/api/apply.js
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const mockDelay = () => new Promise((res) => setTimeout(res, 800));

/**
 * POST /api/jobs/:jobId/apply
 * Submits a candidate application.
 *
 * BACKEND CONTRACT (tell your teammate):
 * Body: FormData with the following fields:
 *   - name: string
 *   - email: string
 *   - github: string (just the username, no URL)
 *   - resume: File (PDF)
 *   - jobId: string
 *
 * Returns: { id: string, interviewLink: string }
 * The interviewLink is the unique URL sent to the candidate for their interview.
 */
export async function submitApplication(jobId, formData) {
  // --- REAL ---
  const res = await fetch(`${import.meta.env.VITE_API_URL}/api/apply/${jobId}`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Failed to submit application");
  return res.json();
}

/**
 * GET /api/jobs/:jobId/info
 * Returns basic public info about the job for the apply page header.
 *
 * Returns: { title: string, type: string, description: string }
 */
export async function getJobInfo(jobId) {
  // --- MOCK ---
  await mockDelay();
  return {
    id: jobId,
    title: "Senior Backend Engineer",
    type: "Remote",
    description: "We are looking for a senior backend engineer to join our team and help build scalable systems.",
  };
  // --- REAL ---
  // const res = await fetch(`${API_URL}/api/jobs/${jobId}/info`);
  // if (!res.ok) throw new Error("Failed to fetch job info");
  // return res.json();
}