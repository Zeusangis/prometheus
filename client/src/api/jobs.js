// src/api/jobs.js
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const mockDelay = () => new Promise((res) => setTimeout(res, 800));

// ── MOCK DATA ─────────────────────────────────────────────────
// Delete the mock blocks and uncomment the fetch calls
// once your teammate's backend is ready.
// ─────────────────────────────────────────────────────────────

/**
 * POST /api/jobs
 * Body: full job config from the wizard
 * Returns: { id, applicationLink, createdAt }
 */
export async function createJob(jobData) {
  // --- MOCK ---
  await mockDelay();
  return {
    id: `job_${Date.now()}`,
    ...jobData,
    createdAt: new Date().toISOString(),
    applicationLink: `https://yourapp.com/apply/job_${Date.now()}`,
  };
  // --- REAL (uncomment when backend is ready) ---
  // const res = await fetch(`${API_URL}/api/jobs`, {
  //   method: "POST",
  //   headers: { "Content-Type": "application/json" },
  //   body: JSON.stringify(jobData),
  // });
  // if (!res.ok) throw new Error("Failed to create job");
  // return res.json();
}

/**
 * GET /api/jobs
 * Returns: Array<{ id, title, createdAt, applicantCount, applicationLink }>
 */
export async function getJobs() {
  // --- MOCK ---
  await mockDelay();
  return [];
  // --- REAL ---
  // const res = await fetch(`${API_URL}/api/jobs`);
  // if (!res.ok) throw new Error("Failed to fetch jobs");
  // return res.json();
}

/**
 * GET /api/jobs/:id
 * Returns: full job object
 */
export async function getJob(id) {
  // --- MOCK ---
  await mockDelay();
  return null;
  // --- REAL ---
  // const res = await fetch(`${API_URL}/api/jobs/${id}`);
  // if (!res.ok) throw new Error("Failed to fetch job");
  // return res.json();
}