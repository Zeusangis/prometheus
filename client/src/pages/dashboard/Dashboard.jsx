// src/pages/dashboard/Dashboard.jsx
import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useDashboardJobs } from "../../hooks/useCandidates";

function StatCard({ label, value, sub }) {
  return (
    <div className="bg-white border border-gray-100 rounded-2xl p-5">
      <p className="text-xs text-gray-400">{label}</p>
      <p className="text-3xl font-semibold text-gray-900 mt-1">{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

function JobRow({ job, onClick }) {
  return (
    <div
      onClick={onClick}
      className="flex items-center justify-between p-4 hover:bg-gray-50 cursor-pointer rounded-xl transition-colors"
    >
      <div className="flex flex-col gap-0.5">
        <p className="text-sm font-medium text-gray-900">{job.title}</p>
        <p className="text-xs text-gray-400">{job.type}</p>
      </div>
      <div className="flex items-center gap-6">
        <div className="text-right">
          <p className="text-sm font-medium text-gray-900">{job.applicantCount}</p>
          <p className="text-xs text-gray-400">applicants</p>
        </div>
        <span className="text-gray-300 text-lg">→</span>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { data: jobs, isLoading, error } = useDashboardJobs();
  const navigate = useNavigate();

  const totalApplicants = jobs?.reduce((sum, j) => sum + j.applicantCount, 0) ?? 0;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-10">

        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900 tracking-tight">Dashboard</h1>
            <p className="text-sm text-gray-400 mt-1">Overview of all your job postings.</p>
          </div>
          <button
            onClick={() => navigate({ to: "/jobs/new" })}
            className="text-sm px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-700 cursor-pointer transition-all"
          >
            + New job
          </button>
        </div>

        {/* Stat cards */}
        <div className="grid grid-cols-3 gap-3 mb-6">
          <StatCard
            label="Total jobs"
            value={isLoading ? "—" : jobs?.length ?? 0}
            sub="active postings"
          />
          <StatCard
            label="Total applicants"
            value={isLoading ? "—" : totalApplicants}
            sub="across all jobs"
          />
          <StatCard
            label="Interviews done"
            value="—"
            sub="coming soon"
          />
        </div>

        {/* Job list */}
        <div className="bg-white border border-gray-100 rounded-2xl">
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
            <h2 className="text-sm font-semibold text-gray-900">Job postings</h2>
            <span className="text-xs text-gray-400">{jobs?.length ?? 0} total</span>
          </div>

          {isLoading && (
            <div className="px-5 py-8 text-center text-sm text-gray-400">
              Loading...
            </div>
          )}

          {error && (
            <div className="px-5 py-8 text-center text-sm text-red-400">
              Failed to load jobs.
            </div>
          )}

          {!isLoading && !error && jobs?.length === 0 && (
            <div className="px-5 py-8 text-center">
              <p className="text-sm text-gray-400">No jobs yet.</p>
              <button
                onClick={() => navigate({ to: "/jobs/new" })}
                className="mt-3 text-sm text-gray-900 underline cursor-pointer"
              >
                Create your first job posting
              </button>
            </div>
          )}

          {!isLoading && jobs?.map((job, i) => (
            <div key={job.id} className={i < jobs.length - 1 ? "border-b border-gray-100" : ""}>
              <JobRow
                job={job}
                onClick={() => navigate({ to: `/dashboard/${job.id}` })}
              />
            </div>
          ))}
        </div>

      </div>
    </div>
  );
}