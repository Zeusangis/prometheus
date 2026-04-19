// src/pages/apply/ApplyPage.jsx
import { useState } from "react";
import { useParams } from "@tanstack/react-router";
import { useQuery, useMutation } from "@tanstack/react-query";
import { submitApplication, getJobInfo } from "../../api/apply";

export default function ApplyPage() {
  const { jobId } = useParams({ strict: false });
  const [submitted, setSubmitted] = useState(false);
  const [interviewLink, setInterviewLink] = useState("");
  const [resumeFile, setResumeFile] = useState(null);
  const [form, setForm] = useState({
    name: "",
    email: "",
    github: "",
  });

  const { data: job, isLoading: jobLoading } = useQuery({
    queryKey: ["job-info", jobId],
    queryFn: () => getJobInfo(jobId),
    enabled: !!jobId,
  });

  const {
    mutate: apply,
    isPending,
    error,
  } = useMutation({
    mutationFn: () => {
      const formData = new FormData();
      formData.append("name", form.name);
      formData.append("email", form.email);
      formData.append("github", form.github);
      formData.append("jobId", jobId);
      if (resumeFile) formData.append("resume", resumeFile);
      return submitApplication(jobId, formData);
    },
    onSuccess: (data) => {
      setInterviewLink(data.interviewLink);
      setSubmitted(true);
    },
  });

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const handleSubmit = () => {
    if (!form.name || !form.email || !form.github || !resumeFile) return;
    apply();
  };

  // Success screen
  if (submitted) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="bg-white border border-gray-100 rounded-2xl p-8 max-w-md w-full text-center">
          <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path
                d="M4 10L8 14L16 6"
                stroke="#15803d"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <h1 className="text-lg font-semibold text-gray-900">
            Application submitted!
          </h1>
          <p className="text-sm text-gray-400 mt-2 leading-relaxed">
            Thanks for applying. We'll review your profile and send you an
            interview link shortly.
          </p>
          <div className="mt-6 p-3 bg-gray-50 rounded-xl border border-gray-100">
            <p className="text-xs text-gray-400 mb-1">Your interview link</p>
            <p className="text-xs text-gray-600 font-mono break-all">
              {interviewLink}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-lg mx-auto px-4 py-10">
        {/* Job header */}
        <div className="mb-8">
          {jobLoading ? (
            <div className="h-8 bg-gray-100 rounded-lg w-48 animate-pulse" />
          ) : (
            <>
              <p className="text-xs text-gray-400 mb-1">You're applying for</p>
              <h1 className="text-2xl font-semibold text-gray-900 tracking-tight">
                {job?.title}
              </h1>
              <p className="text-sm text-gray-400 mt-1">{job?.type}</p>
              {job?.description && (
                <p className="text-sm text-gray-500 mt-3 leading-relaxed">
                  {job?.description}
                </p>
              )}
            </>
          )}
        </div>

        {/* Form */}
        <div className="bg-white border border-gray-100 rounded-2xl p-6 flex flex-col gap-4">
          <h2 className="text-sm font-semibold text-gray-900">Your details</h2>

          <div>
            <label className="block text-xs text-gray-500 mb-1">
              Full name
            </label>
            <input
              type="text"
              value={form.name}
              onChange={set("name")}
              placeholder="Alex Johnson"
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 outline-none focus:border-gray-400"
            />
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">Email</label>
            <input
              type="email"
              value={form.email}
              onChange={set("email")}
              placeholder="alex@example.com"
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 outline-none focus:border-gray-400"
            />
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">
              GitHub username
            </label>
            <div className="flex items-center border border-gray-200 rounded-lg overflow-hidden focus-within:border-gray-400">
              <span className="text-sm text-gray-400 px-3 py-2 bg-gray-50 border-r border-gray-200">
                github.com/
              </span>
              <input
                type="text"
                value={form.github}
                onChange={set("github")}
                placeholder="alexjohnson"
                className="flex-1 text-sm px-3 py-2 outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">
              Resume (PDF)
            </label>
            <div
              onClick={() => document.getElementById("resume-input").click()}
              className={`border border-dashed rounded-lg px-4 py-6 text-center cursor-pointer transition-colors
                ${resumeFile ? "border-gray-300 bg-gray-50" : "border-gray-200 hover:border-gray-400"}`}
            >
              {resumeFile ? (
                <div>
                  <p className="text-sm text-gray-700 font-medium">
                    {resumeFile.name}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">Click to change</p>
                </div>
              ) : (
                <div>
                  <p className="text-sm text-gray-400">
                    Click to upload your resume
                  </p>
                  <p className="text-xs text-gray-300 mt-1">PDF only</p>
                </div>
              )}
            </div>
            <input
              id="resume-input"
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={(e) => setResumeFile(e.target.files[0])}
            />
          </div>
        </div>

        {/* Error */}
        {error && (
          <p className="mt-3 text-sm text-red-500 bg-red-50 border border-red-100 rounded-lg px-4 py-3">
            Something went wrong. Please try again.
          </p>
        )}

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={
            isPending ||
            !form.name ||
            !form.email ||
            !form.github ||
            !resumeFile
          }
          className="w-full mt-4 py-3 bg-gray-900 text-white text-sm font-medium rounded-xl hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-all"
        >
          {isPending ? "Submitting..." : "Submit application"}
        </button>

        <p className="text-xs text-gray-300 text-center mt-3">
          Your GitHub profile will be analysed as part of the review process.
        </p>
      </div>
    </div>
  );
}
