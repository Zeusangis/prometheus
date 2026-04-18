// src/components/WizardComponents.jsx
import { useState } from "react";

export function TagGroup({ options, selected, onChange }) {
  const toggle = (val) =>
    onChange(
      selected.includes(val)
        ? selected.filter((v) => v !== val)
        : [...selected, val]
    );

  return (
    <div className="flex flex-wrap gap-2 mt-1">
      {options.map((opt) => (
        <button
          key={opt}
          type="button"
          onClick={() => toggle(opt)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-sm transition-all cursor-pointer
            ${selected.includes(opt)
              ? "border-gray-800 bg-gray-100 text-gray-900 font-medium"
              : "border-gray-200 text-gray-500 hover:border-gray-400 hover:text-gray-700"
            }`}
        >
          {selected.includes(opt) && (
            <span className="w-3 h-3 rounded-full bg-gray-800 flex items-center justify-center">
              <svg width="7" height="5" viewBox="0 0 7 5" fill="none">
                <path d="M1 2.5L2.5 4L6 1" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </span>
          )}
          {opt}
        </button>
      ))}
    </div>
  );
}

export function Toggle({ on, onChange }) {
  return (
    <button
      type="button"
      onClick={() => onChange(!on)}
      className={`relative w-9 h-5 rounded-full transition-colors flex-shrink-0 cursor-pointer
        ${on ? "bg-gray-800" : "bg-gray-200"}`}
    >
      <span className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-all
        ${on ? "left-4" : "left-0.5"}`}
      />
    </button>
  );
}

export function MetricRow({ name, description, enabled, weight, onChange }) {
  return (
    <div className="flex items-center gap-4 py-3 border-b border-gray-100 last:border-0">
      <Toggle on={enabled} onChange={(val) => onChange({ enabled: val, weight })} />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900">{name}</p>
        <p className="text-xs text-gray-400 mt-0.5">{description}</p>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        <input
          type="range"
          min={0} max={100} step={1}
          value={weight}
          disabled={!enabled}
          onChange={(e) => onChange({ enabled, weight: Number(e.target.value) })}
          className="w-24 accent-gray-800 disabled:opacity-30"
        />
        <span className="text-xs font-medium text-gray-700 w-8 text-right">{weight}%</span>
      </div>
    </div>
  );
}

export function QuestionList({ questions, onChange }) {
  const [draft, setDraft] = useState("");

  const add = () => {
    const trimmed = draft.trim();
    if (!trimmed) return;
    onChange([...questions, trimmed]);
    setDraft("");
  };

  const remove = (idx) => onChange(questions.filter((_, i) => i !== idx));

  return (
    <div>
      {questions.map((q, i) => (
        <div key={i} className="flex items-start gap-2 py-2.5 border-b border-gray-100 last:border-0">
          <span className="text-xs text-gray-300 mt-0.5 min-w-[18px]">{i + 1}.</span>
          <span className="flex-1 text-sm text-gray-700 leading-relaxed">{q}</span>
          <button
            type="button"
            onClick={() => remove(i)}
            className="text-gray-300 hover:text-red-400 text-lg leading-none px-1 cursor-pointer transition-colors"
          >
            ×
          </button>
        </div>
      ))}
      <div className="flex gap-2 mt-3">
        <input
          type="text"
          value={draft}
          placeholder="Add a custom question..."
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && add()}
          className="flex-1 text-sm border border-gray-200 rounded-lg px-3 py-2 outline-none focus:border-gray-400"
        />
        <button
          type="button"
          onClick={add}
          className="text-sm px-3 py-2 border border-gray-200 rounded-lg text-gray-600 hover:border-gray-400 cursor-pointer transition-colors whitespace-nowrap"
        >
          + Add
        </button>
      </div>
    </div>
  );
}

export const TONES = [
  { id: "conversational", label: "Conversational",    desc: "Friendly and relaxed, builds rapport naturally" },
  { id: "technical",      label: "Technical deep-dive", desc: "Probes implementation details and edge cases" },
  { id: "socratic",       label: "Socratic",           desc: 'Asks "why" repeatedly to reveal true understanding' },
  { id: "pressure",       label: "Pressure test",      desc: "Challenges answers to assess confidence and reasoning" },
];

export function ToneSelector({ value, onChange }) {
  return (
    <div className="grid grid-cols-2 gap-2 mt-1">
      {TONES.map((t) => (
        <button
          key={t.id}
          type="button"
          onClick={() => onChange(t.id)}
          className={`text-left p-3 rounded-xl border transition-all cursor-pointer
            ${value === t.id
              ? "border-gray-800 bg-gray-50"
              : "border-gray-200 hover:border-gray-400"
            }`}
        >
          <p className="text-sm font-medium text-gray-900">{t.label}</p>
          <p className="text-xs text-gray-400 mt-1 leading-relaxed">{t.desc}</p>
        </button>
      ))}
    </div>
  );
}