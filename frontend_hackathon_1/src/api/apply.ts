type JobInfo = {
  id: string;
  title: string;
  type: string;
  description: string;
};

type ApplyResponse = {
  interviewLink: string;
};

export async function getJobInfo(jobId: string): Promise<JobInfo> {
  return {
    id: jobId,
    title: "Frontend Engineer",
    type: "Full-time",
    description: "Build product experiences with React and TypeScript.",
  };
}

export async function submitApplication(
  _jobId: string,
  _formData: FormData,
): Promise<ApplyResponse> {
  return {
    interviewLink: "https://calendar.example.com/interview/intro-call",
  };
}
