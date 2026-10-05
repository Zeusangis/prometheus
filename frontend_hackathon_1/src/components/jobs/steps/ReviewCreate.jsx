// src/pages/jobs/steps/ReviewCreate.jsx
import { METRICS } from "./ScraperConfig";
import { TONES } from "../../../components/WizardComponents";

function SummaryRow({ label, value }) {
  return (
    <div className="flex justify-between items-start gap-4 py-2.5 border-b border-gray-100 last:border-0 text-sm">
      <span className="text-gray-400 shrink-0">{label}</span>
      <span className="text-gray-900 font-medium text-right max-w-[60%]">
        {value || "—"}
      </span>
    </div>
  );
}

export default function ReviewCreate({ data }) {
  const enabledMetrics = METRICS.filter(
    (m) => data.scraperMetrics[m.key]?.enabled,
  );
  const toneName = TONES.find((t) => t.id === data.interviewTone)?.label || "—";

  return (
    <div className="flex flex-col gap-4">
      <div className="bg-white border border-gray-100 rounded-2xl p-6">
        <h2 className="text-sm font-semibold text-gray-900 mb-3">
          Job details
        </h2>
        <SummaryRow label="Title" value={data.title} />
        <SummaryRow label="Job type" value={data.jobType} />
        <SummaryRow
          label="Languages"
          value={
            data.languages.length ? data.languages.join(", ") : "None selected"
          }
        />
        <SummaryRow
          label="Frameworks"
          value={
            data.frameworks.length
              ? data.frameworks.join(", ")
              : "None selected"
          }
        />
      </div>

      <div className="bg-white border border-gray-100 rounded-2xl p-6">
        <h2 className="text-sm font-semibold text-gray-900 mb-3">
          GitHub scraper
        </h2>
        <SummaryRow
          label="Active metrics"
          value={`${enabledMetrics.length} of ${METRICS.length} enabled`}
        />
        <SummaryRow
          label="Metrics"
          value={enabledMetrics.map((m) => m.name).join(", ") || "None"}
        />
        {data.scraperInstructions && (
          <SummaryRow
            label="Extra instructions"
            value={data.scraperInstructions}
          />
        )}
      </div>

      <div className="bg-white border border-gray-100 rounded-2xl p-6">
        <h2 className="text-sm font-semibold text-gray-900 mb-3">
          AI interview
        </h2>
        <SummaryRow label="Tone" value={toneName} />
        <SummaryRow
          label="Focus areas"
          value={data.interviewFocus.join(", ") || "None selected"}
        />
        <SummaryRow
          label="Custom questions"
          value={
            data.customQuestions.length
              ? `${data.customQuestions.length} question${data.customQuestions.length > 1 ? "s" : ""}`
              : "None"
          }
        />
        <SummaryRow
          label="Duration"
          value={`${data.interviewLength} minutes`}
        />
      </div>

      <div className="bg-gray-50 border border-dashed border-gray-200 rounded-2xl p-6">
        <h2 className="text-sm font-semibold text-gray-900 mb-3">
          After creating this job you'll get
        </h2>
        <ul className="flex flex-col gap-2">
          {[
            "A shareable application link to send to candidates",
            "An applicant list with recruiter-controlled stages",
            "Stored GitHub analysis preferences (analysis integration pending)",
            "Stored interview settings (live interviews not yet available)",
          ].map((item) => (
            <li
              key={item}
              className="flex items-start gap-2 text-sm text-gray-600"
            >
              <span className="text-gray-400 mt-0.5">→</span>
              {item}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
