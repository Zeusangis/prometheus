// src/pages/dashboard/CandidateDetail.jsx
import { useParams, useNavigate } from "@tanstack/react-router";
import { useCandidate } from "../../hooks/useCandidates";

const METRIC_LABELS = {
  languageMatch:      "Language match",
  codeQuality:        "Code quality",
  codeSecurity:       "Code security",
  commitConsistency:  "Commit consistency",
  projectComplexity:  "Project complexity",
  openSource:         "Open source",
  testCoverage:       "Test coverage",
};

function ScoreBar({ label, value }) {
  const color =
    value >= 85 ? "bg-green-500" :
    value >= 70 ? "bg-yellow-400" :
                  "bg-red-400";
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-gray-400 w-36 flex-shrink-0">{label}</span>
      <div className="flex-1 bg-gray-100 rounded-full h-1.5">
        <div
          className={`h-1.5 rounded-full ${color} transition-all`}
          style={{ width: `${value}%` }}
        />
      </div>
      <span className="text-xs font-medium text-gray-700 w-8 text-right">{value}</span>
    </div>
  );
}

function FitBadge({ fit }) {
  const color =
    fit === "Strong"   ? "bg-green-100 text-green-700" :
    fit === "Good"     ? "bg-blue-100 text-blue-700" :
    fit === "Moderate" ? "bg-yellow-100 text-yellow-700" :
                         "bg-gray-100 text-gray-500";
  return (
    <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${color}`}>
      {fit}
    </span>
  );
}

function TranscriptMessage({ role, message }) {
  const isAi = role === "ai";
  return (
    <div className={`flex gap-3 ${isAi ? "" : "flex-row-reverse"}`}>
      <div className={`w-6 h-6 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-medium
        ${isAi ? "bg-gray-900 text-white" : "bg-gray-100 text-gray-600"}`}>
        {isAi ? "AI" : "C"}
      </div>
      <div className={`max-w-[80%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed
        ${isAi
          ? "bg-gray-100 text-gray-800 rounded-tl-none"
          : "bg-gray-900 text-white rounded-tr-none"
        }`}>
        {message}
      </div>
    </div>
  );
}

export default function CandidateDetail() {
  const { candidateId } = useParams({ strict: false });
  const navigate = useNavigate();
  const { data: candidate, isLoading, error } = useCandidate(candidateId);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-sm text-gray-400">Loading candidate...</p>
      </div>
    );
  }

  if (error || !candidate) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-sm text-red-400">Failed to load candidate.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-10">

        {/* Back */}
        <button
          onClick={() => navigate({ to: `/dashboard/${candidate.jobId}` })}
          className="text-xs text-gray-400 hover:text-gray-600 cursor-pointer mb-6 flex items-center gap-1 transition-colors"
        >
          ← Back to applicants
        </button>

        {/* Header */}
        <div className="bg-white border border-gray-100 rounded-2xl p-6 mb-4">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900 tracking-tight">
                {candidate.name}
              </h1>
              <div className="flex items-center gap-3 mt-1">
                <a
                  href={`https://github.com/${candidate.github}`}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm text-gray-400 hover:text-gray-600 transition-colors"
                >
                  @{candidate.github}
                </a>
                <span className="text-gray-200">·</span>
                <span className="text-sm text-gray-400">
                  Applied {new Date(candidate.appliedAt).toLocaleDateString()}
                </span>
              </div>
            </div>

            {/* Overall score */}
            <div className="text-center">
              <div className={`text-4xl font-semibold ${
                candidate.overallScore >= 85 ? "text-green-600" :
                candidate.overallScore >= 70 ? "text-yellow-500" :
                "text-red-500"
              }`}>
                {candidate.overallScore}
              </div>
              <p className="text-xs text-gray-400 mt-0.5">overall score</p>
            </div>
          </div>

          {/* Badges */}
          <div className="flex items-center gap-2 mt-4">
            <FitBadge fit={candidate.teamFit} />
            <span className="text-xs bg-gray-100 text-gray-600 px-2.5 py-1 rounded-full font-medium">
              {candidate.engineerLevel}
            </span>
            {candidate.topLanguages.map((lang) => (
              <span key={lang} className="text-xs bg-gray-100 text-gray-600 px-2.5 py-1 rounded-full">
                {lang}
              </span>
            ))}
            {candidate.interviewComplete ? (
              <span className="text-xs bg-green-100 text-green-700 px-2.5 py-1 rounded-full font-medium">
                Interview complete
              </span>
            ) : (
              <span className="text-xs bg-yellow-100 text-yellow-700 px-2.5 py-1 rounded-full font-medium">
                Interview pending
              </span>
            )}
          </div>
        </div>

        {/* Score breakdown */}
        <div className="bg-white border border-gray-100 rounded-2xl p-6 mb-4">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">Score breakdown</h2>
          <div className="flex flex-col gap-3">
            {Object.entries(METRIC_LABELS).map(([key, label]) => (
              candidate[key] !== undefined && (
                <ScoreBar key={key} label={label} value={candidate[key]} />
              )
            ))}
          </div>
        </div>

        {/* GitHub scraper summary */}
        <div className="bg-white border border-gray-100 rounded-2xl p-6 mb-4">
          <h2 className="text-sm font-semibold text-gray-900 mb-3">GitHub analysis</h2>
          <p className="text-sm text-gray-600 leading-relaxed">{candidate.scraperSummary}</p>
        </div>

        {/* Interview summary */}
        {candidate.interviewComplete && (
          <div className="bg-white border border-gray-100 rounded-2xl p-6 mb-4">
            <h2 className="text-sm font-semibold text-gray-900 mb-3">Interview summary</h2>
            <p className="text-sm text-gray-600 leading-relaxed">{candidate.interviewSummary}</p>
          </div>
        )}

        {/* Interview transcript */}
        {candidate.interviewComplete && candidate.interviewTranscript?.length > 0 && (
          <div className="bg-white border border-gray-100 rounded-2xl p-6">
            <h2 className="text-sm font-semibold text-gray-900 mb-5">Interview transcript</h2>
            <div className="flex flex-col gap-4">
              {candidate.interviewTranscript.map((msg, i) => (
                <TranscriptMessage key={i} role={msg.role} message={msg.message} />
              ))}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}