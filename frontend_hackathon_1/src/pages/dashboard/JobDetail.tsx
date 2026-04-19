import { Link, useParams } from "@tanstack/react-router";
import { Sidebar } from "../../components/Sidebar";
import { Header } from "../../components/Header";

const pipelineStats = [
  { label: "Sourcing", value: 124, progress: 78 },
  { label: "Screening", value: 48, progress: 46 },
  { label: "Verification", value: 12, progress: 24 },
  { label: "Interview", value: 8, progress: 16 },
  { label: "Offer", value: 2, progress: 10, highlighted: true },
];

const applicants = [
  {
    id: "jane-sutherland",
    name: "Jane Sutherland",
    role: "Senior UI/UX Designer at EcoCorp",
    match: 98,
    stage: "Verification",
    avatar:
      "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=96&h=96&fit=crop&crop=face",
    moveDisabled: false,
  },
  {
    id: "marcus-rivers",
    name: "Marcus Rivers",
    role: "Product Designer at Bloom Metrics",
    match: 84,
    stage: "Screening",
    avatar:
      "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=96&h=96&fit=crop&crop=face",
    moveDisabled: false,
  },
  {
    id: "lila-aris",
    name: "Lila Aris",
    role: "Mid-Weight Designer at Studio Leaf",
    match: 62,
    stage: "Sourcing",
    avatar:
      "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=96&h=96&fit=crop&crop=face",
    moveDisabled: true,
  },
];

export default function JobDetail() {
  const { jobId } = useParams({ from: "/dashboard/$jobId" });

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
                <div className="flex items-center gap-3 text-sm">
                  <span className="rounded-full bg-primary-lighter/35 px-3 py-1 text-xs font-semibold text-primary-dark">
                    Active
                  </span>
                  <span className="text-muted-foreground">• Remote</span>
                </div>

                <h1 className="mt-2 text-4xl leading-tight font-semibold text-foreground">
                  Senior Product Designer
                </h1>

                <p className="mt-3 text-muted-foreground">
                  Posted 12 days ago • Hiring Team: Design Ops • Job ID: {jobId}
                </p>
              </div>

              <div className="flex flex-wrap gap-3">
                <button className="rounded-2xl border border-border bg-card px-5 py-3 text-sm font-semibold text-primary hover:border-primary">
                  Edit Job Description
                </button>
                <button className="rounded-2xl bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground hover:bg-primary-light">
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
                {applicants.map((applicant) => (
                  <article
                    key={applicant.id}
                    className="flex flex-col gap-4 rounded-3xl border border-border bg-card px-4 py-4 md:flex-row md:items-center"
                  >
                    <div className="flex min-w-0 flex-1 items-center gap-4">
                      <img
                        src={applicant.avatar}
                        alt={applicant.name}
                        className="h-12 w-12 rounded-full object-cover"
                      />
                      <div className="min-w-0">
                        <p className="truncate text-lg font-semibold text-foreground">
                          {applicant.name}
                        </p>
                        <p className="truncate text-sm text-muted-foreground">
                          {applicant.role}
                        </p>
                      </div>
                    </div>

                    <div className="w-full md:w-40">
                      <p className="text-[11px] uppercase tracking-[0.15em] text-muted-foreground">
                        AI Match
                      </p>
                      <div className="mt-1 h-1.5 w-full rounded-full bg-secondary">
                        <div
                          className="h-1.5 rounded-full bg-primary"
                          style={{ width: `${applicant.match}%` }}
                        />
                      </div>
                      <p className="mt-1 text-sm font-semibold text-primary">
                        {applicant.match}%
                      </p>
                    </div>

                    <div className="w-full md:w-36">
                      <p className="text-[11px] uppercase tracking-[0.15em] text-muted-foreground">
                        Current Stage
                      </p>
                      <span className="mt-1 inline-flex rounded-full bg-secondary px-3 py-1 text-xs font-semibold text-primary-dark">
                        {applicant.stage}
                      </span>
                    </div>

                    <Link
                      to="/profile/$candidateId"
                      params={{ candidateId: applicant.id }}
                      className="rounded-2xl px-4 py-2 text-sm font-semibold text-primary hover:text-primary-light"
                    >
                      View Profile
                    </Link>

                    <button
                      disabled={applicant.moveDisabled}
                      className="rounded-2xl bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary-light disabled:cursor-not-allowed disabled:bg-secondary disabled:text-muted-foreground"
                    >
                      Move to Next Stage
                    </button>
                  </article>
                ))}
              </div>

              <div className="mt-8 flex justify-center">
                <button className="rounded-full border border-border bg-card px-8 py-3 font-medium text-foreground hover:border-primary">
                  Load 24 more applicants
                </button>
              </div>
            </section>
          </div>
        </main>
      </div>
    </div>
  );
}
