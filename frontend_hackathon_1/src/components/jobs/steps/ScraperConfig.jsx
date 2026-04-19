// src/pages/jobs/steps/ScraperConfig.jsx
import { MetricRow } from "../../../components/WizardComponents";

export const METRICS = [
  { key: "languageMatch",     name: "Language match",            description: "Does their GitHub code match the required languages?" },
  { key: "codeQuality",       name: "Code quality",              description: "Readability, structure, and naming conventions" },
  { key: "codeSecurity",      name: "Code security",             description: "Common vulnerabilities and safe coding practices" },
  { key: "commitConsistency", name: "Commit consistency",        description: "Regular activity and meaningful commit messages" },
  { key: "projectComplexity", name: "Project complexity",        description: "Size, depth, and originality of projects" },
  { key: "openSource",        name: "Open source contributions", description: "PRs, issues, and reviews on public repos" },
  { key: "testCoverage",      name: "Test coverage",             description: "Presence and quality of tests in their repos" },
];

export default function ScraperConfig({ data, onChange }) {
  const updateMetric = (key, value) =>
    onChange({
      ...data,
      scraperMetrics: { ...data.scraperMetrics, [key]: value },
    });

  return (
    <div className="flex flex-col gap-4">

      <div className="bg-white border border-gray-100 rounded-2xl p-6">
        <h2 className="text-sm font-semibold text-gray-900">GitHub scraper metrics</h2>
        <p className="text-xs text-gray-400 mt-0.5 mb-4">
          Toggle metrics on or off and adjust how much each one affects the overall score.
        </p>

        {METRICS.map((m) => (
          <MetricRow
            key={m.key}
            name={m.name}
            description={m.description}
            enabled={data.scraperMetrics[m.key]?.enabled ?? true}
            weight={data.scraperMetrics[m.key]?.weight ?? 50}
            onChange={(val) => updateMetric(m.key, val)}
          />
        ))}
      </div>

      <div className="bg-white border border-gray-100 rounded-2xl p-6">
        <h2 className="text-sm font-semibold text-gray-900">Additional instructions</h2>
        <p className="text-xs text-gray-400 mt-0.5 mb-4">
          Any extra context the scraper should consider when evaluating candidates.
        </p>
        <textarea
          value={data.scraperInstructions}
          onChange={(e) => onChange({ ...data, scraperInstructions: e.target.value })}
          placeholder="e.g. We are a fintech company — prioritise candidates with experience in financial systems or regulated environments..."
          rows={4}
          className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 outline-none focus:border-gray-400 resize-none leading-relaxed"
        />
      </div>

    </div>
  );
}