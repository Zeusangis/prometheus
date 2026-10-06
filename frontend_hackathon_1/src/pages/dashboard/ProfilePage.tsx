import { useState } from "react";
import type { ReactNode } from "react";
import { Link, useParams } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Sidebar } from "../../components/Sidebar";
import { Header } from "../../components/Header";
import ResumeSection, { formatDate, formatLabel } from "./ResumeSection";
import GitHubSection from "./GitHubSection";
import {
  getCandidateAnalysis,
  getCandidateProfile,
  getCandidateStageEvents,
  retryCandidateAnalysis,
} from "../../api/apply";
import type { StageEvent } from "../../api/apply";
import { getJobById, moveCandidateToNextStep } from "../../api/jobs";

const PROFILE_TABS = [
  "Overview",
  "Resume",
  "GitHub Evidence",
  "Scores & Analysis",
  "Activity",
] as const;

const STAGE_BADGE: Record<string, string> = {
  screening: "bg-secondary text-primary-dark",
  interview_scheduled: "bg-[#daf2e2] text-[#246747]",
  interview_completed: "bg-[#dcecff] text-[#254f8d]",
  offer_made: "bg-[#efe6ff] text-[#4f3a9e]",
  hired: "bg-[#d8f6e4] text-[#1c7f4d]",
  rejected: "bg-[#ffe3e0] text-[#9a3530]",
};

const TERMINAL_STAGES = new Set(["hired", "rejected"]);
const RETRYABLE_ANALYSIS = new Set(["failed", "enqueue_failed", "partial"]);

function errorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

function describeStageEvent(event: StageEvent) {
  if (event.event_type === "analysis_retried") {
    return event.previous_analysis_status
      ? `Analysis retry requested (was ${formatLabel(event.previous_analysis_status)})`
      : "Analysis retry requested";
  }
  const from = event.from_stage ? formatLabel(event.from_stage) : "an unknown stage";
  const to = event.to_stage ? formatLabel(event.to_stage) : "an unknown stage";
  return `Moved from ${from} to ${to}`;
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <p className="text-[10px] uppercase tracking-[0.15em] text-muted-foreground">
        {label}
      </p>
      <p className="mt-1 break-words text-sm font-semibold">{value}</p>
    </div>
  );
}

function Panel({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <article className="rounded-2xl border border-border bg-card p-5">
      <h2 className="text-lg font-semibold">{title}</h2>
      <div className="mt-3 space-y-3 text-sm">{children}</div>
    </article>
  );
}

