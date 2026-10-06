import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { getCompanyJobs, moveCandidateToNextStep } from "../api/jobs";
import { getAnalysisReadiness } from "../api/health";
import {
  DEFAULT_PAGE_SIZE,
  PAGE_SIZE_OPTIONS,
  getScreeningQueue,
  type ScreeningCandidate,
} from "../api/screening";

const PIPELINE_STAGES = [
  "screening",
  "interview_scheduled",
  "interview_completed",
  "offer_made",
  "hired",
  "rejected",
] as const;

const STAGE_BADGE: Record<string, string> = {
  screening: "bg-primary-lighter/35 text-primary-dark",
  interview_scheduled: "bg-[#daf2e2] text-[#246747]",
  interview_completed: "bg-[#dcecff] text-[#254f8d]",
  offer_made: "bg-[#efe6ff] text-[#4f3a9e]",
  hired: "bg-[#d8f6e4] text-[#1c7f4d]",
  rejected: "bg-[#ffe3e0] text-[#9a3530]",
};

const ANALYSIS_BADGE: Record<string, string> = {
  complete: "text-[#1c7f4d]",
  partial: "text-[#8a5a05]",
  failed: "text-[#9a3530]",
  enqueue_failed: "text-[#9a3530]",
  queued: "text-muted-foreground",
  running: "text-[#254f8d]",
};

const RETRYABLE = new Set(["failed", "enqueue_failed", "partial"]);
const IN_FLIGHT = ["queued", "running"];

/** The named groupings the queue API understands, so the client invents no vocabulary. */
const VIEW_OPTIONS = [
  { value: "", label: "All applicants" },
  { value: "attention", label: "Needs attention" },
  { value: "running", label: "Queued or running" },
] as const;

type QueueView = "" | "attention" | "running";

type QueueFilters = {
  stage: string;
  analysisStatus: string;
  view: QueueView;
  jobId: string;
  q: string;
  page: number;
  pageSize: number;
};

const EMPTY_FILTERS: QueueFilters = {
  stage: "",
  analysisStatus: "",
  view: "",
  jobId: "",
  q: "",
  page: 1,
  pageSize: DEFAULT_PAGE_SIZE,
};

const SEARCH_DEBOUNCE_MS = 300;

function toStatusLabel(value: string) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatSubmitted(value: string) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "-";
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(parsed);
}

function toPublicGitHubUrl(username: string | null) {
  return username ? `https://github.com/${encodeURIComponent(username)}` : null;
}

/**
 * Quote a CSV cell, and stop a stored value from being executed as a spreadsheet
 * formula when the export is opened in Excel or Sheets.
 */
function csvCell(value: string | number | null) {
  const text = value === null || value === undefined ? "" : String(value);
  const guarded = /^[=+\-@\t\r]/.test(text) ? `'${text}` : text;
  return `"${guarded.replace(/"/g, '""')}"`;
}

function Metric({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <article className="rounded-2xl border border-border bg-card p-5">
      <p className="text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
        {label}
      </p>
      <p className="mt-2 text-4xl font-semibold leading-none text-foreground">
        {value}
      </p>
      <p className="mt-2 text-xs text-muted-foreground">{detail}</p>
    </article>
  );
}

