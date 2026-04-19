import { useState } from "react";
import { Link, useParams } from "@tanstack/react-router";
import { Sidebar } from "../../components/Sidebar";
import { Header } from "../../components/Header";
import ResumeSection from "./ResumeSection";
import type { ResumeAnalysisData } from "./ResumeSection";

const PROFILE_TABS = [
  "Overview",
  "Resume",
  "Verified Skills",
  "Interview Summary",
  "Scores & Analysis",
] as const;

const skills = [
  { name: "Figma & Prototyping", score: 98 },
  { name: "Design Systems", score: 95 },
  { name: "React / Tailwind CSS", score: 82 },
  { name: "User Research", score: 88 },
];

const archetypes = [
  "Figma Expert",
  "System Thinker",
  "Growth Focused",
  "Technical Hybrid",
  "Strategic Lead",
];

const resumeAnalysisData: ResumeAnalysisData = {
  ats_score: 75,
  breakdown: {
    achievements: 6,
    completeness: 9,
    education: 9,
    experience_relevance: 12,
    formatting: 9,
    keyword_match: 18,
    skills_alignment: 12,
  },
  final_verdict:
    "This is a strong entry-level resume for a student, highlighted by a perfect GPA and relevant projects. The candidate demonstrates proficiency in the Python ecosystem. However, to pass more rigorous ATS filters for Backend or Data Science roles, the candidate must add database-related keywords (SQL) and focus on demonstrating the measurable impact of their technical projects.",
  missing_keywords: [
    "SQL",
    "PostgreSQL",
    "Git",
    "Docker",
    "REST API",
    "Unit Testing",
    "Agile",
    "CI/CD",
    "AWS",
    "PyTorch",
    "NoSQL",
  ],
  projects: [
    "Data Augmentation on Geospatial Data",
    "Exploring Patterns in Mobile Data for Smarter Decisions",
    "AI Fitness Chatbot",
  ],
  top_improvements: [
    "Include SQL and specific database names like PostgreSQL or MongoDB in the skills section.",
    "Quantify project results, such as 'Increased data processing speed by 30% through multithreading'.",
    "Add version control tools like Git and GitHub explicitly under 'Libraries & Tools'.",
    "Reframe Helpdesk duties to emphasize any automation or scripting performed.",
    "Expand the 'Backend Developer Intern' section with more specific technologies used for caching and database design.",
  ],
  weak_areas: [
    "Short duration of the primary technical internship (3 months).",
    "IT Helpdesk experience is support-oriented rather than development-oriented.",
    "Lack of quantifiable metrics (percentages, time saved) in the project descriptions.",
    "Missing fundamental database management keywords like SQL.",
  ],
};

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