export default function ProfilePage() {
  const { candidateId } = useParams({ from: "/profile/$candidateId" });
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] =
    useState<(typeof PROFILE_TABS)[number]>("Overview");
  const [actionError, setActionError] = useState<string | null>(null);
  const [pendingStage, setPendingStage] = useState<string | null>(null);

  const profileQuery = useQuery({
    queryKey: ["candidate", candidateId],
    queryFn: () => getCandidateProfile(candidateId),
  });

  const analysisQuery = useQuery({
    queryKey: ["candidate-analysis", candidateId],
    queryFn: () => getCandidateAnalysis(candidateId),
  });

  const auditQuery = useQuery({
    queryKey: ["candidate-stage-events", candidateId],
    queryFn: () => getCandidateStageEvents(candidateId),
  });

  const jobQuery = useQuery({
    queryKey: ["job-detail", profileQuery.data?.job_id],
    queryFn: () => getJobById(String(profileQuery.data?.job_id)),
    enabled: profileQuery.data?.job_id != null,
  });

  const candidate = profileQuery.data;
  const analysis = analysisQuery.data;

  const retryMutation = useMutation({
    mutationFn: () => retryCandidateAnalysis(candidateId),
    onSuccess: async () => {
      setActionError(null);
      await queryClient.invalidateQueries({
        queryKey: ["candidate-analysis", candidateId],
      });
      await queryClient.invalidateQueries({
        queryKey: ["candidate", candidateId],
      });
      await queryClient.invalidateQueries({
        queryKey: ["candidate-stage-events", candidateId],
      });
    },
    onError: (error) =>
      setActionError(errorMessage(error, "Analysis retry could not be queued.")),
  });

  const stageMutation = useMutation({
    mutationFn: (nextStatus: string) =>
      moveCandidateToNextStep({
        jobId: String(candidate?.job_id ?? ""),
        candidateId: candidate?.id ?? 0,
        nextStatus,
      }),
    onSuccess: async () => {
      setPendingStage(null);
      setActionError(null);
      await queryClient.invalidateQueries({
        queryKey: ["candidate", candidateId],
      });
      await queryClient.invalidateQueries({
        queryKey: ["candidate-stage-events", candidateId],
      });
    },
    onError: (error) => {
      setPendingStage(null);
      setActionError(errorMessage(error, "Stage change failed."));
    },
  });

  const canChangeStage = Boolean(candidate && candidate.job_id !== null);
  const nextStage = candidate?.allowed_actions.find(
    (action) => action !== "rejected",
  );
  const canReject = Boolean(candidate?.allowed_actions.includes("rejected"));
  const analysisIsRetryable = Boolean(
    analysis && RETRYABLE_ANALYSIS.has(analysis.status),
  );

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        <Header />

        <main className="px-4 pb-8 pt-4 md:px-6">
          <div className="mx-auto max-w-6xl space-y-5">
            {profileQuery.isLoading ? (
              <p className="rounded-2xl border border-border bg-card px-4 py-5 text-sm text-muted-foreground">
                Loading candidate…
              </p>
            ) : profileQuery.error ? (
              <p
                role="alert"
                className="rounded-2xl border border-[#ffe3e0] bg-[#fff6f5] px-4 py-5 text-sm text-[#9a3530]"
              >
                {errorMessage(
                  profileQuery.error,
                  "Failed to load this candidate.",
                )}
              </p>
            ) : candidate ? (
              <>
                <section className="rounded-3xl border border-border bg-card p-4 sm:p-5">
                  <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                    <div className="min-w-0">
                      <h1 className="break-words text-3xl font-semibold leading-tight text-foreground">
                        {candidate.full_name || `Candidate #${candidate.id}`}
                      </h1>
                      <p className="mt-1 break-words text-base text-muted-foreground">
                        {candidate.email || "No email on record"} ·{" "}
                        {candidate.filename || "No resume file"}
                      </p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        GitHub entity:{" "}
                        {candidate.github_username
                          ? `@${candidate.github_username}`
                          : "not provided"}
                      </p>
                      <div className="mt-2 flex flex-wrap gap-2 text-xs font-semibold">
                        <span
                          className={`rounded-full px-2 py-1 ${
                            STAGE_BADGE[candidate.status] ??
                            "bg-secondary text-primary-dark"
                          }`}
                        >
                          {formatLabel(candidate.status)}
                        </span>
                        <span className="rounded-full bg-secondary px-2 py-1 text-primary-dark">
                          Analysis: {formatLabel(candidate.analysis_status)}
                        </span>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      {canChangeStage && nextStage ? (
                        <button
                          onClick={() => {
                            setActionError(null);
                            setPendingStage(nextStage);
                          }}
                          disabled={stageMutation.isPending}
                          className="rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary-light disabled:cursor-not-allowed disabled:bg-secondary disabled:text-muted-foreground"
                        >
                          Move to {formatLabel(nextStage)}
                        </button>
                      ) : null}
                      {canChangeStage && canReject ? (
                        <button
                          onClick={() => {
                            setActionError(null);
                            setPendingStage("rejected");
                          }}
                          disabled={stageMutation.isPending}
                          className="rounded-xl bg-[#ffd9d6] px-4 py-2 text-sm font-semibold text-[#9a3530] disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          Reject
                        </button>
                      ) : null}
                      {TERMINAL_STAGES.has(candidate.status) ? (
                        <span className="rounded-xl border border-border px-4 py-2 text-sm text-muted-foreground">
                          {formatLabel(candidate.status)} is a terminal stage.
                        </span>
                      ) : null}
                    </div>
                  </div>

                  {actionError ? (
                    <p
                      role="alert"
                      className="mt-3 rounded-xl border border-[#ffe3e0] bg-[#fff6f5] px-4 py-3 text-sm text-[#9a3530]"
                    >
                      {actionError}
                    </p>
                  ) : null}

                  {pendingStage ? (
                    <div className="mt-3 flex flex-wrap items-center gap-3 rounded-xl border border-[#d4dfd9] bg-secondary/40 px-4 py-3 text-sm">
                      <span>
                        Confirm server-authorized stage change to{" "}
                        <strong>{formatLabel(pendingStage)}</strong> for{" "}
                        {candidate.full_name || `candidate #${candidate.id}`}?
                      </span>
                      <button
                        onClick={() => stageMutation.mutate(pendingStage)}
                        disabled={stageMutation.isPending}
                        className="rounded-lg bg-primary px-3 py-1.5 font-semibold text-primary-foreground disabled:opacity-60"
                      >
                        {stageMutation.isPending ? "Moving…" : "Confirm"}
                      </button>
                      <button
                        onClick={() => setPendingStage(null)}
                        className="rounded-lg border border-border px-3 py-1.5 font-semibold"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : null}

                  <div className="mt-5 flex flex-wrap gap-5 border-b border-border pb-3 text-sm">
                    {PROFILE_TABS.map((tab) => (
                      <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`font-medium ${
                          tab === activeTab
                            ? "border-b-2 border-primary pb-2 text-primary"
                            : "text-muted-foreground"
                        }`}
                      >
                        {tab}
                      </button>
                    ))}
                  </div>
                </section>

                {analysisQuery.isLoading ? (
                  <p className="rounded-2xl border border-border bg-card px-4 py-5 text-sm text-muted-foreground">
                    Loading saved analysis…
                  </p>
                ) : analysisQuery.error ? (
                  <p
                    role="alert"
                    className="rounded-2xl border border-[#ffe3e0] bg-[#fff6f5] px-4 py-5 text-sm text-[#9a3530]"
                  >
                    {errorMessage(
                      analysisQuery.error,
                      "Failed to load saved analysis.",
                    )}
                  </p>
                ) : null}

                {activeTab === "Overview" ? (
                  <section className="grid grid-cols-1 gap-5 lg:grid-cols-2">
                    <Panel title="Submission">
                      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                        <Field
                          label="Full name"
                          value={candidate.full_name || "Not recorded"}
                        />
                        <Field
                          label="Email"
                          value={candidate.email || "Not recorded"}
                        />
                        <Field
                          label="GitHub entity"
                          value={
                            candidate.github_username
                              ? `@${candidate.github_username}`
                              : "Not provided"
                          }
                        />
                        <Field
                          label="Resume file"
                          value={candidate.filename || "Not recorded"}
                        />
                        <Field
                          label="Submitted"
                          value={formatDate(candidate.uploaded_at)}
                        />
                        <Field
                          label="Analysis status"
                          value={formatLabel(candidate.analysis_status)}
                        />
                      </div>
                      {candidate.job_id !== null ? (
                        <Link
                          to="/dashboard/$jobId"
                          params={{ jobId: String(candidate.job_id) }}
                          className="inline-block font-semibold text-primary hover:text-primary-light"
                        >
                          {jobQuery.data?.title
                            ? `Applied for ${jobQuery.data.title}`
                            : `View job ${candidate.job_id}`}
                        </Link>
                      ) : (
                        <p className="text-muted-foreground">
                          This candidate is not linked to a job, so stage
                          changes are unavailable.
                        </p>
                      )}
                    </Panel>

                    <Panel title="Analysis and review">
                      <p className="text-muted-foreground">
                        Resume and GitHub results are independent provider
                        evidence for human review. This profile never shows
                        invented scores, skills, or recommendations.
                      </p>
                      <p>
                        Overall status:{" "}
                        <strong>
                          {analysis
                            ? formatLabel(analysis.status)
                            : "No saved analysis"}
                        </strong>
                      </p>
                      {analysis?.error_message ? (
                        <p
                          role="status"
                          className="rounded-lg bg-secondary p-3 text-muted-foreground"
                        >
                          {analysis.error_message}
                        </p>
                      ) : null}
                      {analysisIsRetryable ? (
                        <div className="space-y-2">
                          <button
                            onClick={() => retryMutation.mutate()}
                            disabled={retryMutation.isPending}
                            className="rounded-lg bg-primary px-4 py-2 font-semibold text-primary-foreground disabled:opacity-60"
                          >
                            {retryMutation.isPending
                              ? "Queueing…"
                              : "Retry failed analysis"}
                          </button>
                          <p className="text-xs text-muted-foreground">
                            Retry re-queues only the components that are not
                            complete; completed results are preserved.
                          </p>
                        </div>
                      ) : (
                        <p className="text-xs text-muted-foreground">
                          Retry is offered only for failed, enqueue_failed or
                          partial analysis.
                        </p>
                      )}
                    </Panel>
                  </section>
                ) : null}

                {activeTab === "Resume" ? (
                  <section className="space-y-4">
                    <ResumeSection data={analysis?.resume ?? null} />
                    <details className="rounded-2xl border border-border bg-card p-5">
                      <summary className="cursor-pointer text-lg font-semibold">
                        Extracted resume text
                      </summary>
                      <p className="mt-2 text-sm text-muted-foreground">
                        Exactly the text the server read from the uploaded PDF and sent
                        to the analysis provider. It is shown so you can verify the
                        evidence yourself; a PDF with no extractable text cannot be
                        analysed.
                      </p>
                      {analysis?.resume_text ? (
                        <pre className="mt-3 max-h-96 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-secondary/50 p-3 text-xs">
                          {analysis.resume_text}
                        </pre>
                      ) : (
                        <p className="mt-3 text-sm text-muted-foreground">
                          No text has been extracted yet. It appears here once the
                          resume is read, even when the analysis itself fails.
                        </p>
                      )}
                    </details>
                  </section>
                ) : null}

                {activeTab === "GitHub Evidence" ? (
                  <GitHubSection
                    data={analysis?.github ?? null}
                    requested={Boolean(
                      candidate.github_username || analysis?.github,
                    )}
                  />
                ) : null}

                {activeTab === "Scores & Analysis" ? (
                  <section className="space-y-4">
                    <Panel title="Resume ATS evidence">
                      <p>
                        {analysis?.resume?.status === "complete" &&
                        analysis.resume.ats_score !== null
                          ? `${analysis.resume.ats_score} / 100`
                          : "Not measured"}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Resume ATS score from the saved job-aware analysis.
                      </p>
                    </Panel>

                    <Panel title="Sampled repository scores">
                      {analysis?.github?.repositories.length ? (
                        <div className="overflow-x-auto">
                          <table className="w-full min-w-80 border-collapse text-left">
                            <thead>
                              <tr className="text-xs uppercase tracking-[0.15em] text-muted-foreground">
                                <th className="py-2">Repository</th>
                                <th className="py-2">Score</th>
                                <th className="py-2">Enabled weight covered</th>
                              </tr>
                            </thead>
                            <tbody>
                              {analysis.github.repositories.map((repo) => {
                                const coverage =
                                  repo.metrics?.aggregation?.weight_coverage;
                                return (
                                  <tr
                                    key={repo.repo_name}
                                    className="border-t border-border"
                                  >
                                    <td className="break-words py-2 pr-3 text-sm">
                                      {repo.repo_name}
                                    </td>
                                    <td className="py-2 pr-3 text-sm font-semibold">
                                      {repo.score === null
                                        ? "Not scored"
                                        : `${repo.score} / 100`}
                                    </td>
                                    <td className="py-2 text-sm">
                                      {coverage == null
                                        ? "Not measured"
                                        : `${Math.round(coverage * 100)}%`}
                                    </td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <p className="text-muted-foreground">
                          No repository scores are saved for this candidate.
                        </p>
                      )}
                      <p className="text-xs text-muted-foreground">
                        Resume ATS scores and sampled repository scores are
                        unrelated scales and are never combined into a single
                        candidate score or ranking.
                      </p>
                    </Panel>
                  </section>
                ) : null}

                {activeTab === "Activity" ? (
                  <section className="space-y-4">
                    <Panel title="Audit trail">
                      <p className="text-muted-foreground">
                        Append-only record of every stage change and analysis
                        retry for this candidate. Entries are written by the
                        server and cannot be edited or deleted.
                      </p>
                      {auditQuery.isLoading ? (
                        <p className="text-muted-foreground">
                          Loading audit trail…
                        </p>
                      ) : auditQuery.error ? (
                        <p
                          role="alert"
                          className="rounded-lg border border-[#ffe3e0] bg-[#fff6f5] px-3 py-2 text-[#9a3530]"
                        >
                          {errorMessage(
                            auditQuery.error,
                            "Failed to load the audit trail.",
                          )}
                        </p>
                      ) : auditQuery.data && auditQuery.data.length ? (
                        <ol className="space-y-3">
                          {auditQuery.data.map((event) => (
                            <li
                              key={event.id}
                              className="border-l-2 border-border pl-3"
                            >
                              <p className="font-semibold">
                                {describeStageEvent(event)}
                              </p>
                              <p className="text-xs text-muted-foreground">
                                {formatDate(event.created_at)} ·{" "}
                                {event.actor_email
                                  ? `by ${event.actor_email}`
                                  : "actor not recorded"}
                              </p>
                            </li>
                          ))}
                        </ol>
                      ) : (
                        <p className="text-muted-foreground">
                          No stage changes or analysis retries have been
                          recorded for this candidate yet.
                        </p>
                      )}
                    </Panel>
                  </section>
                ) : null}
              </>
            ) : (
              <p className="rounded-2xl border border-border bg-card px-4 py-5 text-sm text-muted-foreground">
                No candidate data is available.
              </p>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
