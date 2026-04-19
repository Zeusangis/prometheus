import { Link, useParams } from "@tanstack/react-router";
import { Sidebar } from "../../components/Sidebar";
import { Header } from "../../components/Header";

const interviewSummary = {
  score: 9.2,
  scoreLabel: "Exceptional",
  title: "Exceptional Technical Leadership",
  summary:
    "Jane demonstrates outstanding mastery of design systems and architectural thinking. Her ability to articulate complex design decisions during the system design phase. Her ability to articulate the gap between component flexibility and performance optimization was world class.",
  lastInterview: "Oct 24, 2023",
  keyStrengths: [
    "Mastery of Design System tokens and React implementation",
    "Strong empathetic communication during stakeholder displays",
    "Proven track record of scaling high-performance teams",
  ],
  areasForImprovement: [
    "Could refine data-driven storytelling in executive presentations",
    "Exploration of AI-integrated design workflows is still early",
  ],
  hiringRecommendation: {
    status: "Strong Hire",
    role: "Design Principal role with immediate onboarding.",
    support: "Unanimous Support",
  },
};

const archetypes = [
  "Figma Expert",
  "System Thinker",
  "Growth Focused",
  "Technical Hybrid",
  "Strategic Lead",
];

export default function InterviewSummaryPage() {
  const { candidateId } = useParams({
    from: "/profile/$candidateId/interview-summary",
  });

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        <Header />

        <main className="px-4 pb-8 pt-4 md:px-6">
          <div className="mx-auto max-w-6xl space-y-5">
            <section className="rounded-3xl border border-[#e1e6e3] bg-[#f7f9f8] p-4 sm:p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#0f6c45]">
                    Candidate Interview Intelligence
                  </p>
                  <h1 className="mt-2 text-3xl font-semibold leading-tight text-foreground">
                    Interview Summary
                  </h1>
                  <p className="mt-2 text-sm text-[#425349]">
                    Candidate ID: {candidateId}
                  </p>
                </div>

                <Link
                  to="/profile/$candidateId"
                  params={{ candidateId }}
                  className="rounded-xl border border-[#d4dfd9] bg-white px-4 py-2 text-sm font-semibold text-[#37443d]"
                >
                  Back to profile
                </Link>
              </div>
            </section>

            <section className="grid grid-cols-1 gap-5 xl:grid-cols-[2fr_1fr]">
              <div className="flex flex-col gap-5">
                <article className="flex flex-col gap-6 rounded-3xl border border-[#e1e6e3] bg-[#f8faf9] p-6 sm:flex-row sm:items-start">
                  <div className="flex shrink-0 flex-col items-center gap-2">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#0f6c45]">
                      Overall Score
                    </p>
                    <div className="mt-2 flex h-24 w-24 items-center justify-center rounded-full border-4 border-[#dff0e5] bg-[#f0f5f2]">
                      <div className="text-center">
                        <p className="text-3xl font-bold text-[#0f6c45]">
                          {interviewSummary.score}
                        </p>
                        <p className="text-[9px] font-semibold uppercase tracking-[0.15em] text-[#5b7a68]">
                          {interviewSummary.scoreLabel}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="flex-1">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#0f6c45]">
                      Interview Summary
                    </p>
                    <h2 className="mt-3 text-2xl font-semibold text-[#1d2a23]">
                      {interviewSummary.title}
                    </h2>
                    <p className="mt-2 text-sm text-[#5b6a62]">
                      {interviewSummary.summary}
                    </p>
                    <p className="mt-3 text-xs text-[#7d8b83]">
                      Last Interview: {interviewSummary.lastInterview}
                    </p>
                  </div>
                </article>

                <article className="rounded-3xl border border-[#e1e6e3] bg-[#f8faf9] p-6">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#0f6c45]">
                    Key Strengths
                  </p>
                  <ul className="mt-4 space-y-3">
                    {interviewSummary.keyStrengths.map((strength, idx) => (
                      <li
                        key={idx}
                        className="flex gap-3 text-sm text-[#2f3b34]"
                      >
                        <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#0f6c45]" />
                        <span>{strength}</span>
                      </li>
                    ))}
                  </ul>
                </article>

                <article className="rounded-3xl border border-[#e1e6e3] bg-[#f8faf9] p-6">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#213229]">
                    Areas for Improvement
                  </p>
                  <ul className="mt-4 space-y-3">
                    {interviewSummary.areasForImprovement.map((area, idx) => (
                      <li
                        key={idx}
                        className="flex gap-3 text-sm text-[#2f3b34]"
                      >
                        <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#d4dfd9]" />
                        <span>{area}</span>
                      </li>
                    ))}
                  </ul>
                </article>

                <article className="rounded-3xl bg-[#0f6c45] p-6 text-white">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.2em]">
                        Hiring Recommendation
                      </p>
                      <h3 className="mt-3 text-2xl font-bold">
                        {interviewSummary.hiringRecommendation.status}
                      </h3>
                      <p className="mt-2 text-sm">
                        Recommended for{" "}
                        {interviewSummary.hiringRecommendation.role}
                      </p>
                    </div>
                    <div className="shrink-0 text-right">
                      <p className="text-xs font-semibold uppercase tracking-[0.15em]">
                        {interviewSummary.hiringRecommendation.support}
                      </p>
                    </div>
                  </div>
                </article>
              </div>

              <div className="space-y-5">
                <article className="rounded-3xl border border-[#e1e6e3] bg-[#f8faf9] p-6">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#213229]">
                    Contact & Links
                  </p>
                  <div className="mt-4 space-y-4 text-sm">
                    <div>
                      <p className="text-[10px] uppercase tracking-[0.15em] text-[#7d8b83]">
                        Email
                      </p>
                      <p className="mt-1 font-semibold">jane.s@design.io</p>
                    </div>
                    <div>
                      <p className="text-[10px] uppercase tracking-[0.15em] text-[#7d8b83]">
                        Portfolio
                      </p>
                      <p className="mt-1 font-semibold">sutherland.design</p>
                    </div>
                    <div>
                      <p className="text-[10px] uppercase tracking-[0.15em] text-[#7d8b83]">
                        Social
                      </p>
                      <p className="mt-1 font-semibold">
                        LinkedIn • GitHub • Dribbble
                      </p>
                    </div>
                  </div>
                </article>

                <article className="rounded-3xl border border-[#e1e6e3] bg-[#f8faf9] p-6">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#213229]">
                    Candidate Archetype
                  </p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {archetypes.map((tag, idx) => (
                      <span
                        key={tag}
                        className={`rounded-full px-3 py-1.5 text-xs font-semibold ${
                          idx < 2
                            ? "bg-[#dff0e5] text-[#0f6c45]"
                            : "bg-[#ecefef] text-[#4d5a53]"
                        }`}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </article>
              </div>
            </section>
          </div>
        </main>
      </div>
    </div>
  );
}
