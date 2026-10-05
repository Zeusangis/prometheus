// src/pages/apply/ApplyPage.jsx
import { useRef, useState } from "react";
import { useParams } from "@tanstack/react-router";
import { useMutation, useQuery } from "@tanstack/react-query";
import { getJobInfo, submitApplication } from "../../api/apply";

export default function ApplyPage() {
  const { jobId } = useParams({ strict: false });
  const { data: job, isLoading: isJobLoading, error: jobError } = useQuery({
    queryKey: ["public-job", jobId],
    queryFn: () => getJobInfo(jobId),
    enabled: !!jobId,
    retry: false,
  });
  const [submitted, setSubmitted] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const fileInputRef = useRef(null);
  const [resumeFile, setResumeFile] = useState(null);
  const [form, setForm] = useState({
    fullName: "",
    email: "",
    githubUsername: "",
  });

  const updateResumeFile = (file) => {
    if (!file) return;
    const isPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
    if (!isPdf) {
      setErrorMessage("Please upload a PDF file only.");
      return;
    }

    const maxSizeBytes = 5 * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      setErrorMessage("Maximum file size is 5MB.");
      return;
    }

    setErrorMessage("");
    setResumeFile(file);
  };

  const {
    mutate: apply,
    isPending,
    error,
  } = useMutation({
    mutationFn: () => {
      const formData = new FormData();
      formData.append("full_name", form.fullName);
      formData.append("email", form.email);
      formData.append("github_username", form.githubUsername);
      formData.append("jobId", jobId);

      if (resumeFile) {
        formData.append("resume", resumeFile);
      }

      return submitApplication(jobId, formData);
    },
    onSuccess: () => {
      setSubmitted(true);
    },
  });

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const handleSubmit = () => {
    if (!job || !form.fullName || !form.email || !resumeFile) {
      setErrorMessage("Please complete all fields before submitting.");
      return;
    }

    setErrorMessage("");
    apply();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    updateResumeFile(file);
  };

  // Success screen
  if (submitted) {
    return (
      <div className="min-h-screen bg-[#f3f4f4]">
        <header className="h-14 border-b border-[#e4e6e6] bg-white/90 backdrop-blur">
          <div className="mx-auto flex h-full w-full max-w-6xl items-center justify-between px-5">
            <div className="text-[31px] font-semibold tracking-[-0.02em] text-[#11543b]">
              TrueHire
            </div>
          </div>
        </header>

        <div className="flex min-h-[calc(100vh-56px)] items-center justify-center px-4 py-10">
          <div className="w-full max-w-xl rounded-[22px] border border-[#e4e6e6] bg-white p-8 text-center shadow-[0_8px_35px_rgba(14,48,34,0.08)]">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-[#d6efe1]">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path
                  d="M4 10L8 14L16 6"
                  stroke="#0f6c45"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
            <h1 className="text-2xl font-semibold text-[#1f2b24]">
              Application Submitted
            </h1>
            <p className="mt-2 text-sm text-[#57655e]">
              Thanks for applying. Your application has been saved for recruiter review.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f3f4f4]">
      <header className="h-14 border-b border-[#e4e6e6] bg-white/90 backdrop-blur">
        <div className="mx-auto flex h-full w-full max-w-6xl items-center justify-between px-5">
          <div className="text-[31px] font-semibold tracking-[-0.02em] text-[#11543b]">
            TrueHire
          </div>


        </div>
      </header>

      <main className="px-4 py-10">
        <div className="mx-auto w-full max-w-lg rounded-[22px] border border-[#e4e6e6] bg-white p-8 shadow-[0_8px_35px_rgba(14,48,34,0.08)]">
          <div className="mb-6 flex items-start gap-3">
            <div className="mt-1 flex h-9 w-9 items-center justify-center rounded-full bg-[#d6efe1] text-[#0f6c45]">
              <svg width="15" height="18" viewBox="0 0 15 18" fill="none">
                <path
                  d="M3 1.5H8.25L12 5.25V16.5H3V1.5Z"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <path
                  d="M8.25 1.5V5.25H12"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>

            <div>
              <h1 className="text-[37px] font-semibold tracking-[-0.01em] text-[#1f2b24]">
                {isJobLoading ? "Loading job…" : job?.title || "Job unavailable"}
              </h1>
              <p className="mt-1 text-sm text-[#617067]">
                {job ? `${job.company} • ${job.type}${job.location ? ` • ${job.location}` : ""}` : ""}
              </p>
            </div>
          </div>

          {jobError && <p role="alert" className="mb-4 text-sm text-red-700">{jobError.message}</p>}
          {job?.description && <p className="mb-6 whitespace-pre-wrap text-sm text-[#617067]">{job.description}</p>}
          <fieldset disabled={!job || isPending} className="space-y-4">
            <div>
              <label className="mb-2 block text-[11px] font-semibold uppercase tracking-[0.18em] text-[#33433a]">
                Full Name
              </label>
              <input
                aria-label="Full Name"
                type="text"
                value={form.fullName}
                onChange={set("fullName")}
                placeholder="Alex Rivers"
                className="w-full rounded-xl border border-[#e4e6e6] px-4 py-3 text-sm text-[#1f2b24] outline-none placeholder:text-[#a2ada7] focus:border-[#b9c9bf]"
              />
            </div>

            <div>
              <label className="mb-2 block text-[11px] font-semibold uppercase tracking-[0.18em] text-[#33433a]">
                Email Address
              </label>
              <input
                aria-label="Email Address"
                type="email"
                value={form.email}
                onChange={set("email")}
                placeholder="alex.rivers@example.com"
                className="w-full rounded-xl border border-[#e4e6e6] px-4 py-3 text-sm text-[#1f2b24] outline-none placeholder:text-[#a2ada7] focus:border-[#b9c9bf]"
              />
            </div>

            <div>
              <label className="mb-2 block text-[11px] font-semibold uppercase tracking-[0.18em] text-[#33433a]">
                GitHub Username (optional)
              </label>
              <div className="flex overflow-hidden rounded-xl border border-[#e4e6e6] focus-within:border-[#b9c9bf]">
                <span className="border-r border-[#e4e6e6] bg-[#f9faf9] px-4 py-3 text-sm text-[#445449]">
                  github.com/
                </span>
                <input
                  aria-label="GitHub Username"
                  type="text"
                  value={form.githubUsername}
                  onChange={set("githubUsername")}
                  placeholder="username"
                  className="w-full px-4 py-3 text-sm text-[#1f2b24] outline-none placeholder:text-[#a2ada7]"
                />
              </div>
            </div>

            <div>
              <label className="mb-2 block text-[11px] font-semibold uppercase tracking-[0.18em] text-[#33433a]">
                Resume (PDF)
              </label>
              <div
                role="button"
                tabIndex={0}
                onClick={() => fileInputRef.current?.click()}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    fileInputRef.current?.click();
                  }
                }}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragActive(true);
                }}
                onDragLeave={() => setDragActive(false)}
                onDrop={handleDrop}
                className={`rounded-2xl border border-dashed px-4 py-8 text-center transition-colors ${
                  dragActive
                    ? "border-[#7cb699] bg-[#eef8f2]"
                    : "border-[#d8dcda] bg-[#f4f5f5]"
                }`}
              >
                <div className="mx-auto mb-2 flex h-7 w-7 items-center justify-center text-[#0f6c45]">
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <path
                      d="M10 13.75V4.5"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                    />
                    <path
                      d="M6.25 8.25L10 4.5L13.75 8.25"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                    <path
                      d="M4.5 15.5H15.5"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                    />
                  </svg>
                </div>
                {resumeFile ? (
                  <>
                    <p className="text-sm font-semibold text-[#1f2b24]">
                      {resumeFile.name}
                    </p>
                    <p className="mt-1 text-xs text-[#617067]">
                      Click to upload a different PDF
                    </p>
                  </>
                ) : (
                  <>
                    <p className="text-sm text-[#1f2b24]">
                      Click to upload or drag and drop
                    </p>
                    <p className="mt-1 text-xs text-[#7a847f]">
                      Maximum file size: 5MB
                    </p>
                  </>
                )}
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,application/pdf"
                className="hidden"
                onChange={(e) => updateResumeFile(e.target.files?.[0])}
              />
            </div>
          </fieldset>

          {(errorMessage || error) && (
            <p className="mt-4 rounded-lg border border-[#f1cccc] bg-[#fff6f5] px-3 py-2 text-sm text-[#9a3530]">
              {errorMessage || error?.message || "Something went wrong. Please try again."}
            </p>
          )}

          <button
            onClick={handleSubmit}
            disabled={
              isPending ||
              !job ||
              !form.fullName ||
              !form.email ||
              !resumeFile
            }
            className="mt-6 flex w-full items-center justify-center gap-2 rounded-2xl bg-[#0f6c45] py-3.5 text-sm font-semibold text-white transition-colors hover:bg-[#0d5c3b] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isPending ? "Submitting..." : "Submit Application"}
            {!isPending && <span aria-hidden>→</span>}
          </button>
        </div>
      </main>
    </div>
  );
}
