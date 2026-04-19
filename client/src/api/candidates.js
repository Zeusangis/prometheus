// src/api/candidates.js
const mockDelay = () => new Promise((res) => setTimeout(res, 800));

const MOCK_JOBS = [
  { id: "job_1",  title: "Senior Backend Engineer",   type: "Remote",  createdAt: "2025-01-10T00:00:00Z", applicantCount: 8,  applicationLink: "https://yourapp.com/apply/job_1"  },
  { id: "job_2",  title: "Frontend Developer",        type: "Hybrid",  createdAt: "2025-01-14T00:00:00Z", applicantCount: 5,  applicationLink: "https://yourapp.com/apply/job_2"  },
  { id: "job_3",  title: "DevOps Engineer",           type: "Onsite",  createdAt: "2025-01-16T00:00:00Z", applicantCount: 3,  applicationLink: "https://yourapp.com/apply/job_3"  },
  { id: "job_4",  title: "Machine Learning Engineer", type: "Remote",  createdAt: "2025-01-17T00:00:00Z", applicantCount: 12, applicationLink: "https://yourapp.com/apply/job_4"  },
  { id: "job_5",  title: "Product Designer",          type: "Hybrid",  createdAt: "2025-01-18T00:00:00Z", applicantCount: 7,  applicationLink: "https://yourapp.com/apply/job_5"  },
  { id: "job_6",  title: "Data Engineer",             type: "Remote",  createdAt: "2025-01-19T00:00:00Z", applicantCount: 4,  applicationLink: "https://yourapp.com/apply/job_6"  },
  { id: "job_7",  title: "iOS Developer",             type: "Onsite",  createdAt: "2025-01-20T00:00:00Z", applicantCount: 6,  applicationLink: "https://yourapp.com/apply/job_7"  },
  { id: "job_8",  title: "Security Engineer",         type: "Remote",  createdAt: "2025-01-21T00:00:00Z", applicantCount: 9,  applicationLink: "https://yourapp.com/apply/job_8"  },
  { id: "job_9",  title: "Cloud Architect",           type: "Hybrid",  createdAt: "2025-01-22T00:00:00Z", applicantCount: 2,  applicationLink: "https://yourapp.com/apply/job_9"  },
  { id: "job_10", title: "Full Stack Developer",      type: "Remote",  createdAt: "2025-01-23T00:00:00Z", applicantCount: 11, applicationLink: "https://yourapp.com/apply/job_10" },
  { id: "job_11", title: "Android Developer",         type: "Onsite",  createdAt: "2025-01-24T00:00:00Z", applicantCount: 3,  applicationLink: "https://yourapp.com/apply/job_11" },
  { id: "job_12", title: "QA Engineer",               type: "Hybrid",  createdAt: "2025-01-25T00:00:00Z", applicantCount: 5,  applicationLink: "https://yourapp.com/apply/job_12" },
  { id: "job_13", title: "Backend Engineer",          type: "Remote",  createdAt: "2025-01-26T00:00:00Z", applicantCount: 8,  applicationLink: "https://yourapp.com/apply/job_13" },
  { id: "job_14", title: "Site Reliability Engineer", type: "Remote",  createdAt: "2025-01-27T00:00:00Z", applicantCount: 4,  applicationLink: "https://yourapp.com/apply/job_14" },
  { id: "job_15", title: "Data Scientist",            type: "Hybrid",  createdAt: "2025-01-28T00:00:00Z", applicantCount: 10, applicationLink: "https://yourapp.com/apply/job_15" },
  { id: "job_16", title: "Platform Engineer",         type: "Remote",  createdAt: "2025-01-29T00:00:00Z", applicantCount: 6,  applicationLink: "https://yourapp.com/apply/job_16" },
  { id: "job_17", title: "React Native Developer",    type: "Hybrid",  createdAt: "2025-01-30T00:00:00Z", applicantCount: 3,  applicationLink: "https://yourapp.com/apply/job_17" },
  { id: "job_18", title: "Technical Lead",            type: "Onsite",  createdAt: "2025-01-31T00:00:00Z", applicantCount: 7,  applicationLink: "https://yourapp.com/apply/job_18" },
  { id: "job_19", title: "Embedded Systems Engineer", type: "Onsite",  createdAt: "2025-02-01T00:00:00Z", applicantCount: 2,  applicationLink: "https://yourapp.com/apply/job_19" },
  { id: "job_20", title: "Developer Advocate",        type: "Remote",  createdAt: "2025-02-02T00:00:00Z", applicantCount: 5,  applicationLink: "https://yourapp.com/apply/job_20" },
];

