// src/pages/dashboard/Dashboard.jsx
import { useNavigate } from "@tanstack/react-router";
import { useDashboardJobs } from "../../hooks/useCandidates";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
} from "recharts";

function StatCard({ label, value, sub, accent }) {
  return (
    <div className={`rounded-2xl p-5 flex flex-col gap-1 ${accent ? "bg-green-700 text-white" : "bg-white border border-gray-100"}`}>
      <p className={`text-xs font-medium ${accent ? "text-green-200" : "text-gray-400"}`}>{label}</p>
      <p className={`text-3xl font-semibold tracking-tight ${accent ? "text-white" : "text-gray-900"}`}>{value}</p>
      {sub && <p className={`text-xs ${accent ? "text-green-200" : "text-gray-400"}`}>{sub}</p>}
    </div>
  );
}

function JobRow({ job, onClick, rank }) {
  const typeColor =
    job.type === "Remote" ? "bg-blue-50 text-blue-600" :
    job.type === "Hybrid" ? "bg-yellow-50 text-yellow-600" :
                            "bg-gray-100 text-gray-500";
  const maxApplicants = 10;
  const fillPct = Math.min((job.applicantCount / maxApplicants) * 100, 100);

  return (
    <div
      onClick={onClick}
      className="flex items-center gap-4 px-5 py-4 hover:bg-gray-50 cursor-pointer transition-colors"
    >
      <div className="w-7 h-7 rounded-lg bg-green-50 flex items-center justify-center flex-shrink-0">
        <span className="text-xs font-semibold text-green-700">{rank}</span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1.5">
          <p className="text-sm font-medium text-gray-900 truncate">{job.title}</p>
          <div className="flex items-center gap-2 flex-shrink-0 ml-2">
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${typeColor}`}>
              {job.type}
            </span>
            <span className="text-xs font-semibold text-gray-700">{job.applicantCount}</span>
          </div>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-1">
          <div
            className="h-1 rounded-full bg-green-500 transition-all"
            style={{ width: `${fillPct}%` }}
          />
        </div>
      </div>
    </div>
  );
}

const BarTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white border border-gray-100 rounded-xl px-3 py-2 shadow-sm">
        <p className="text-xs text-gray-400">{label}</p>
        <p className="text-sm font-semibold text-gray-900">{payload[0].value} applicants</p>
      </div>
    );
  }
  return null;
};

export default function Dashboard() {
  const { data: jobs, isLoading, error } = useDashboardJobs();
  const navigate = useNavigate();

  const totalApplicants = jobs?.reduce((sum, j) => sum + j.applicantCount, 0) ?? 0;
  const totalJobs = jobs?.length ?? 0;

  const barData = jobs?.map((j) => ({
    name: j.title.split(" ").slice(0, 2).join(" "),
    applicants: j.applicantCount,
  })) ?? [];

  const pieData = [
    { name: "Remote",  value: jobs?.filter(j => j.type === "Remote").length ?? 0,  fill: "#15803d" },
    { name: "Hybrid",  value: jobs?.filter(j => j.type === "Hybrid").length ?? 0,  fill: "#bbf7d0" },
    { name: "Onsite",  value: jobs?.filter(j => j.type === "Onsite").length ?? 0,  fill: "#e5e7eb" },
  ].filter(d => d.value > 0);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-6 py-8">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900 tracking-tight">Dashboard</h1>
            <p className="text-sm text-gray-400 mt-0.5">Overview of your hiring pipeline.</p>
          </div>
          <button
            onClick={() => navigate({ to: "/jobs/new" })}
            className="text-sm px-4 py-2 bg-green-700 text-white rounded-xl hover:bg-green-600 cursor-pointer transition-all font-medium"
          >
            + New job
          </button>
        </div>

        {/* Main grid */}
        <div className="grid grid-cols-3 gap-4">

          {/* LEFT COLUMN */}
          <div className="col-span-2 flex flex-col gap-4">

            {/* Stat cards */}
            <div className="grid grid-cols-3 gap-4">
              <StatCard
                label="Total jobs"
                value={isLoading ? "—" : totalJobs}
                sub="active postings"
                accent
              />
              <StatCard
                label="Applicants"
                value={isLoading ? "—" : totalApplicants}
                sub="across all jobs"
              />
              <StatCard
                label="Interviews"
                value="—"
                sub="coming soon"
              />
            </div>

            {/* Bar chart */}
            {!isLoading && barData.length > 0 && (
              <div className="bg-white border border-gray-100 rounded-2xl p-5 flex-1">
                <h2 className="text-sm font-semibold text-gray-900">Applicants per job</h2>
                <p className="text-xs text-gray-400 mt-0.5 mb-4">Candidates applied to each posting.</p>
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={barData} barSize={40}>
                    <XAxis
                      dataKey="name"
                      tick={{ fontSize: 11, fill: "#9ca3af" }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      tick={{ fontSize: 11, fill: "#9ca3af" }}
                      axisLine={false}
                      tickLine={false}
                      width={20}
                      allowDecimals={false}
                    />
                    <Tooltip content={<BarTooltip />} cursor={{ fill: "#f9fafb" }} />
                    <Bar dataKey="applicants" radius={[6, 6, 0, 0]}>
                      {barData.map((_, i) => (
                        <Cell key={i} fill={i === 0 ? "#15803d" : "#bbf7d0"} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

          </div>

          {/* RIGHT COLUMN */}
          <div className="flex flex-col gap-4">

            {/* Donut chart */}
            {!isLoading && pieData.length > 0 && (
              <div className="bg-white border border-gray-100 rounded-2xl p-5">
                <h2 className="text-sm font-semibold text-gray-900">Job types</h2>
                <p className="text-xs text-gray-400 mt-0.5 mb-2">Remote vs hybrid vs onsite.</p>
                <div className="flex items-center justify-center">
                  <PieChart width={140} height={140}>
                    <Pie
                      data={pieData}
                      cx={65}
                      cy={65}
                      innerRadius={42}
                      outerRadius={62}
                      paddingAngle={3}
                      dataKey="value"
                    >
                      {pieData.map((entry, i) => (
                        <Cell key={i} fill={entry.fill} />
                      ))}
                    </Pie>
                  </PieChart>
                </div>
                <div className="flex flex-col gap-1.5 mt-1">
                  {pieData.map((d) => (
                    <div key={d.name} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full" style={{ background: d.fill }} />
                        <span className="text-xs text-gray-500">{d.name}</span>
                      </div>
                      <span className="text-xs font-medium text-gray-700">{d.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Job list */}
            <div className="bg-white border border-gray-100 rounded-2xl overflow-hidden flex-1">
              <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
                <h2 className="text-sm font-semibold text-gray-900">Job postings</h2>
                <span className="text-xs text-gray-400">{totalJobs} total</span>
              </div>

              {isLoading && (
                <div className="px-5 py-8 text-center text-sm text-gray-400">Loading...</div>
              )}

              {error && (
                <div className="px-5 py-8 text-center text-sm text-red-400">Failed to load.</div>
              )}

              {!isLoading && jobs?.length === 0 && (
                <div className="px-5 py-8 text-center">
                  <p className="text-sm text-gray-400">No jobs yet.</p>
                  <button
                    onClick={() => navigate({ to: "/jobs/new" })}
                    className="mt-2 text-sm text-green-700 underline cursor-pointer"
                  >
                    Create one
                  </button>
                </div>
              )}

              {!isLoading && jobs?.map((job, i) => (
                <div key={job.id} className={i < jobs.length - 1 ? "border-b border-gray-100" : ""}>
                  <JobRow
                    job={job}
                    rank={i + 1}
                    onClick={() => navigate({ to: `/dashboard/${job.id}` })}
                  />
                </div>
              ))}
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}