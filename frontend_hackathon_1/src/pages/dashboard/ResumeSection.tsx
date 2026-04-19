export type ResumeAnalysisData = {
  ats_score: number;
  breakdown: {
    achievements: number;
    completeness: number;
    education: number;
    experience_relevance: number;
    formatting: number;
    keyword_match: number;
    skills_alignment: number;
  };
  final_verdict: string;
  missing_keywords: string[];
  projects: string[];
  top_improvements: string[];
  weak_areas: string[];
};

type ResumeSectionProps = {
  data: ResumeAnalysisData;
};

function repoSlug(name: string) {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

function formatLabel(key: string) {
  return key.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

export default function ResumeSection({ data }: ResumeSectionProps) {
  const breakdownEntries = Object.entries(data.breakdown);
  const totalScore = breakdownEntries.reduce(
    (sum, [, value]) => sum + value,
    0,
  );
  const scoreOutOf = 100;
  const keywordsFound = Math.max(0, 20 - data.missing_keywords.length);
  const semanticMatch = Math.round((data.breakdown.keyword_match / 20) * 100);
  const verdictExcerpt = data.final_verdict
    .split(". ")
    .slice(0, 2)
    .join(". ")
    .trim();

  const repositories = data.projects.slice(0, 2).map((project, index) => ({
    name: repoSlug(project),
    score: (7.6 - index * 0.6).toFixed(1),
    pro:
      index === 0
        ? "Strong domain-oriented architecture and clean technical decomposition."
        : "Good implementation quality with practical and readable project structure.",
    redFlag:
      index === 0
        ? "Missing explicit testing depth and visible CI quality signals."
        : "Limited measurable adoption and no clear deployment metrics.",
  }));

  return (
    <section className="space-y-4">
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.15fr_1fr]">
        <article className="flex min-h-38 w-full items-center rounded-3xl border border-[#dce5df] bg-[#0f6c45] p-5 text-white shadow-[0_14px_24px_-18px_rgba(15,108,69,0.8)]">
          <div className="flex items-center gap-4 md:gap-5">
            <div className="grid h-22 w-22 place-items-center rounded-full border-6 border-white/45 border-t-white">
              <p className="text-3xl font-bold">{data.ats_score}</p>
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-white/80">
                Combined Intel Score
              </p>
              <p className="mt-2 max-w-xs text-sm text-white/90">
                Aggregated ATS and GitHub performance metrics.
              </p>
            </div>
          </div>
        </article>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <article className="grid min-h-38 place-items-center rounded-2xl border border-[#dce5df] bg-[#f8faf9] p-4 text-center">
            <div>
              <p className="text-[11px] uppercase tracking-[0.16em] text-[#6b7a72]">
                Repositories
              </p>
              <p className="mt-2 text-5xl font-bold text-[#134830]">47</p>
            </div>
          </article>

          <article className="grid min-h-38 place-items-center rounded-2xl bg-[#0f6c45] p-4 text-center text-white">
            <div>
              <p className="text-[11px] uppercase tracking-[0.16em] text-white/80">
                Total Commits
              </p>
              <p className="mt-2 text-4xl font-bold">15k+</p>
            </div>
          </article>

          <article className="grid min-h-38 place-items-center rounded-2xl border border-[#dce5df] bg-[#f8faf9] p-4 text-center">
            <div>
              <p className="text-[11px] uppercase tracking-[0.16em] text-[#6b7a72]">
                Stars
              </p>
              <p className="mt-2 text-5xl font-bold text-[#134830]">25</p>
            </div>
          </article>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1.05fr_1.3fr]">
        <div className="space-y-5">
          <article className="rounded-3xl border border-[#dce5df] bg-[#f8faf9] p-5">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-xl font-semibold text-[#1d2c24]">
                Resume Analysis
              </h3>
              <span className="rounded-full bg-[#d9efe2] px-3 py-1 text-xs font-semibold text-[#246747]">
                {totalScore}/{scoreOutOf} ATS
              </span>
            </div>

            <div className="mt-5 space-y-4">
              {breakdownEntries.slice(0, 3).map(([key, value]) => {
                const max = key === "keyword_match" ? 20 : 15;
                const pct = Math.round((value / max) * 100);
                return (
                  <div key={key}>
                    <div className="mb-1 flex items-center justify-between text-sm text-[#34443b]">
                      <span>{formatLabel(key)}</span>
                      <span>
                        {value}/{max}
                      </span>
                    </div>
                    <div className="h-2 rounded-full bg-[#deebe4]">
                      <div
                        className="h-2 rounded-full bg-[#0f6c45]"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="mt-5">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[#0f6c45]">
                Archivist Verdict
              </p>
              <p className="mt-2 text-sm italic text-[#4f6057]">
                "{verdictExcerpt}."
              </p>
            </div>
          </article>

          <article className="rounded-3xl border border-[#dce5df] bg-[#f8faf9] p-5">
            <h3 className="text-xl font-semibold text-[#1d2c24]">
              Critical Skill Gaps
            </h3>
            <div className="mt-4 flex flex-wrap gap-2">
              {data.missing_keywords.slice(0, 6).map((keyword) => (
                <span
                  key={keyword}
                  className="rounded-md bg-[#ffe6e2] px-2 py-1 text-xs font-semibold uppercase text-[#a23d37]"
                >
                  {keyword}
                </span>
              ))}
            </div>

            <h4 className="mt-5 text-sm font-semibold text-[#314139]">
              Top Improvements Required:
            </h4>
            <ul className="mt-2 space-y-1 text-sm text-[#44554c]">
              {data.top_improvements.slice(0, 3).map((item) => (
                <li key={item}>
                  • {item.length > 70 ? `${item.slice(0, 70)}...` : item}
                </li>
              ))}
            </ul>
          </article>
        </div>

        <div className="space-y-5">
          <article className="rounded-3xl border border-[#dce5df] bg-[#f8faf9] p-5">
            <h3 className="text-2xl font-semibold text-[#1d2c24]">
              Highlighted Repositories
            </h3>

            <div className="mt-4 space-y-4">
              {repositories.map((repo) => (
                <div
                  key={repo.name}
                  className="rounded-2xl border border-[#dce5df] bg-white p-4"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-2xl font-semibold text-[#1d2c24]">
                        {repo.name}
                      </p>
                      <div className="mt-2 flex gap-2">
                        <span className="rounded-full bg-[#d8efe2] px-2 py-1 text-xs font-semibold text-[#246747]">
                          Python
                        </span>
                        <span className="rounded-full bg-[#d8efe2] px-2 py-1 text-xs font-semibold text-[#246747]">
                          Automation
                        </span>
                      </div>
                    </div>
                    <p className="text-right text-sm font-semibold text-[#33443b]">
                      <span className="text-3xl text-[#1d2c24]">
                        {repo.score}
                      </span>
                      /10
                      <br />
                      Repo Score
                    </p>
                  </div>

                  <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
                    <div className="rounded-xl bg-[#edf6f0] p-3">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#246747]">
                        Pro
                      </p>
                      <p className="mt-1 text-sm text-[#43544b]">{repo.pro}</p>
                    </div>
                    <div className="rounded-xl bg-[#fff1ef] p-3">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#ae3f38]">
                        Red Flag
                      </p>
                      <p className="mt-1 text-sm text-[#5b4c49]">
                        {repo.redFlag}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </article>
        </div>
      </div>

      <div className="flex flex-col gap-4 rounded-2xl border border-[#dce5df] bg-[#f8faf9] p-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm font-semibold text-[#2c3d34]">Review Status</p>
          <p className="text-sm text-[#607066]">
            Last scanned: Today at 09:12 AM
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <button className="rounded-full border border-[#d9e3dd] bg-white px-5 py-2 text-sm font-semibold text-[#46564d]">
            Archive
          </button>
          <button className="rounded-full bg-[#cdebd8] px-5 py-2 text-sm font-semibold text-[#2a6a49]">
            Shortlist
          </button>
          <button className="rounded-full bg-[#0f6c45] px-5 py-2 text-sm font-semibold text-white">
            Interview
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 text-[10px] font-semibold uppercase tracking-[0.2em] text-[#9aa8a0] md:grid-cols-2">
        <p>HireFlow Intelligent ATS Analysis</p>
        <p className="md:text-right">
          Privacy Policy · Terms Of Service · Data Protocol v2.4
        </p>
      </div>

      <div className="hidden">
        {semanticMatch}
        {keywordsFound}
      </div>
    </section>
  );
}
