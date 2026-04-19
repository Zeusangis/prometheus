// src/api/jobs.js
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const mockDelay = () => new Promise((res) => setTimeout(res, 800));

// ── MOCK DATA ─────────────────────────────────────────────────
// Delete the mock blocks and uncomment the fetch calls
// once your teammate's backend is ready.
// ─────────────────────────────────────────────────────────────

/**
 * Orchestrates three sequential/parallel calls to create a job:
 *   1. POST /api/jobs           → job details (returns jobId)
 *   2. POST /api/jobs/:id/scraper    → GitHub scraper config
 *   3. POST /api/jobs/:id/interview  → AI interview config
 */
export async function createJob(jobData) {
  // --- MOCK ---
  await mockDelay();

  const { title, jobType, description, languages, frameworks,
          scraperMetrics, scraperInstructions,
          interviewTone, interviewFocus, customQuestions, interviewLength, interviewInstructions } = jobData;

  const payload = {
    job:       { title, jobType, description, languages, frameworks },
    scraper:   { scraperMetrics, scraperInstructions },
    interview: { interviewTone, interviewFocus, customQuestions, interviewLength, interviewInstructions },
  };
  console.log("POST /api/jobs", payload);

  const jobId = `job_${Date.now()}`;
  return {
    id: jobId,
    title: jobData.title,
    jobType: jobData.jobType,
    createdAt: new Date().toISOString(),
    applicationLink: `https://yourapp.com/apply/${jobId}`,
  };

  // --- REAL (uncomment when backend is ready) ---
  // const { title, jobType, description, languages, frameworks,
  //         scraperMetrics, scraperInstructions,
  //         interviewTone, interviewFocus, customQuestions, interviewLength, interviewInstructions } = jobData;

  // Step 1: create the job, get back the jobId
  // const jobRes = await fetch(`${API_URL}/api/jobs`, {
  //   method: "POST",
  //   headers: { "Content-Type": "application/json" },
  //   body: JSON.stringify({ title, jobType, description, languages, frameworks }),
  // });
  // if (!jobRes.ok) throw new Error("Failed to create job");
  // const newJob = await jobRes.json(); // expects { id, applicationLink, createdAt }

  // Step 2 & 3: send scraper + interview config in parallel
  // await Promise.all([
  //   fetch(`${API_URL}/api/jobs/${newJob.id}/scraper`, {
  //     method: "POST",
  //     headers: { "Content-Type": "application/json" },
  //     body: JSON.stringify({ scraperMetrics, scraperInstructions }),
  //   }).then(r => { if (!r.ok) throw new Error("Failed to save scraper config"); }),

  //   fetch(`${API_URL}/api/jobs/${newJob.id}/interview`, {
  //     method: "POST",
  //     headers: { "Content-Type": "application/json" },
  //     body: JSON.stringify({ interviewTone, interviewFocus, customQuestions, interviewLength, interviewInstructions }),
  //   }).then(r => { if (!r.ok) throw new Error("Failed to save interview config"); }),
  // ]);

  // return newJob;
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