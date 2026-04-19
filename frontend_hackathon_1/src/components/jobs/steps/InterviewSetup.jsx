// src/pages/jobs/steps/InterviewSetup.jsx
import { TagGroup, ToneSelector, QuestionList } from "../../../components/WizardComponents";

const FOCUS_AREAS = [
  "Understanding of their own code",
  "Problem-solving approach",
  "System design",
  "Team collaboration",
  "Past failures and learnings",
  "Why they made specific decisions",
  "Security awareness",
  "Performance optimisation",
  "Scalability thinking",
  "Code review experience",
];

const LENGTHS = [
  { value: 15, label: "15 minutes — quick screen" },
  { value: 30, label: "30 minutes — standard" },
  { value: 45, label: "45 minutes — in-depth" },
  { value: 60, label: "60 minutes — comprehensive" },
];

export default function InterviewSetup({ data, onChange }) {
  return (
    <div className="flex flex-col gap-4">

      <div className="bg-white border border-gray-100 rounded-2xl p-6">
        <h2 className="text-sm font-semibold text-gray-900">Interview tone</h2>
        <p className="text-xs text-gray-400 mt-0.5 mb-2">How should the AI interviewer conduct the session?</p>
        <ToneSelector
          value={data.interviewTone}
          onChange={(v) => onChange({ ...data, interviewTone: v })}
        />
      </div>

      <div className="bg-white border border-gray-100 rounded-2xl p-6">
        <h2 className="text-sm font-semibold text-gray-900">Focus areas</h2>
        <p className="text-xs text-gray-400 mt-0.5 mb-2">What should the interview dig into most?</p>
        <TagGroup
          options={FOCUS_AREAS}
          selected={data.interviewFocus}
          onChange={(v) => onChange({ ...data, interviewFocus: v })}
        />
      </div>

      <div className="bg-white border border-gray-100 rounded-2xl p-6">
        <h2 className="text-sm font-semibold text-gray-900">Custom questions</h2>
        <p className="text-xs text-gray-400 mt-0.5 mb-4">
          The AI will weave these into the interview naturally based on the candidate's profile.
        </p>
        <QuestionList
          questions={data.customQuestions}
          onChange={(v) => onChange({ ...data, customQuestions: v })}
        />
      </div>

      <div className="bg-white border border-gray-100 rounded-2xl p-6">
        <h2 className="text-sm font-semibold text-gray-900">Interview length</h2>
        <p className="text-xs text-gray-400 mt-0.5 mb-3">Estimated duration for the AI session.</p>
        <select
          value={data.interviewLength}
          onChange={(e) => onChange({ ...data, interviewLength: Number(e.target.value) })}
          className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 outline-none focus:border-gray-400 bg-white"
        >
          {LENGTHS.map((l) => (
            <option key={l.value} value={l.value}>{l.label}</option>
          ))}
        </select>
      </div>

      <div className="bg-white border border-gray-100 rounded-2xl p-6">
        <h2 className="text-sm font-semibold text-gray-900">Interviewer instructions</h2>
        <p className="text-xs text-gray-400 mt-0.5 mb-3">
          Specific guidance for the AI — topics to avoid, how to handle nerves, etc.
        </p>
        <textarea
          value={data.interviewInstructions}
          onChange={(e) => onChange({ ...data, interviewInstructions: e.target.value })}
          placeholder="e.g. Be encouraging if the candidate seems nervous. Do not ask about compensation..."
          rows={3}
          className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 outline-none focus:border-gray-400 resize-none leading-relaxed"
        />
      </div>

    </div>
  );
}