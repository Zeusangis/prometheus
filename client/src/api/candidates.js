// src/api/candidates.js
const mockDelay = () => new Promise((res) => setTimeout(res, 800));

// ── MOCK DATA ─────────────────────────────────────────────────
const MOCK_JOBS = [
  {
    id: "job_1",
    title: "Senior Backend Engineer",
    type: "Remote",
    createdAt: "2025-01-10T00:00:00Z",
    applicantCount: 8,
    applicationLink: "https://yourapp.com/apply/job_1",
  },
  {
    id: "job_2",
    title: "Frontend Developer",
    type: "Hybrid",
    createdAt: "2025-01-14T00:00:00Z",
    applicantCount: 5,
    applicationLink: "https://yourapp.com/apply/job_2",
  },
  {
    id: "job_3",
    title: "DevOps Engineer",
    type: "Onsite",
    createdAt: "2025-01-16T00:00:00Z",
    applicantCount: 3,
    applicationLink: "https://yourapp.com/apply/job_3",
  },
];

const MOCK_CANDIDATES = [
  {
    id: "c_1",
    jobId: "job_1",
    name: "Alex Johnson",
    github: "alexjohnson",
    appliedAt: "2025-01-12T00:00:00Z",
    overallScore: 87,
    languageMatch: 92,
    codeQuality: 85,
    codeSecurity: 78,
    topLanguages: ["Python", "Go"],
    teamFit: "Strong",
    engineerLevel: "Senior",
    interviewComplete: true,
  },
  {
    id: "c_2",
    jobId: "job_1",
    name: "Sara Mills",
    github: "saramills",
    appliedAt: "2025-01-13T00:00:00Z",
    overallScore: 74,
    languageMatch: 80,
    codeQuality: 70,
    codeSecurity: 65,
    topLanguages: ["TypeScript", "Python"],
    teamFit: "Good",
    engineerLevel: "Mid-level",
    interviewComplete: true,
  },
  {
    id: "c_3",
    jobId: "job_1",
    name: "James Carter",
    github: "jamescarter",
    appliedAt: "2025-01-14T00:00:00Z",
    overallScore: 91,
    languageMatch: 95,
    codeQuality: 90,
    codeSecurity: 88,
    topLanguages: ["Go", "Rust"],
    teamFit: "Strong",
    engineerLevel: "Senior",
    interviewComplete: false,
  },
  {
    id: "c_4",
    jobId: "job_2",
    name: "Priya Patel",
    github: "priyapatel",
    appliedAt: "2025-01-15T00:00:00Z",
    overallScore: 83,
    languageMatch: 88,
    codeQuality: 82,
    codeSecurity: 75,
    topLanguages: ["React", "TypeScript"],
    teamFit: "Strong",
    engineerLevel: "Mid-level",
    interviewComplete: true,
  },
  {
    id: "c_5",
    jobId: "job_2",
    name: "Tom Wu",
    github: "tomwu",
    appliedAt: "2025-01-16T00:00:00Z",
    overallScore: 61,
    languageMatch: 65,
    codeQuality: 58,
    codeSecurity: 55,
    topLanguages: ["JavaScript"],
    teamFit: "Moderate",
    engineerLevel: "Junior",
    interviewComplete: false,
  },
  {
    id: "c_6",
    jobId: "job_3",
    name: "Nina Ross",
    github: "ninaross",
    appliedAt: "2025-01-17T00:00:00Z",
    overallScore: 79,
    languageMatch: 82,
    codeQuality: 76,
    codeSecurity: 80,
    topLanguages: ["Python", "Docker"],
    teamFit: "Good",
    engineerLevel: "Senior",
    interviewComplete: true,
  },
];
// ─────────────────────────────────────────────────────────────

/**
 * GET /api/jobs
 * Returns all jobs with applicant counts.
 */