const MOCK_CANDIDATES = [
  { id: "c_1",  jobId: "job_1",  name: "Alex Johnson",  github: "alexjohnson",  appliedAt: "2025-01-12T00:00:00Z", overallScore: 87, languageMatch: 92, codeQuality: 85, codeSecurity: 78, topLanguages: ["Python", "Go"],          teamFit: "Strong",   engineerLevel: "Senior",    interviewComplete: true  },
  { id: "c_2",  jobId: "job_1",  name: "Sara Mills",    github: "saramills",    appliedAt: "2025-01-13T00:00:00Z", overallScore: 74, languageMatch: 80, codeQuality: 70, codeSecurity: 65, topLanguages: ["TypeScript", "Python"],  teamFit: "Good",     engineerLevel: "Mid-level", interviewComplete: true  },
  { id: "c_3",  jobId: "job_1",  name: "James Carter",  github: "jamescarter",  appliedAt: "2025-01-14T00:00:00Z", overallScore: 91, languageMatch: 95, codeQuality: 90, codeSecurity: 88, topLanguages: ["Go", "Rust"],            teamFit: "Strong",   engineerLevel: "Senior",    interviewComplete: false },
  { id: "c_4",  jobId: "job_2",  name: "Priya Patel",   github: "priyapatel",   appliedAt: "2025-01-15T00:00:00Z", overallScore: 83, languageMatch: 88, codeQuality: 82, codeSecurity: 75, topLanguages: ["React", "TypeScript"],   teamFit: "Strong",   engineerLevel: "Mid-level", interviewComplete: true  },
  { id: "c_5",  jobId: "job_2",  name: "Tom Wu",        github: "tomwu",        appliedAt: "2025-01-16T00:00:00Z", overallScore: 61, languageMatch: 65, codeQuality: 58, codeSecurity: 55, topLanguages: ["JavaScript"],            teamFit: "Moderate", engineerLevel: "Junior",    interviewComplete: false },
  { id: "c_6",  jobId: "job_3",  name: "Nina Ross",     github: "ninaross",     appliedAt: "2025-01-17T00:00:00Z", overallScore: 79, languageMatch: 82, codeQuality: 76, codeSecurity: 80, topLanguages: ["Python", "Docker"],      teamFit: "Good",     engineerLevel: "Senior",    interviewComplete: true  },
  { id: "c_7",  jobId: "job_4",  name: "Leo Kim",       github: "leokim",       appliedAt: "2025-01-18T00:00:00Z", overallScore: 93, languageMatch: 96, codeQuality: 91, codeSecurity: 89, topLanguages: ["Python", "PyTorch"],     teamFit: "Strong",   engineerLevel: "Senior",    interviewComplete: true  },
  { id: "c_8",  jobId: "job_4",  name: "Maya Singh",    github: "mayasingh",    appliedAt: "2025-01-19T00:00:00Z", overallScore: 88, languageMatch: 90, codeQuality: 87, codeSecurity: 82, topLanguages: ["Python", "TensorFlow"],  teamFit: "Strong",   engineerLevel: "Senior",    interviewComplete: true  },
  { id: "c_9",  jobId: "job_5",  name: "Chris Lee",     github: "chrislee",     appliedAt: "2025-01-20T00:00:00Z", overallScore: 76, languageMatch: 78, codeQuality: 74, codeSecurity: 70, topLanguages: ["Figma", "React"],        teamFit: "Good",     engineerLevel: "Mid-level", interviewComplete: false },
  { id: "c_10", jobId: "job_6",  name: "Dana White",    github: "danawhite",    appliedAt: "2025-01-21T00:00:00Z", overallScore: 82, languageMatch: 85, codeQuality: 80, codeSecurity: 77, topLanguages: ["Spark", "Python"]}];

export async function getJobs() {
  await mockDelay();
  return MOCK_JOBS;
}

export async function getCandidates(jobId) {
  await mockDelay();
  return MOCK_CANDIDATES.filter((c) => c.jobId === jobId);
}

export async function getCandidate(id) {
  await mockDelay();
  return MOCK_CANDIDATES.find((c) => c.id === id) || null;
}