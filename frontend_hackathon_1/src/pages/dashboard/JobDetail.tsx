import { Link, useParams } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Sidebar } from "../../components/Sidebar";
import { Header } from "../../components/Header";
import {
  getJobApplicants,
  getJobById,
  moveCandidateToNextStep,
  normalizeJobId,
  type JobApplicant,
} from "../../api/jobs";

const pipelineStats = [
  { label: "Sourcing", value: 124, progress: 78 },
  { label: "Screening", value: 48, progress: 46 },
  { label: "Verification", value: 12, progress: 24 },
  { label: "Interview", value: 8, progress: 16 },
  { label: "Offer", value: 2, progress: 10, highlighted: true },
];

const statusBadgeClassMap: Record<string, string> = {
  queued: "bg-secondary text-primary-dark",
  uploaded: "bg-secondary text-primary-dark",
  ats_scored: "bg-primary-lighter/35 text-primary-dark",
  interview_scheduled: "bg-[#daf2e2] text-[#246747]",
  interview_completed: "bg-[#dcecff] text-[#254f8d]",
  offer_made: "bg-[#efe6ff] text-[#4f3a9e]",
  hired: "bg-[#d8f6e4] text-[#1c7f4d]",
  screening: "bg-primary-lighter/35 text-primary-dark",
  shortlisted: "bg-[#daf2e2] text-[#246747]",
  rejected: "bg-[#ffe3e0] text-[#9a3530]",
};

const nextStatusMap: Record<string, string | null> = {
  queued: "uploaded",
  uploaded: "ats_scored",
  ats_scored: "interview_scheduled",
  interview_scheduled: "interview_completed",
  interview_completed: "offer_made",
  offer_made: "hired",
  hired: null,
  rejected: null,
  screening: "ats_scored",
  shortlisted: "interview_scheduled",
};

