import type { ResumeAnalysis } from "../../api/apply";

export const ATS_LIMITS: Record<string, number> = {
  keyword_match: 25, skills_alignment: 15, experience_relevance: 20,
  education: 10, formatting: 10, achievements: 10, completeness: 10,
};

export function formatLabel(key: string) {
  return key.replace(/_/g, " ").replace(/([a-z])([A-Z])/g, "$1 $2").replace(/\b\w/g, (char) => char.toUpperCase());
}

export function formatDate(value: string | null | undefined) {
  if (!value) return "Not available";
  // Backend's SQLite DateTime serialization omits the UTC suffix.
  const date = new Date(/(?:Z|[+-]\d{2}:\d{2})$/.test(value) ? value : `${value}Z`);
  return Number.isNaN(date.getTime()) ? "Not available" : date.toLocaleString();
}

export function EvidenceList({ title, items }: { title: string; items: string[] | null }) {
  return <article className="rounded-2xl border border-border bg-card p-5">
    <h3 className="text-lg font-semibold">{title}</h3>
    {items?.length ? <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-muted-foreground">
      {items.map((item, index) => <li key={index} className="whitespace-pre-wrap break-words">{item}</li>)}
    </ul> : <p className="mt-3 text-sm text-muted-foreground">No items reported in the saved analysis.</p>}
  </article>;
}

export default function ResumeSection({ data }: { data: ResumeAnalysis | null }) {
  const complete = data?.status === "complete";
  return <section aria-label="Resume analysis" className="space-y-4">
    <article className="rounded-2xl border border-border bg-card p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-semibold">Resume analysis</h2>
        <span className="rounded-full bg-secondary px-3 py-1 text-sm">{data ? formatLabel(data.status) : "Not available"}</span>
      </div>
      <p className="mt-3 text-sm text-muted-foreground">Job-aware AI evidence for human review, not verified skills or a hiring recommendation.</p>
      {data?.error_message && <p role="status" className="mt-3 rounded-lg bg-secondary p-3 text-sm">{data.error_message}</p>}
      {!complete ? <p className="mt-4 text-sm">{data?.status === "pending" || data?.status === "running"
        ? "Resume analysis is pending. No score has been produced yet."
        : "No completed resume analysis is available. No ATS score is shown."}</p> : <>
        <p className="mt-5 text-3xl font-bold text-primary">{data.ats_score ?? "Not measured"}{data.ats_score !== null && <span className="text-base font-normal"> / 100 ATS</span>}</p>
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          {Object.entries(ATS_LIMITS).map(([key, maximum]) => {
            const value = data.breakdown?.[key];
            return <div key={key}>
              <div className="mb-1 flex justify-between gap-2 text-sm"><span>{formatLabel(key)}</span><span>{value == null ? "Not measured" : `${value} / ${maximum}`}</span></div>
              {value != null && <div role="progressbar" aria-label={formatLabel(key)} aria-valuenow={value} aria-valuemin={0} aria-valuemax={maximum} className="h-2 rounded-full bg-secondary">
                <div className="h-2 rounded-full bg-primary" style={{ width: `${Math.min(100, Math.max(0, value / maximum * 100))}%` }} />
              </div>}
            </div>;
          })}
        </div>
        <h3 className="mt-6 font-semibold">Saved resume assessment</h3>
        <p className="mt-2 whitespace-pre-wrap break-words text-sm text-muted-foreground">{data.final_verdict || "No summary reported."}</p>
      </>}
      <p className="mt-5 text-xs text-muted-foreground">Updated: {formatDate(data?.updated_at)}{data?.model_name ? ` · Model: ${data.model_name}` : ""}</p>
    </article>
    {complete && <div className="grid gap-4 md:grid-cols-2">
      <EvidenceList title="Missing keywords" items={data.missing_keywords} />
      <EvidenceList title="Weak areas and uncertainty" items={data.weak_areas} />
      <EvidenceList title="Suggested improvements" items={data.top_improvements} />
      <EvidenceList title="Projects mentioned in resume" items={data.projects} />
    </div>}
  </section>;
}
