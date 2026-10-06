import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { useState } from "react";
import { getCompanyJobs, moveCandidateToNextStep } from "../api/jobs";
import { getScreeningQueue, type ScreeningCandidate } from "../api/screening";

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

export function Dashboard() {
  const queryClient = useQueryClient();
  const [actionError, setActionError] = useState<string | null>(null);

  const jobsQuery = useQuery({
    queryKey: ["company-jobs"],
    queryFn: getCompanyJobs,
  });
  const queueQuery = useQuery({
    queryKey: ["screening-queue"],
    queryFn: () => getScreeningQueue(),
  });

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
  const queue = queueQuery.data ?? [];
  const queueLoading = queueQuery.isLoading;
  const openJobs = jobs.filter((job) => job.status === "open").length;
  const awaitingScreening = queue.filter(
    (candidate) => candidate.status === "screening",
  ).length;
  const needsAttention = queue.filter((candidate) =>
    RETRYABLE.has(candidate.analysis_status),
  ).length;
  const inFlight = queue.filter((candidate) =>
    ["queued", "running"].includes(candidate.analysis_status),
  ).length;

  const pipeline = PIPELINE_STAGES.map((stage) => ({
    stage,
    label: toStatusLabel(stage),
    count: queue.filter((candidate) => candidate.status === stage).length,
  }));
  const pipelineTotal = pipeline.reduce((total, item) => total + item.count, 0);

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
          value={queueLoading ? "—" : String(queue.length)}
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
            Recruiting stages are tracked separately from analysis status.
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

        {queueLoading ? (
          <p className="mt-4 text-sm text-muted-foreground">
            Loading screening queue…
          </p>
        ) : queue.length === 0 ? (
          <p className="mt-4 text-sm text-muted-foreground">
            No applicants to screen yet.
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
                {queue.slice(0, 10).map((candidate) => {
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
            {queue.length > 10 ? (
              <p className="mt-3 text-xs text-muted-foreground">
                Showing the 10 most recent of {queue.length} applicants.
              </p>
            ) : null}
          </div>
        )}
      </section>
    </div>
  );
}
