export const TONES = [
  { id: "conversational", label: "Conversational" },
  { id: "technical", label: "Technical" },
  { id: "structured", label: "Structured" },
  { id: "friendly", label: "Friendly" },
];

export function TagGroup({ options, selected, onChange }) {
  const toggle = (item) => {
    if (selected.includes(item)) {
      onChange(selected.filter((v) => v !== item));
      return;
    }
    onChange([...selected, item]);
  };

  return (
    <div className="flex flex-wrap gap-2">
      {options.map((option) => {
        const active = selected.includes(option);
        return (
          <button
            key={option}
            type="button"
            onClick={() => toggle(option)}
            className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
              active
                ? "bg-gray-900 border-gray-900 text-white"
                : "bg-white border-gray-200 text-gray-600 hover:border-gray-400"
            }`}
          >
            {option}
          </button>
        );
      })}
    </div>
  );
}

export function MetricRow({ name, description, enabled, weight, onChange }) {
  return (
    <div className="border border-gray-100 rounded-xl p-4 mb-3 last:mb-0">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-gray-900">{name}</p>
          <p className="text-xs text-gray-500 mt-1">{description}</p>
        </div>
        <label className="inline-flex items-center gap-2 text-xs text-gray-600">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => onChange({ enabled: e.target.checked, weight })}
          />
          Enabled
        </label>
      </div>

      <div className="mt-3">
        <label className="block text-xs text-gray-500 mb-1">
          Weight: {weight}
        </label>
        <input
          type="range"
          min={0}
          max={100}
          value={weight}
          disabled={!enabled}
          onChange={(e) =>
            onChange({ enabled, weight: Number(e.target.value) })
          }
          className="w-full"
        />
      </div>
    </div>
  );
}

export function ToneSelector({ value, onChange }) {
  return (
    <div className="grid grid-cols-2 gap-2">
      {TONES.map((tone) => (
        <button
          key={tone.id}
          type="button"
          onClick={() => onChange(tone.id)}
          className={`rounded-lg border px-3 py-2 text-sm text-left transition-colors ${
            tone.id === value
              ? "bg-gray-900 border-gray-900 text-white"
              : "bg-white border-gray-200 text-gray-700 hover:border-gray-400"
          }`}
        >
          {tone.label}
        </button>
      ))}
    </div>
  );
}

export function QuestionList({ questions, onChange }) {
  const update = (index, value) => {
    const next = [...questions];
    next[index] = value;
    onChange(next);
  };

  const add = () => onChange([...questions, ""]);
  const remove = (index) => onChange(questions.filter((_, i) => i !== index));

  return (
    <div className="space-y-2">
      {questions.map((question, index) => (
        <div key={index} className="flex gap-2">
          <input
            value={question}
            onChange={(e) => update(index, e.target.value)}
            className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 outline-none focus:border-gray-400"
            placeholder="Ask something meaningful about candidate experience"
          />
          <button
            type="button"
            onClick={() => remove(index)}
            className="px-3 text-sm border border-gray-200 rounded-lg text-gray-600 hover:border-gray-400"
          >
            Remove
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={add}
        className="text-sm px-3 py-2 border border-gray-200 rounded-lg text-gray-600 hover:border-gray-400"
      >
        + Add question
      </button>
    </div>
  );
}