export async function getJobs() {
  // --- MOCK ---
  await mockDelay();
  return MOCK_JOBS;
  // --- REAL ---
  // const res = await fetch(`${API_URL}/api/jobs`);
  // if (!res.ok) throw new Error("Failed to fetch jobs");
  // return res.json();
}

/**
 * GET /api/jobs/:id/candidates
 * Returns all candidates for a specific job.
 */
export async function getCandidates(jobId) {
  // --- MOCK ---
  await mockDelay();
  return MOCK_CANDIDATES.filter((c) => c.jobId === jobId);
  // --- REAL ---
  // const res = await fetch(`${API_URL}/api/jobs/${jobId}/candidates`);
  // if (!res.ok) throw new Error("Failed to fetch candidatesxs");
  // return res.json();
}

const MOCK_CANDIDATE_DETAIL = {
  id: "c_1",
  jobId: "job_1",
  name: "Alex Johnson",
  github: "alexjohnson",
  appliedAt: "2025-01-12T00:00:00Z",
  overallScore: 87,
  languageMatch: 92,
  codeQuality: 85,
  codeSecurity: 78,
  commitConsistency: 80,
  projectComplexity: 88,
  openSource: 70,
  testCoverage: 65,
  topLanguages: ["Python", "Go"],
  teamFit: "Strong",
  engineerLevel: "Senior",
  interviewComplete: true,
  scraperSummary: "Alex has a strong GitHub presence with 12 public repositories spanning backend systems and CLI tooling. Their Python code is well structured with consistent naming conventions and clear separation of concerns. Notable projects include a distributed task queue built with Redis and a REST API framework with 98% test coverage. Code security practices are generally solid though some older repos show hardcoded config values. Commit history is consistent over the past 2 years with meaningful commit messages. Overall a strong technical profile that aligns well with the role requirements.",
  interviewSummary: "Alex demonstrated a deep and genuine understanding of their own work throughout the interview. They were able to explain architectural decisions clearly and showed strong awareness of tradeoffs. When challenged on security decisions in older projects they acknowledged the issues and described how they would approach them differently today. Problem solving approach is methodical and they communicate technical concepts well. Recommended for next round.",
  interviewTranscript: [
    { role: "ai",        message: "Walk me through the distributed task queue project on your GitHub. What problem were you solving and why did you make the architectural decisions you did?" },
    { role: "candidate", message: "Sure — the project started because we had a monolith that was struggling with long running jobs blocking the main thread. I chose Redis as the broker because we were already using it for caching and I wanted to minimise new infrastructure. The worker pool is configurable and each worker runs in its own goroutine." },
    { role: "ai",        message: "Why Go specifically for the workers rather than staying in Python?" },
    { role: "candidate", message: "Mostly for the concurrency model. Goroutines are much lighter than Python threads and since we were doing a lot of I/O bound work the scheduling worked really well for us. Python would have worked but we would have needed more instances." },
    { role: "ai",        message: "I noticed in some of your older repos there are hardcoded API keys in config files. How do you think about secrets management now compared to when you wrote that?" },
    { role: "candidate", message: "Yeah that's embarrassing honestly. That was early on before I understood the implications. Now I use environment variables for everything local and a secrets manager like AWS Secrets Manager or Vault in production. I've also added pre-commit hooks to catch that kind of thing before it ever hits the repo." },
    { role: "ai",        message: "If you were to rewrite the task queue today what would you change?" },
    { role: "candidate", message: "I'd add dead letter queues from the start — right now failed jobs just get dropped which isn't great. I'd also add proper observability with distributed tracing instead of just logging. And I'd make the serialization format pluggable rather than hardcoding JSON." },
  ],
};

export async function getCandidate(id) {
  // --- MOCK ---
  await mockDelay();
  return MOCK_CANDIDATE_DETAIL;
  // --- REAL ---
  // const res = await fetch(`${API_URL}/api/candidates/${id}`);
  // if (!res.ok) throw new Error("Failed to fetch candidate");
  // return res.json();
}