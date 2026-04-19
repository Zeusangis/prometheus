// src/pages/jobs/steps/JobDetails.jsx
import { TagGroup } from "../../../components/WizardComponents";

const LANGUAGES = [
  "Python",
  "JavaScript",
  "TypeScript",
  "Go",
  "Rust",
  "Java",
  "C++",
  "Ruby",
  "Swift",
  "Kotlin",
  "PHP",
  "Scala",
];

const FRAMEWORKS = [
  "React",
  "Node.js",
  "Django",
  "FastAPI",
  "Next.js",
  "Docker",
  "Kubernetes",
  "GraphQL",
  "PostgreSQL",
  "Redis",
  "AWS",
  "GCP",
];

export default function JobDetails({ data, onChange }) {
  const set = (key) => (e) => onChange({ ...data, [key]: e.target.value });

  return (
    <div className="flex flex-col gap-4">
      {/* Basic info */}
      <div className="bg-white border border-gray-100 rounded-2xl p-6">
        <h2 className="text-sm font-semibold text-gray-900">Job details</h2>
        <p className="text-xs text-gray-400 mt-0.5 mb-4">
          Basic information about the role.
        </p>

        <div className="flex flex-col gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">
              Job title
            </label>
            <input
              type="text"
              value={data.title}
              onChange={set("title")}
              placeholder="e.g. Senior Backend Engineer"
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 outline-none focus:border-gray-400"
            />
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-2">Job type</label>
            <div className="flex gap-2">
              {["Remote", "Hybrid", "On-site"].map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => onChange({ ...data, jobType: type })}
                  className={`px-4 py-2 text-sm rounded-lg border transition-colors ${
                    data.jobType === type
                      ? "bg-gray-900 text-white border-gray-900"
                      : "bg-white text-gray-600 border-gray-200 hover:border-gray-400"
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">
              Role description
            </label>
            <textarea
              value={data.description}
              onChange={set("description")}
              placeholder="Briefly describe the role and what the candidate will be working on..."
              rows={4}
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 outline-none focus:border-gray-400 resize-none leading-relaxed"
            />
          </div>
        </div>
      </div>

      {/* Skills */}
      <div className="bg-white border border-gray-100 rounded-2xl p-6">
        <h2 className="text-sm font-semibold text-gray-900">Required skills</h2>
        <p className="text-xs text-gray-400 mt-0.5 mb-4">
          Select the languages and tools candidates should know.
        </p>

        <div className="flex flex-col gap-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">
              Languages
            </label>
            <TagGroup
              options={LANGUAGES}
              selected={data.languages}
              onChange={(v) => onChange({ ...data, languages: v })}
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">
              Frameworks & tools
            </label>
            <TagGroup
              options={FRAMEWORKS}
              selected={data.frameworks}
              onChange={(v) => onChange({ ...data, frameworks: v })}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