function toStatusLabel(status: string) {
  return status
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export default function JobDetail() {
  const { jobId } = useParams({ from: "/dashboard/$jobId" });
  const queryClient = useQueryClient();
  const [actionError, setActionError] = useState<string | null>(null);
  const [confirmMoveTarget, setConfirmMoveTarget] = useState<{
    candidateId: number;
    candidateName: string;
    nextStatus: string;
  } | null>(null);
  const [isShareDialogOpen, setIsShareDialogOpen] = useState(false);
  const [copyFeedback, setCopyFeedback] = useState<"idle" | "copied" | "error">(
    "idle",
  );
  const {
    data: job,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["job-detail", jobId],
    queryFn: () => getJobById(jobId),
    enabled: !!jobId,
  });
  const {
    data: applicants,
    isLoading: isApplicantsLoading,
    error: applicantsError,
  } = useQuery({
    queryKey: ["job-applicants", jobId],
    queryFn: () => getJobApplicants(jobId),
    enabled: !!jobId,
  });

  const moveStageMutation = useMutation({
    mutationFn: async (params: { candidateId: number; nextStatus: string }) => {
      return moveCandidateToNextStep({
        jobId,
        candidateId: params.candidateId,
        nextStatus: params.nextStatus,
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["job-applicants", jobId],
      });
      setActionError(null);
    },
    onError: (error) => {
      setActionError(
        error instanceof Error
          ? error.message
          : "Failed to move candidate to next stage",
      );
    },
  });

  const handleMoveToNextStage = (applicant: JobApplicant) => {
    const normalizedStatus = applicant.status.toLowerCase();
    const nextStatus = nextStatusMap[normalizedStatus];

    if (!nextStatus) {
      return;
    }

    setConfirmMoveTarget({
      candidateId: applicant.id,
      candidateName: applicant.full_name,
      nextStatus,
    });
  };

  const confirmMoveToNextStage = () => {
    if (!confirmMoveTarget) {
      return;
    }

    setActionError(null);
    moveStageMutation.mutate({
      candidateId: confirmMoveTarget.candidateId,
      nextStatus: confirmMoveTarget.nextStatus,
    });
    setConfirmMoveTarget(null);
  };

  const statusLabel =
    job?.status === "open"
      ? "Active"
      : job?.status === "closed"
        ? "Closed"
        : "Draft";

  const postedDateLabel = (() => {
    if (!job?.posted_date) return "-";
    const parsed = new Date(job.posted_date);
    if (Number.isNaN(parsed.getTime())) return "-";
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    }).format(parsed);
  })();

  const applicationLink =
    typeof window === "undefined"
      ? ""
      : `${window.location.origin}/apply/${normalizeJobId(jobId)}`;

  const handleCopyApplicationLink = async () => {
    try {
      await navigator.clipboard.writeText(applicationLink);
      setCopyFeedback("copied");
    } catch {
      setCopyFeedback("error");
    }
  };

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">
        <Header />

        <main className="px-6 pb-8 pt-2 md:px-8">
          <div className="max-w-6xl mx-auto">
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-primary hover:text-primary-light"
            >
              <span aria-hidden>←</span>
              Back to Dashboard
            </Link>

            <section className="mt-6 flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
              <div>
                {isLoading ? (
                  <p className="text-sm text-muted-foreground">
                    Loading job details...
                  </p>
                ) : error ? (
                  <p className="text-sm text-red-600">
                    Failed to load job details. Please verify backend is
                    running.
                  </p>
                ) : (
                  <>
                    <div className="flex items-center gap-3 text-sm">
                      <span className="rounded-full bg-primary-lighter/35 px-3 py-1 text-xs font-semibold text-primary-dark">
                        {statusLabel}
                      </span>
                      <span className="text-muted-foreground">
                        • {job?.location || job?.jobType || "Remote"}
                      </span>
                    </div>

                    <h1 className="mt-2 text-4xl leading-tight font-semibold text-foreground">
                      {job?.title}
                    </h1>

                    <p className="mt-3 text-muted-foreground">
                      Posted: {postedDateLabel} • Company: {job?.company || "-"}
                    </p>
                    {job?.description && (
                      <p className="mt-3 max-w-3xl text-sm text-muted-foreground">
                        {job.description}
                      </p>
                    )}
                    <div className="mt-4 flex flex-wrap gap-2">
                      {(job?.languages || []).map((language) => (
                        <span
                          key={language}
                          className="rounded-full bg-secondary px-3 py-1 text-xs font-semibold text-primary-dark"
                        >
                          {language}
                        </span>
                      ))}
                      {(job?.frameworks || []).map((framework) => (
                        <span
                          key={framework}
                          className="rounded-full bg-primary-lighter/35 px-3 py-1 text-xs font-semibold text-primary-dark"
                        >
                          {framework}
                        </span>
                      ))}
                    </div>
                  </>
                )}
              </div>

              <div className="flex flex-wrap gap-3">
                <button className="rounded-2xl border border-border bg-card px-5 py-3 text-sm font-semibold text-primary hover:border-primary">
                  Edit Job Description
                </button>
                <button
                  onClick={() => {
                    setCopyFeedback("idle");
                    setIsShareDialogOpen(true);
                  }}
                  className="rounded-2xl bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground hover:bg-primary-light"
                >
                  Share Job Link
                </button>
              </div>
            </section>

            <section className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
              {pipelineStats.map((stat) => (
                <article
                  key={stat.label}
                  className={`rounded-3xl border p-4 ${
                    stat.highlighted
                      ? "bg-primary border-primary text-primary-foreground shadow-lg"
                      : "bg-card border-border"
                  }`}
                >
                  <p
                    className={`text-[11px] uppercase tracking-[0.18em] ${
                      stat.highlighted
                        ? "text-primary-foreground/70"
                        : "text-muted-foreground"
                    }`}
                  >
                    {stat.label}
                  </p>
                  <p className="mt-2 text-5xl font-semibold leading-none">
                    {stat.value}
                  </p>
                  <div
                    className={`mt-4 h-1.5 w-full rounded-full ${
                      stat.highlighted ? "bg-primary-dark/40" : "bg-secondary"
                    }`}
                  >
                    <div
                      className={`h-1.5 rounded-full ${
                        stat.highlighted
                          ? "bg-primary-foreground"
                          : "bg-primary"
                      }`}
                      style={{ width: `${stat.progress}%` }}
                    />
                  </div>
                </article>
              ))}
            </section>

            <section className="mt-8">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-2xl font-semibold text-foreground">
                  Recent Applicants
                </h2>

                <div className="flex items-center gap-2">
                  <button className="grid h-10 w-10 place-items-center rounded-xl border border-border bg-card text-muted-foreground hover:text-foreground">
                    <span>⌄</span>
                  </button>
                  <button className="grid h-10 w-10 place-items-center rounded-xl border border-border bg-card text-muted-foreground hover:text-foreground">
                    <span>☰</span>
                  </button>
                </div>
              </div>

              <div className="space-y-3">
                {actionError ? (
                  <article className="rounded-3xl border border-[#ffe3e0] bg-[#fff6f5] px-4 py-3 text-sm text-[#9a3530]">
                    {actionError}
                  </article>
                ) : null}

                {isApplicantsLoading ? (
                  <article className="rounded-3xl border border-border bg-card px-4 py-5 text-sm text-muted-foreground">
                    Loading applicants...
                  </article>
                ) : applicantsError ? (
                  <article className="rounded-3xl border border-[#ffe3e0] bg-[#fff6f5] px-4 py-5 text-sm text-[#9a3530]">
                    Failed to load applicants. Please verify backend is running.
                  </article>
                ) : (applicants?.length ?? 0) === 0 ? (
                  <article className="rounded-3xl border border-border bg-card px-4 py-5 text-sm text-muted-foreground">
                    No applicants yet.
                  </article>
                ) : (
                  applicants?.map((applicant) => {
                    const uploadedDateLabel = (() => {
                      const parsed = new Date(applicant.uploaded_at);
                      if (Number.isNaN(parsed.getTime())) return "-";
                      return new Intl.DateTimeFormat("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      }).format(parsed);
                    })();
                    const normalizedStatus = applicant.status.toLowerCase();
                    const statusClass =
                      statusBadgeClassMap[normalizedStatus] ||
                      "bg-secondary text-primary-dark";
                    const nextStatus = nextStatusMap[normalizedStatus];
                    const isMovingThisCandidate =
                      moveStageMutation.isPending &&
                      moveStageMutation.variables?.candidateId === applicant.id;

                    return (
                      <article
                        key={applicant.id}
                        className="flex flex-col gap-4 rounded-3xl border border-border bg-card px-4 py-4 md:flex-row md:items-center"
                      >
                        <div className="flex min-w-0 flex-1 items-center gap-4">
                          <div className="grid h-12 w-12 place-items-center rounded-full bg-secondary text-sm font-semibold uppercase text-primary-dark">
                            {applicant.full_name
                              .split(" ")
                              .filter(Boolean)
                              .slice(0, 2)
                              .map((part) => part[0])
                              .join("") || "NA"}
                          </div>
                          <div className="min-w-0">
                            <p className="truncate text-lg font-semibold text-foreground">
                              {applicant.full_name}
                            </p>
                            <p className="truncate text-sm text-muted-foreground">
                              {applicant.email}
                            </p>
                            <p className="truncate text-xs text-muted-foreground">
                              {applicant.github_username
                                ? `GitHub: @${applicant.github_username}`
                                : "GitHub: not provided"}
                            </p>
                          </div>
                        </div>

                        <div className="w-full md:w-44">
                          <p className="text-[11px] uppercase tracking-[0.15em] text-muted-foreground">
                            Resume
                          </p>
                          <p className="mt-1 truncate text-sm font-semibold text-foreground">
                            {applicant.filename || "No file"}
                          </p>
                        </div>

                        <div className="w-full md:w-40">
                          <p className="text-[11px] uppercase tracking-[0.15em] text-muted-foreground">
                            Uploaded
                          </p>
                          <p className="mt-1 text-sm font-semibold text-primary">
                            {uploadedDateLabel}
                          </p>
                        </div>

                        <div className="w-full md:w-36">
                          <p className="text-[11px] uppercase tracking-[0.15em] text-muted-foreground">
                            Status
                          </p>
                          <span
                            className={`mt-1 inline-flex rounded-full px-3 py-1 text-xs font-semibold ${statusClass}`}
                          >
                            {toStatusLabel(applicant.status)}
                          </span>
                        </div>

                        <Link
                          to="/profile/$candidateId"
                          params={{ candidateId: String(applicant.id) }}
                          className="rounded-2xl px-4 py-2 text-sm font-semibold text-primary hover:text-primary-light"
                        >
                          View Profile
                        </Link>

                        <button
                          onClick={() => handleMoveToNextStage(applicant)}
                          disabled={!nextStatus || moveStageMutation.isPending}
                          className="rounded-2xl bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary-light disabled:cursor-not-allowed disabled:bg-secondary disabled:text-muted-foreground"
                        >
                          {isMovingThisCandidate
                            ? "Moving..."
                            : nextStatus
                              ? `Move to ${toStatusLabel(nextStatus)}`
                              : "Final Stage"}
                        </button>
                      </article>
                    );
                  })
                )}
              </div>
            </section>
          </div>
        </main>
      </div>

      {confirmMoveTarget ? (
        <div className="fixed inset-0 z-60 flex items-center justify-center bg-primary-dark/30 px-4">
          <div className="w-full max-w-md rounded-3xl border border-border bg-card p-6 shadow-2xl">
            <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              Confirm Stage Update
            </p>
            <h3 className="mt-2 text-2xl font-semibold text-foreground">
              Move Candidate Forward?
            </h3>
            <p className="mt-3 text-sm text-muted-foreground">
              <span className="font-semibold text-foreground">
                {confirmMoveTarget.candidateName}
              </span>{" "}
              will be moved to{" "}
              <span className="font-semibold text-foreground">
                {toStatusLabel(confirmMoveTarget.nextStatus)}
              </span>
              .
            </p>

            <div className="mt-6 flex items-center justify-end gap-3">
              <button
                onClick={() => setConfirmMoveTarget(null)}
                disabled={moveStageMutation.isPending}
                className="rounded-2xl border border-border bg-card px-4 py-2 text-sm font-semibold text-muted-foreground hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-60"
              >
                Cancel
              </button>
              <button
                onClick={confirmMoveToNextStage}
                disabled={moveStageMutation.isPending}
                className="rounded-2xl bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary-light disabled:cursor-not-allowed disabled:opacity-60"
              >
                {moveStageMutation.isPending ? "Moving..." : "Yes, Move"}
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {isShareDialogOpen ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-primary-dark/30 px-4"
          onClick={() => setIsShareDialogOpen(false)}
        >
          <div
            className="w-full max-w-lg rounded-3xl border border-border bg-card p-6 shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              Share Application Form
            </p>
            <h3 className="mt-2 text-2xl font-semibold text-foreground">
              Copy Public Form Link
            </h3>
            <p className="mt-2 text-sm text-muted-foreground">
              Send this link to candidates so they can apply directly.
            </p>

            <div className="mt-5 rounded-2xl border border-border bg-background px-4 py-3">
              <p className="truncate text-sm font-medium text-foreground">
                {applicationLink}
              </p>
            </div>

            {copyFeedback === "copied" ? (
              <p className="mt-3 text-sm font-semibold text-primary">
                Link copied to clipboard.
              </p>
            ) : copyFeedback === "error" ? (
              <p className="mt-3 text-sm font-semibold text-[#9a3530]">
                Could not copy automatically. Please copy the link manually.
              </p>
            ) : null}

            <div className="mt-6 flex items-center justify-end gap-3">
              <button
                onClick={() => setIsShareDialogOpen(false)}
                className="rounded-2xl border border-border bg-card px-4 py-2 text-sm font-semibold text-muted-foreground hover:border-primary hover:text-primary"
              >
                Close
              </button>
              <button
                onClick={handleCopyApplicationLink}
                className="rounded-2xl bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary-light"
              >
                Copy Link
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
