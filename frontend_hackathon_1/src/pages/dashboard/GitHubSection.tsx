import type { GitHubAnalysis, RepositoryAnalysis } from "../../api/apply";
import { EvidenceList, formatDate, formatLabel } from "./ResumeSection";

export function publicGitHubUrl(value: string | undefined | null) {
  try {
    const url = new URL(value || "");
    return url.protocol === "https:" && url.hostname === "github.com" && !url.username && !url.password && !url.port ? url.href : null;
  } catch { return null; }
}

function RepositoryCard({ repo }: { repo: RepositoryAnalysis }) {
  const link = publicGitHubUrl(repo.repo_url);
  const evidence = repo.evidence_metadata;
  const coverage = repo.metrics?.aggregation?.weight_coverage;
  return <article className="min-w-0 rounded-2xl border border-border bg-card p-5">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div className="min-w-0">
        <h3 className="break-words text-lg font-semibold">{link ? <a className="text-primary underline" href={link} target="_blank" rel="noopener noreferrer">{repo.repo_name}</a> : repo.repo_name}</h3>
        <p className="mt-1 text-sm text-muted-foreground">{repo.primary_language || "Language not reported"}{repo.metrics?.fork ? " · Fork — authorship caution" : ""}</p>
      </div>
      <p className="text-lg font-semibold">{repo.score === null ? "Not scored" : `${repo.score} / 100`}<span className="block text-xs font-normal text-muted-foreground">Sampled repository score</span></p>
    </div>
    <p className="mt-3 text-sm text-muted-foreground">Enabled weight coverage: {coverage == null ? "Not measured" : `${Math.round(coverage * 100)}%`}. Unknown dimensions are excluded from the score.</p>
    <p className="mt-3 whitespace-pre-wrap break-words text-sm">{repo.recruiter_summary || "No qualitative summary reported."}</p>
    {evidence?.review_error && <p role="status" className="mt-3 rounded-lg bg-secondary p-3 text-sm">{evidence.review_error}</p>}
    <dl className="mt-4 grid gap-3 sm:grid-cols-2">
      {Object.entries(repo.metrics?.dimensions || {}).map(([key, dimension]) => <div key={key} className="rounded-lg bg-secondary/50 p-3">
        <dt className="text-sm font-semibold">{formatLabel(key)}: {dimension.score === null ? "Not measured" : `${dimension.score} / 100`}</dt>
        <dd className="mt-1 break-words text-xs text-muted-foreground">{dimension.reasoning}</dd>
        {dimension.evidence_paths.length > 0 && <dd className="mt-2 break-all text-xs">Cited files: {dimension.evidence_paths.join(", ")}</dd>}
      </div>)}
    </dl>
    <div className="mt-4 grid gap-3 md:grid-cols-2">
      <EvidenceList title="Reported strengths" items={repo.strengths} />
      <EvidenceList title="Reported concerns" items={repo.red_flags} />
    </div>
    <details className="mt-4 rounded-lg border border-border p-3 text-sm">
      <summary className="cursor-pointer font-semibold">Evidence and sampling limits</summary>
      <p className="mt-3 text-muted-foreground">{evidence?.authorship_caveat || "Repository code is not proof of individual authorship."}</p>
      <p className="mt-2 text-muted-foreground">{evidence?.commit_scope || "Commit scope not reported."}</p>
      <p className="mt-2">Tree truncated: {evidence?.tree_truncated ? "Yes" : "No reported truncation"} · Commit sample truncated: {evidence?.commit_sample_truncated ? "Yes" : "No reported truncation"}</p>
      <h4 className="mt-3 font-semibold">Sampled file provenance</h4>
      {evidence?.files?.length ? <ul className="mt-2 space-y-2 text-xs">{evidence.files.map((file, index) => <li key={index} className="break-all">{file.path} · SHA {file.sha}{file.truncated ? " · Excerpt truncated" : ""}</li>)}</ul> : <p className="mt-2 text-xs">No sampled text-file provenance available.</p>}
      <h4 className="mt-3 font-semibold">Candidate-attributed sampled commits</h4>
      {evidence?.commits?.length ? <ul className="mt-2 space-y-2 text-xs">{evidence.commits.map((commit, index) => {
        const url = publicGitHubUrl(commit.url);
        return <li key={index} className="break-all">{url ? <a className="underline" href={url} target="_blank" rel="noopener noreferrer">{commit.sha}</a> : commit.sha} · {formatDate(commit.date)}</li>;
      })}</ul> : <p className="mt-2 text-xs">No candidate-attributed commits in the saved sample.</p>}
      <p className="mt-3 break-all text-xs text-muted-foreground">Pushed: {formatDate(repo.pushed_at)}{evidence?.model_name ? ` · Review model: ${evidence.model_name}` : ""}</p>
    </details>
  </article>;
}

