import { StatCard } from "./StatCard";
import { HiringAnalytics } from "./HiringAnalytics";
import { Reminders } from "./Reminders";
import { TeamCollaboration } from "./TeamCollaboration";
import { HiringProgress } from "./HiringProgress";
import { TimeTracker } from "./TimeTracker";
import { Link } from "@tanstack/react-router";

const recentJobs = [
  {
    title: "Senior Product Designer",
    status: "Active",
    count: "48 applicants",
  },
  { title: "Marketing Manager", status: "Active", count: "24 applicants" },
  { title: "Backend Engineer", status: "Closed", count: "Archived" },
];

const stats = [
  {
    title: "Total Jobs",
    value: 24,
    subtitle: "Increased from last month",
    highlighted: true,
  },
  {
    title: "Total Applicants",
    value: 156,
    subtitle: "Increased from last month",
    highlighted: false,
  },
  {
    title: "Interviews",
    value: 42,
    subtitle: "Increased from last month",
    highlighted: false,
  },
  {
    title: "Pending Reviews",
    value: 8,
    subtitle: "On discuss",
    highlighted: false,
  },
];

export function Dashboard() {
  return (
    <div className="flex-1 p-6 overflow-auto">
      {/* Dashboard Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
          <p className="text-muted-foreground">
            Plan, prioritize, and accomplish your hiring goals with ease.
          </p>
        </div>
        <div className="flex gap-3">
          <Link
            className="flex items-center gap-2 bg-primary hover:bg-primary-light text-white font-semibold px-5 py-2.5 rounded-xl transition-colors"
            to="/jobs/new"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            Add Job
          </Link>
          <button className="flex items-center gap-2 bg-card border border-border hover:border-primary text-foreground font-semibold px-5 py-2.5 rounded-xl transition-colors">
            Import Data
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {stats.map((stat, index) => (
          <StatCard key={index} {...stat} />
        ))}
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-12 gap-4">
        {/* Analytics */}
        <div className="col-span-5">
          <HiringAnalytics />
        </div>

        {/* Reminders */}
        <div className="col-span-3">
          <Reminders />
        </div>

        {/* Jobs Overview */}
        <div className="col-span-4 row-span-2 rounded-2xl border border-border bg-card p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h3 className="text-lg font-semibold text-foreground">
                Jobs Overview
              </h3>
              <p className="text-sm text-muted-foreground">
                Quick view of the current hiring pipeline.
              </p>
            </div>
            <Link
              to="/dashboard/jobs"
              className="rounded-xl border border-border px-3 py-2 text-sm font-semibold text-primary transition-colors hover:border-primary"
            >
              View all
            </Link>
          </div>

          <div className="mt-5 space-y-3">
            {recentJobs.map((job) => (
              <div
                key={job.title}
                className="flex items-center justify-between rounded-2xl border border-border bg-background px-4 py-3"
              >
                <div>
                  <p className="font-semibold text-foreground">{job.title}</p>
                  <p className="text-sm text-muted-foreground">{job.count}</p>
                </div>
                <span
                  className={`rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] ${
                    job.status === "Active"
                      ? "bg-[#dff0e5] text-[#0f6c45]"
                      : "bg-[#eef1ef] text-[#64736b]"
                  }`}
                >
                  {job.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Team Collaboration */}
        <div className="col-span-5">
          <TeamCollaboration />
        </div>

        {/* Hiring Progress */}
        <div className="col-span-3">
          <HiringProgress />
        </div>

        {/* Time Tracker - spans below */}
        <div className="col-span-4">
          <TimeTracker />
        </div>
      </div>
    </div>
  );
}