function Select({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <label className="flex flex-col gap-1 text-xs font-semibold text-muted-foreground">
      {label}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="rounded-xl border border-border bg-background px-3 py-2 text-sm font-normal text-foreground"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

export function Dashboard() {
  const queryClient = useQueryClient();
  const [actionError, setActionError] = useState<string | null>(null);
  const [filters, setFilters] = useState<QueueFilters>(EMPTY_FILTERS);
  const [searchInput, setSearchInput] = useState("");

  const jobsQuery = useQuery({
    queryKey: ["company-jobs"],
    queryFn: getCompanyJobs,
  });
  const queueQuery = useQuery({
    queryKey: ["screening-queue", filters],
    queryFn: () =>
      getScreeningQueue({
        stage: filters.stage || undefined,
        analysisStatus: filters.analysisStatus || undefined,
        attention: filters.view === "attention",
        running: filters.view === "running",
        jobId: filters.jobId,
        q: filters.q,
        page: filters.page,
        pageSize: filters.pageSize,
      }),
    // Keep the previous page visible while the next one loads.
    placeholderData: (previous) => previous,
  });
  const readinessQuery = useQuery({
    queryKey: ["analysis-readiness"],
    queryFn: getAnalysisReadiness,
    staleTime: 60_000,
  });

  // Debounce typing so a search does not fire a request per keystroke.
  useEffect(() => {
    const handle = window.setTimeout(() => {
      setFilters((current) =>
        current.q === searchInput
          ? current
          : { ...current, q: searchInput, page: 1 },
      );
    }, SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(handle);
  }, [searchInput]);

  const moveStage = useMutation({
    mutationFn: (candidate: ScreeningCandidate) => {
      const nextStage = candidate.allowed_actions.find(
        (action) => action !== "rejected",
      );
      if (!nextStage || candidate.job_id === null) {
        throw new Error("This applicant has no available stage change.");
      }
      return moveCandidateToNextStep({
        jobId: String(candidate.job_id),
        candidateId: candidate.id,
        nextStatus: nextStage,
      });
    },
    onSuccess: async () => {
      setActionError(null);
      await queryClient.invalidateQueries({ queryKey: ["screening-queue"] });
      await queryClient.invalidateQueries({ queryKey: ["company-jobs"] });
      await queryClient.invalidateQueries({ queryKey: ["job-applicants"] });
    },
    onError: (error) =>
      setActionError(
        error instanceof Error ? error.message : "Stage change failed.",
      ),
  });

  const jobs = jobsQuery.data ?? [];
  const queue = queueQuery.data?.candidates ?? [];
  const summary = queueQuery.data?.summary;
  const queueLoading = queueQuery.isLoading;
  const page = queueQuery.data?.page ?? filters.page;
  const pageSize = queueQuery.data?.pageSize ?? filters.pageSize;
  const total = queueQuery.data?.total ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / pageSize));
  const firstRow = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const lastRow = Math.min(page * pageSize, total);

  // Every metric is organization-wide, so filtering or paging never changes it.
  const stageCounts = summary?.stage_counts ?? {};
  const analysisCounts = summary?.analysis_counts ?? {};
  const totalApplicants = summary?.total_applicants ?? 0;
  const openJobs = jobs.filter((job) => job.status === "open").length;
  const awaitingScreening = stageCounts.screening ?? 0;
  const needsAttention = [...RETRYABLE].reduce(
    (sum, status) => sum + (analysisCounts[status] ?? 0),
    0,
  );
  const inFlight = IN_FLIGHT.reduce(
    (sum, status) => sum + (analysisCounts[status] ?? 0),
    0,
  );

  const pipeline = PIPELINE_STAGES.map((stage) => ({
    stage,
    label: toStatusLabel(stage),
    count: stageCounts[stage] ?? 0,
  }));
  const pipelineTotal = pipeline.reduce((sum, item) => sum + item.count, 0);

  const hasFilters =
    Boolean(filters.stage) ||
    Boolean(filters.analysisStatus) ||
    Boolean(filters.view) ||
    Boolean(filters.jobId) ||
    Boolean(filters.q);

  const updateFilters = (patch: Partial<QueueFilters>) =>
    setFilters((current) => ({ ...current, ...patch, page: patch.page ?? 1 }));

  const clearFilters = () => {
    setSearchInput("");
    setFilters((current) => ({
      ...EMPTY_FILTERS,
      pageSize: current.pageSize,
    }));
  };

  const exportPageCsv = () => {
    const header = [
      "Applicant",
      "Email",
      "GitHub",
      "Role",
      "Stage",
      "Analysis",
      "ATS score",
      "Submitted",
    ];
    const rows = queue.map((candidate) => [
      candidate.full_name || `Candidate #${candidate.id}`,
      candidate.email,
      candidate.github_username ?? "not provided",
      candidate.job_title,
      candidate.status,
      candidate.analysis_status,
      candidate.ats_score === null ? "Not measured" : String(candidate.ats_score),
      candidate.uploaded_at,
    ]);
    const csv = [header, ...rows]
      .map((row) => row.map(csvCell).join(","))
      .join("\r\n");
    const blob = new Blob([`\uFEFF${csv}`], {
      type: "text/csv;charset=utf-8;",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `screening-queue-page-${page}.csv`;
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  };

  const jobOptions = [
    { value: "", label: "All roles" },
    ...jobs.map((job) => ({ value: String(job.id), label: job.title })),
  ];
  const stageOptions = [
    { value: "", label: "All stages" },
    ...PIPELINE_STAGES.map((stage) => ({
      value: stage,
      label: toStatusLabel(stage),
    })),
  ];
  const analysisOptions = [
    { value: "", label: "All analysis states" },
    ...Object.keys(ANALYSIS_BADGE).map((status) => ({
      value: status,
      label: toStatusLabel(status),
    })),
  ];

  return (
    <div className="flex-1 overflow-auto p-6">
      <div className="mb-6 flex items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
          <p className="text-muted-foreground">
            Screening queue and pipeline for your organization, from saved
            applicant records.
          </p>
        </div>
        <Link
          to="/jobs/new"
          className="flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 font-semibold text-primary-foreground transition-colors hover:bg-primary-light"
        >
          Add Job
        </Link>
      </div>

      {readinessQuery.data?.resume_provider_configured === false ? (
        <p
          role="status"
          className="mb-6 rounded-2xl border border-[#f0e0b8] bg-[#fdf8ec] px-4 py-3 text-sm text-[#7a5a12]"
        >
          <strong>Resume analysis is not configured on the server.</strong> Set{" "}
          <code>GEMINI_API_KEY</code> in <code>talent_intelligence_backend/.env</code>
          {" "}and restart the Celery worker. Applications are still saved and
          GitHub evidence still runs; resume analysis will keep failing and
          saying so until the key is set.
        </p>
      ) : null}

      {jobsQuery.error || queueQuery.error ? (
        <p
          role="alert"
          className="mb-6 rounded-2xl border border-[#ffe3e0] bg-[#fff6f5] px-4 py-3 text-sm text-[#9a3530]"
        >
          {jobsQuery.error instanceof Error
            ? jobsQuery.error.message
            : queueQuery.error instanceof Error
              ? queueQuery.error.message
              : "Failed to load dashboard data."}
        </p>
      ) : null}

      {actionError ? (
        <p
          role="alert"
          className="mb-6 rounded-2xl border border-[#ffe3e0] bg-[#fff6f5] px-4 py-3 text-sm text-[#9a3530]"
        >
          {actionError}
        </p>
      ) : null}

      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metric
          label="Open roles"
          value={jobsQuery.isLoading ? "—" : String(openJobs)}
          detail={`${jobs.length} role${jobs.length === 1 ? "" : "s"} in total`}
        />
        <Metric
          label="Applicants"
          value={queueLoading ? "—" : String(totalApplicants)}
          detail="Applicants linked to your organization's jobs"
        />
        <Metric
          label="Awaiting screening"
          value={queueLoading ? "—" : String(awaitingScreening)}
          detail="Still in the screening stage"
        />
        <Metric
          label="Analysis needs attention"
          value={queueLoading ? "—" : String(needsAttention)}
          detail={
            inFlight
              ? `${inFlight} analysis job${inFlight === 1 ? "" : "s"} still queued or running`
              : "Failed or partial results a recruiter can retry"
          }
        />
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-12">
        <section className="rounded-2xl border border-border bg-card p-5 xl:col-span-5">
          <h2 className="text-lg font-semibold text-foreground">
            Pipeline distribution
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Recruiting stages are tracked separately from analysis status. Counts
            cover the whole organization, not the current filter.
          </p>
          {queueLoading ? (
            <p className="mt-4 text-sm text-muted-foreground">
              Loading pipeline…
            </p>
          ) : pipelineTotal === 0 ? (
            <p className="mt-4 text-sm text-muted-foreground">
              No applicants yet. Share a job link to start collecting
              applications.
            </p>
          ) : (
            <ul className="mt-4 space-y-3">
              {pipeline.map((item) => (
                <li key={item.stage}>
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium text-foreground">
                      {item.label}
                    </span>
                    <span className="text-muted-foreground">{item.count}</span>
                  </div>
                  <div className="mt-1 h-2 rounded-full bg-secondary">
                    <div
                      className="h-2 rounded-full bg-primary"
                      style={{
                        width: `${(item.count / pipelineTotal) * 100}%`,
                      }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="rounded-2xl border border-border bg-card p-5 xl:col-span-7">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-foreground">Roles</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Applicant and interviewing counts are computed from stored
                applications.
              </p>
            </div>
            <Link
              to="/dashboard/jobs"
              className="rounded-xl border border-border px-3 py-2 text-sm font-semibold text-primary transition-colors hover:border-primary"
            >
              View all
            </Link>
          </div>
          {jobsQuery.isLoading ? (
            <p className="mt-4 text-sm text-muted-foreground">Loading roles…</p>
          ) : jobs.length === 0 ? (
            <p className="mt-4 text-sm text-muted-foreground">
              No roles yet. Create one to start screening applicants.
            </p>
          ) : (
            <ul className="mt-4 space-y-3">
              {jobs.slice(0, 5).map((job) => (
                <li
                  key={job.id}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border bg-background px-4 py-3"
                >
                  <div className="min-w-0">
                    <Link
                      to="/dashboard/$jobId"
                      params={{ jobId: String(job.id).replace(/^job_/, "") }}
                      className="font-semibold text-foreground hover:text-primary"
                    >
                      {job.title}
                    </Link>
                    <p className="text-sm text-muted-foreground">
                      {job.total_applicants} applicant
                      {job.total_applicants === 1 ? "" : "s"} ·{" "}
                      {job.interviewing_count} interviewing
                    </p>
                  </div>
                  <span
                    className={`rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] ${
                      job.status === "open"
                        ? "bg-[#dff0e5] text-[#0f6c45]"
                        : "bg-[#eef1ef] text-[#64736b]"
                    }`}
                  >
                    {job.status}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <section className="mt-4 rounded-2xl border border-border bg-card p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-foreground">
              Screening queue
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Saved resume analysis for each applicant. Scores are evidence for
              review, never a hiring decision.
            </p>
          </div>
          <Link
            to="/dashboard/jobs"
            className="rounded-xl border border-border px-3 py-2 text-sm font-semibold text-primary transition-colors hover:border-primary"
          >
            Screening per role
          </Link>
        </div>

        <div className="mt-4 flex flex-wrap items-end gap-3 rounded-2xl border border-border bg-background p-4">
          <label className="flex min-w-56 flex-1 flex-col gap-1 text-xs font-semibold text-muted-foreground">
            Search
            <input
              type="search"
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder="Name or email"
              aria-label="Search applicants by name or email"
              className="rounded-xl border border-border bg-card px-3 py-2 text-sm font-normal text-foreground"
            />
          </label>
          <Select
            label="Stage"
            value={filters.stage}
            onChange={(value) => updateFilters({ stage: value })}
            options={stageOptions}
          />
          <Select
            label="Analysis"
            value={filters.analysisStatus}
            onChange={(value) => updateFilters({ analysisStatus: value })}
            options={analysisOptions}
          />
          <Select
            label="View"
            value={filters.view}
            onChange={(value) => updateFilters({ view: value as QueueView })}
            options={[...VIEW_OPTIONS]}
          />
          <Select
            label="Role"
            value={filters.jobId}
            onChange={(value) => updateFilters({ jobId: value })}
            options={jobOptions}
          />
          <Select
            label="Rows per page"
            value={String(filters.pageSize)}
            onChange={(value) => updateFilters({ pageSize: Number(value) })}
            options={PAGE_SIZE_OPTIONS.map((size) => ({
              value: String(size),
              label: String(size),
            }))}
          />
          {hasFilters ? (
            <button
              onClick={clearFilters}
              className="rounded-xl border border-border px-3 py-2 text-sm font-semibold text-primary transition-colors hover:border-primary"
            >
              Clear filters
            </button>
          ) : null}
        </div>

        {queueLoading ? (
          <p className="mt-4 text-sm text-muted-foreground">
            Loading screening queue…
          </p>
        ) : queue.length === 0 ? (
          <p className="mt-4 text-sm text-muted-foreground">
            {hasFilters
              ? "No applicants match these filters."
              : "No applicants to screen yet."}
          </p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full border-collapse text-left">
              <thead>
                <tr className="text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
                  <th className="py-2 pr-4">Applicant</th>
                  <th className="py-2 pr-4">Role</th>
                  <th className="py-2 pr-4">Stage</th>
                  <th className="py-2 pr-4">Resume analysis</th>
                  <th className="py-2 pr-4">ATS evidence</th>
                  <th className="py-2 pr-4">Submitted</th>
                  <th className="py-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {queue.map((candidate) => {
                  const nextStage = candidate.allowed_actions.find(
                    (action) => action !== "rejected",
                  );
                  const isMoving =
                    moveStage.isPending &&
                    moveStage.variables?.id === candidate.id;
                  const githubUrl = toPublicGitHubUrl(candidate.github_username);
                  return (
                    <tr key={candidate.id} className="border-t border-border">
                      <td className="py-3 pr-4">
                        <Link
                          to="/profile/$candidateId"
                          params={{ candidateId: String(candidate.id) }}
                          className="font-semibold text-foreground hover:text-primary"
                        >
                          {candidate.full_name || `Candidate #${candidate.id}`}
                        </Link>
                        <p className="text-xs text-muted-foreground">
                          {candidate.email || "No email on record"}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {githubUrl ? (
                            <a
                              href={githubUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="underline"
                            >
                              @{candidate.github_username}
                            </a>
                          ) : (
                            "GitHub: not provided"
                          )}
                        </p>
                      </td>
                      <td className="py-3 pr-4 text-sm">
                        {candidate.job_id !== null ? (
                          <Link
                            to="/dashboard/$jobId"
                            params={{ jobId: String(candidate.job_id) }}
                            className="text-primary hover:text-primary-light"
                          >
                            {candidate.job_title}
                          </Link>
                        ) : (
                          candidate.job_title
                        )}
                      </td>
                      <td className="py-3 pr-4">
                        <span
                          className={`inline-flex rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.12em] ${
                            STAGE_BADGE[candidate.status] ??
                            "bg-secondary text-primary-dark"
                          }`}
                        >
                          {toStatusLabel(candidate.status)}
                        </span>
                      </td>
                      <td className="py-3 pr-4 text-sm">
                        <span
                          className={
                            ANALYSIS_BADGE[candidate.analysis_status] ??
                            "text-muted-foreground"
                          }
                        >
                          {toStatusLabel(candidate.analysis_status)}
                        </span>
                        {RETRYABLE.has(candidate.analysis_status) ? (
                          <Link
                            to="/profile/$candidateId"
                            params={{ candidateId: String(candidate.id) }}
                            className="mt-1 block text-xs font-semibold text-primary underline"
                          >
                            Review and retry
                          </Link>
                        ) : null}
                      </td>
                      <td className="py-3 pr-4 text-sm">
                        {candidate.ats_score === null
                          ? "Not measured"
                          : `${candidate.ats_score} / 100`}
                      </td>
                      <td className="py-3 pr-4 text-sm text-muted-foreground">
                        {formatSubmitted(candidate.uploaded_at)}
                      </td>
                      <td className="py-3">
                        <div className="flex flex-wrap items-center gap-2">
                          <Link
                            to="/profile/$candidateId"
                            params={{ candidateId: String(candidate.id) }}
                            className="rounded-xl border border-border px-3 py-1.5 text-xs font-semibold text-primary hover:border-primary"
                          >
                            View profile
                          </Link>
                          {nextStage ? (
                            <button
                              onClick={() => moveStage.mutate(candidate)}
                              disabled={moveStage.isPending}
                              className="rounded-xl bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary-light disabled:cursor-not-allowed disabled:bg-secondary disabled:text-muted-foreground"
                            >
                              {isMoving
                                ? "Moving…"
                                : `Move to ${toStatusLabel(nextStage)}`}
                            </button>
                          ) : (
                            <span className="text-xs text-muted-foreground">
                              No further action
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
              <p className="text-xs text-muted-foreground">
                Showing {firstRow}–{lastRow} of {total} applicant
                {total === 1 ? "" : "s"}
                {hasFilters ? " matching these filters" : ""}.{" "}
                <button
                  onClick={exportPageCsv}
                  className="font-semibold text-primary underline"
                >
                  Export this page as CSV
                </button>
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => updateFilters({ page: page - 1 })}
                  disabled={page <= 1}
                  className="rounded-xl border border-border px-3 py-1.5 text-xs font-semibold text-primary transition-colors hover:border-primary disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Previous
                </button>
                <span className="text-xs text-muted-foreground">
                  Page {page} of {pageCount}
                </span>
                <button
                  onClick={() => updateFilters({ page: page + 1 })}
                  disabled={page >= pageCount}
                  className="rounded-xl border border-border px-3 py-1.5 text-xs font-semibold text-primary transition-colors hover:border-primary disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