export default function GitHubSection({ data, requested }: { data: GitHubAnalysis | null; requested: boolean }) {
  return <section aria-label="GitHub evidence" className="space-y-4">
    <article className="rounded-2xl border border-border bg-card p-5">
      <div className="flex flex-wrap items-center justify-between gap-3"><h2 className="text-xl font-semibold">GitHub evidence</h2><span className="rounded-full bg-secondary px-3 py-1 text-sm">{data ? formatLabel(data.status) : requested ? "Not available" : "Not requested"}</span></div>
      <p className="mt-3 text-sm text-muted-foreground">Bounded public evidence, not verified proficiency or individual authorship. Repository scores are separate from resume ATS scores.</p>
      {!data && <p className="mt-4 text-sm">{requested ? "No saved GitHub analysis is available." : "No GitHub username was supplied. No GitHub analysis was requested."}</p>}
      {data?.error_message && <p role="status" className="mt-3 rounded-lg bg-secondary p-3 text-sm">{data.error_message}</p>}
      {data && <>
        <dl className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
          {[["Public repositories", data.total_public_repos], ["Stars across full public listing", data.total_stars], ["Attributed commits in analyzed sample", data.candidate_attributed_commits]].map(([label, value]) => <div key={String(label)} className="rounded-lg bg-secondary/50 p-3"><dt className="text-xs text-muted-foreground">{label}</dt><dd className="mt-1 text-2xl font-semibold">{value ?? "Not measured"}</dd></div>)}
        </dl>
        {data.summary && <div className="mt-4 space-y-2 text-sm text-muted-foreground">
          <p>Listed: {data.summary.listed_repos ?? "Unknown"} · Analyzed: {data.summary.analyzed_repos ?? "Unknown"} · Stars in listed sample: {data.summary.sample_stars ?? "Unknown"}</p>
          <p>Repository listing {data.summary.repository_listing_truncated ? "truncated" : "has no reported truncation"}; repository analysis {data.summary.repository_analysis_sampled ? "sampled" : "has no reported sampling limit reached"}.</p>
          <p>{data.summary.commit_scope}</p><p>{data.summary.score_scope}</p>
          {data.summary.unsupported_metrics?.map((item, index) => <p key={index}>{item}</p>)}
          {data.summary.errors?.map((item, index) => <p key={index} className="break-words">{item.repo_name}: {item.message}</p>)}
          {data.summary.review_failures?.map((item, index) => <p key={`review-${index}`} className="break-words">{item.repo_name}: {item.message}</p>)}
        </div>}
        <p className="mt-4 text-xs text-muted-foreground">Updated: {formatDate(data.updated_at)}. Test evidence is not execution coverage; security review is not a guarantee.</p>
      </>}
    </article>
    {data?.repositories.map((repo) => <RepositoryCard key={repo.repo_name} repo={repo} />)}
    {data && data.repositories.length === 0 && <p className="rounded-2xl border border-border p-5 text-sm">No analyzed repositories are available in this saved result.</p>}
  </section>;
}
