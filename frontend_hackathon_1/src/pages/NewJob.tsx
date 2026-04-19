import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { createJob } from "../api/jobs";
import type { CreatedJob, NewJobInput } from "../api/jobs";
import { consoleData, consoleNewJobFormData } from "../utils/consoleData";
import JobDetails from "../components/jobs/steps/JobDetails";
import ScraperConfig from "../components/jobs/steps/ScraperConfig";
import InterviewSetup from "../components/jobs/steps/InterviewSetup";
import ReviewCreate from "../components/jobs/steps/ReviewCreate";

const DEFAULT_JOB = {
  title: "",
  jobType: "",
  description: "",
  languages: [],
  frameworks: [],
  scraperMetrics: {
    languageMatch: { enabled: true, weight: 80 },
    codeQuality: { enabled: true, weight: 70 },
    codeSecurity: { enabled: true, weight: 60 },
    commitConsistency: { enabled: false, weight: 50 },
    projectComplexity: { enabled: false, weight: 65 },
    openSource: { enabled: false, weight: 40 },
    testCoverage: { enabled: false, weight: 55 },
  },
  scraperInstructions: "",
  interviewTone: "conversational",
  interviewFocus: [
    "Understanding of their own code",
    "Problem-solving approach",
  ],
  customQuestions: [
    "Walk me through a project on your GitHub that you're most proud of and explain the key decisions you made.",
    "Is there anything in your GitHub you'd rewrite today? What would you change and why?",
  ],
  interviewLength: 30,
  interviewInstructions: "",
};

const STEPS = [
  { id: 1, label: "Job details" },
  { id: 2, label: "Scraper config" },
  { id: 3, label: "Interview setup" },
  { id: 4, label: "Review" },
];

export default function NewJob() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [jobData, setJobData] = useState(DEFAULT_JOB);
  const [createdJob, setCreatedJob] = useState<CreatedJob | null>(null);
  const {
    mutate: submitJob,
    isPending,
    error,
  } = useMutation<CreatedJob, Error, NewJobInput>({ mutationFn: createJob });

  const handleSubmit = () => {
    consoleNewJobFormData(jobData);

    submitJob(jobData, {
      onSuccess: (newJob) => {
        consoleData("Create Job Success", newJob);
        setCreatedJob(newJob);
      },
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-10">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-gray-900 tracking-tight">
            Create a job posting
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Set up the role, configure what to look for, and launch.
          </p>
        </div>

        <div className="flex items-center mb-8">
          {STEPS.map((s, i) => (
            <div key={s.id} className="flex items-center">
              <div className="flex items-center gap-2">
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium transition-all
                  ${
                    step > s.id
                      ? "bg-green-100 text-green-700"
                      : step === s.id
                        ? "bg-gray-900 text-white"
                        : "bg-white border border-gray-200 text-gray-400"
                  }`}
                >
                  {step > s.id ? "✓" : s.id}
                </div>
                <span
                  className={`text-xs whitespace-nowrap ${step === s.id ? "text-gray-900 font-medium" : "text-gray-400"}`}
                >
                  {s.label}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <div className="w-8 h-px bg-gray-200 mx-2 shrink-0" />
              )}
            </div>
          ))}
        </div>

        {step === 1 && <JobDetails data={jobData} onChange={setJobData} />}
        {step === 2 && <ScraperConfig data={jobData} onChange={setJobData} />}
        {step === 3 && <InterviewSetup data={jobData} onChange={setJobData} />}
        {step === 4 && <ReviewCreate data={jobData} />}

        {error && (
          <p className="mt-4 text-sm text-red-500 bg-red-50 border border-red-100 rounded-lg px-4 py-3">
            Something went wrong: {error.message}
          </p>
        )}

        <div className="flex justify-between items-center mt-6 pt-5 border-t border-gray-100">
          <button
            onClick={() => setStep((s) => s - 1)}
            style={{ visibility: step === 1 ? "hidden" : "visible" }}
            className="text-sm px-4 py-2 border border-gray-200 rounded-lg text-gray-500 hover:border-gray-400 hover:text-gray-700 cursor-pointer transition-all"
          >
            ← Back
          </button>

          <span className="text-xs text-gray-300">
            Step {step} of {STEPS.length}
          </span>

          {step < STEPS.length ? (
            <button
              onClick={() => setStep((s) => s + 1)}
              className="text-sm px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-700 cursor-pointer transition-all"
            >
              Next →
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={isPending}
              className="text-sm px-4 py-2 bg-green-700 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 cursor-pointer transition-all"
            >
              {isPending ? "Creating..." : "Create job ✓"}
            </button>
          )}
        </div>
      </div>

      {createdJob && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 px-4">
          <div className="w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl">
            <div className="flex items-start gap-4">
              <div className="grid h-12 w-12 shrink-0 place-items-center rounded-full bg-green-100 text-green-700">
                ✓
              </div>
              <div className="min-w-0">
                <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-green-700">
                  Success
                </p>
                <h2 className="mt-1 text-2xl font-semibold text-gray-900">
                  Job created successfully
                </h2>
                <p className="mt-2 text-sm leading-6 text-gray-500">
                  Your new role is live and ready to share with candidates.
                </p>
              </div>
            </div>

            <div className="mt-5 rounded-2xl border border-gray-100 bg-gray-50 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-gray-400">
                Application link
              </p>
              <p className="mt-2 break-all text-sm font-medium text-gray-900">
                {createdJob.applicationLink}
              </p>
            </div>

            <div className="mt-6 flex flex-col gap-3 sm:flex-row">
              <button
                onClick={() => {
                  setCreatedJob(null);
                  navigate({
                    to: "/dashboard/$jobId",
                    params: { jobId: createdJob.id },
                  });
                }}
                className="inline-flex flex-1 items-center justify-center rounded-2xl bg-green-700 px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-green-600"
              >
                View job
              </button>
              <button
                onClick={() => {
                  setCreatedJob(null);
                  navigate({ to: "/dashboard/jobs" });
                }}
                className="inline-flex flex-1 items-center justify-center rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm font-semibold text-gray-700 transition-colors hover:border-gray-400"
              >
                Back to jobs
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