export default function ProfilePage() {
  const { candidateId } = useParams({ from: "/profile/$candidateId" });
  const [activeTab, setActiveTab] =
    useState<(typeof PROFILE_TABS)[number]>("Overview");

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        <Header />

        <main className="px-4 pb-8 pt-4 md:px-6">
          <div className="mx-auto max-w-6xl space-y-5">
            <section className="rounded-3xl border border-[#e1e6e3] bg-[#f7f9f8] p-4 sm:p-5">
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div className="flex items-center gap-3">
                  <div>
                    <h1 className="text-3xl font-semibold leading-tight text-foreground">
                      Jane Sutherland
                    </h1>
                    <p className="mt-1 text-base text-[#425349]">
                      Senior UI/UX Designer • London, United Kingdom
                    </p>
                    <div className="mt-2 flex flex-wrap gap-2 text-xs font-semibold">
                      <span className="rounded-full bg-[#cdebd8] px-2 py-1 text-[#0f6c45]">
                        High Match
                      </span>
                      <span className="rounded-full bg-[#daf2e2] px-2 py-1 text-[#246747]">
                        Verification Complete
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Link
                    to="/profile/$candidateId/interview-summary"
                    params={{ candidateId }}
                    className="rounded-xl border border-[#d4dfd9] bg-white px-4 py-2 text-sm font-semibold text-[#37443d]"
                  >
                    Interview Summary Page
                  </Link>
                  <button className="rounded-xl border border-[#d4dfd9] bg-white px-4 py-2 text-sm font-semibold text-[#37443d]">
                    Share Profile
                  </button>
                  <button className="rounded-xl bg-[#ffd9d6] px-4 py-2 text-sm font-semibold text-[#9a3530]">
                    Reject
                  </button>
                  <button className="rounded-xl bg-[#0f6c45] px-4 py-2 text-sm font-semibold text-white">
                    Move to Next Stage
                  </button>
                </div>
              </div>

              <div className="mt-6 flex flex-wrap gap-5 border-b border-[#dfe7e2] pb-3 text-sm">
                {PROFILE_TABS.map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`font-medium ${
                      tab === activeTab
                        ? "border-b-2 border-[#0f6c45] pb-2 text-[#0f6c45]"
                        : "text-[#5b6a62]"
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>
            </section>

            {activeTab === "Resume" ? (
              <ResumeSection data={resumeAnalysisData} />
            ) : activeTab === "Interview Summary" ? (
              <section className="grid grid-cols-1 gap-5 xl:grid-cols-[2fr_1fr]">
                {/* Interview Summary with Score */}
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
                      <h3 className="mt-3 text-2xl font-semibold text-[#1d2a23]">
                        {interviewSummary.title}
                      </h3>
                      <p className="mt-2 text-sm text-[#5b6a62]">
                        {interviewSummary.summary}
                      </p>
                      <p className="mt-3 text-xs text-[#7d8b83]">
                        Last Interview: {interviewSummary.lastInterview}
                      </p>
                    </div>
                  </article>

                  {/* Key Strengths */}
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

                  {/* Areas for Improvement */}
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

                  {/* Hiring Recommendation */}
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

                {/* Right Sidebar */}
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

                  <article className="rounded-3xl border border-[#e1e6e3] bg-[#f8faf9] p-6">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#213229]">
                      Engagement Score
                    </p>

                    <div className="mx-auto mt-5 grid h-36 w-36 place-items-center rounded-full border-10 border-[#d8e6df] border-t-[#0f6c45]">
                      <div className="text-center">
                        <p className="text-4xl font-bold text-[#1d2a23]">9.0</p>
                        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#6b7b72]">
                          Exceptional
                        </p>
                      </div>
                    </div>

                    <p className="mt-4 text-center text-sm text-[#5a6a61]">
                      Jane has completed all preliminary screening rounds with
                      top-tier scores in communication.
                    </p>
                  </article>
                </div>
              </section>
            ) : (
              <section className="grid grid-cols-1 gap-5 xl:grid-cols-[2fr_1fr]">
                <article className="rounded-3xl border border-[#e1e6e3] bg-[#f8faf9] p-6">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#0f6c45]">
                    AI Candidate Summary
                  </p>
                  <p className="mt-4 text-2xl leading-relaxed text-[#27342d]">
                    "Jane stands out as a rare 98% match due to her extensive
                    experience scaling design systems at Stripe and Dropbox. Her
                    GitHub contributions show a deep technical understanding of
                    React-based component libraries, bridging the gap between
                    high-end UI craft and scalable production code. She is
                    uniquely suited for the Design Principal role."
                  </p>
                </article>

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

                <div className="space-y-5">
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

                  <article className="rounded-3xl border border-[#e1e6e3] bg-[#f8faf9] p-6">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#213229]">
                      Engagement Score
                    </p>

                    <div className="mx-auto mt-5 grid h-36 w-36 place-items-center rounded-full border-10 border-[#d8e6df] border-t-[#0f6c45]">
                      <div className="text-center">
                        <p className="text-4xl font-bold text-[#1d2a23]">9.0</p>
                        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#6b7b72]">
                          Exceptional
                        </p>
                      </div>
                    </div>

                    <p className="mt-4 text-center text-sm text-[#5a6a61]">
                      Jane has completed all preliminary screening rounds with
                      top-tier scores in communication.
                    </p>
                  </article>
                </div>

                <article className="rounded-3xl border border-[#e1e6e3] bg-[#f8faf9] p-6 xl:col-span-1">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#0f6c45]">
                      Verified Proficiency Heatmap
                    </p>
                    <p className="text-xs text-[#607066]">
                      ● GitHub Signal • ● AI Assessment
                    </p>
                  </div>

                  <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
                    {skills.map((skill) => (
                      <div key={skill.name}>
                        <div className="mb-1 flex items-center justify-between text-sm">
                          <p className="font-medium text-[#2f3b34]">
                            {skill.name}
                          </p>
                          <p className="font-semibold text-[#0f6c45]">
                            {skill.score}%
                          </p>
                        </div>
                        <div className="h-2 rounded-full bg-[#deebe4]">
                          <div
                            className="h-2 rounded-full bg-[#0f6c45]"
                            style={{ width: `${skill.score}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </article>
              </section>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
