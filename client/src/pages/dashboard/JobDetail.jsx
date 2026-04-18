// src/pages/dashboard/JobDetail.jsx
import { useState } from "react";
import { useParams, useNavigate } from "@tanstack/react-router";
import { useCandidates, useDashboardJobs } from "../../hooks/useCandidates";

function ScoreBadge({ score }) {
  const color =
    score >= 85 ? "bg-green-100 text-green-700" :
    score >= 70 ? "bg-yellow-100 text-yellow-700" :
                  "bg-red-100 text-red-700";
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${color}`}>
      {score}
    </span>
  );
}

function FitBadge({ fit }) {
  const color =
    fit === "Strong"   ? "bg-green-100 text-green-700" :
    fit === "Good"     ? "bg-blue-100 text-blue-700" :
    fit === "Moderate" ? "bg-yellow-100 text-yellow-700" :
                         "bg-gray-100 text-gray-500";
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${color}`}>
      {fit}
    </span>
  );
}

function CandidateRow({ candidate, onClick }) {
  return (
    <div
      onClick={onClick}
      className="flex items-center justify-between p-4 hover:bg-gray-50 cursor-pointer rounded-xl transition-colors"
    >
      <div className="flex flex-col gap-0.5">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium text-gray-900">{candidate.name}</p>
          {!candidate.interviewComplete && (
            <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
              interview pending
            </span>
          )}
        </div>
        <p className="text-xs text-gray-400">
          @{candidate.github} · {candidate.topLanguages.join(", ")} · {candidate.engineerLevel}
        </p>
      </div>
      <div className="flex items-center gap-3">
        <FitBadge fit={candidate.teamFit} />
        <ScoreBadge score={candidate.overallScore} />
        <span className="text-gray-300 text-lg">→</span>
      </div>
    </div>
  );
}

export default function JobDetail() {
  const { jobId } = useParams({ strict: false });
  const navigate = useNavigate();
  const [search, setSearch] = useState("");

  const { data: candidates, isLoading, error } = useCandidates(jobId);
  const { data: jobs } = useDashboardJobs();

  const job = jobs?.find((j) => j.id === jobId);

  const sorted = candidates
    ? [...candidates].sort((a, b) => b.overallScore - a.overallScore)
    : [];

  const filtered = sorted.filter((c) =>
    c.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-10">

        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate({ to: "/dashboard" })}
            className="text-xs text-gray-400 hover:text-gray-600 cursor-pointer mb-4 flex items-center gap-1 transition-colors"
          >
            ← Back to dashboard
          </button>
          <h1 className="text-2xl font-semibold text-gray-900 tracking-tight">
            {job?.title ?? "Job posting"}
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            {job?.type} · {candidates?.length ?? 0} applicants
          </p>
        </div>

        {/* Candidate list */}
        <div className="bg-white border border-gray-100 rounded-2xl">
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
            <h2 className="text-sm font-semibold text-gray-900">Applicants</h2>
            <span className="text-xs text-gray-400">sorted by score</span>
          </div>

          {/* Search */}
          <div className="px-4 py-3 border-b border-gray-100">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by name..."
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 outline-none focus:border-gray-400"
            />
          </div>

          {isLoading && (
            <div className="px-5 py-8 text-center text-sm text-gray-400">
              Loading...
            </div>
          )}

          {error && (
            <div className="px-5 py-8 text-center text-sm text-red-400">
              Failed to load candidates.
            </div>
          )}

          {!isLoading && filtered.length === 0 && (
            <div className="px-5 py-8 text-center text-sm text-gray-400">
              {search ? `No candidates matching "${search}"` : "No applicants yet."}
            </div>
          )}

          {!isLoading && filtered.map((candidate, i) => (
            <div key={candidate.id} className={i < filtered.length - 1 ? "border-b border-gray-100" : ""}>
              <CandidateRow
                candidate={candidate}
                onClick={() => navigate({ to: `/candidate/${candidate.id}` })}
              />
            </div>
          ))}

        </div>
      </div>
    </div>
  );
}