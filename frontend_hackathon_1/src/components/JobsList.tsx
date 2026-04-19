import { Link } from "@tanstack/react-router";

const jobs = [
  {
    id: "frontend-dev",
    title: "Senior Product Designer",
    location: "Remote, US",
    department: "Design & Creative",
    status: "Active",
    applicants: 48,
    interviewing: 12,
    actionLabel: "Manage",
  },
  {
    id: "ui-ux-designer",
    title: "Backend Engineer",
    location: "London, UK",
    department: "Engineering",
    status: "Closed",
    applicants: 0,
    interviewing: 0,
    actionLabel: "Review",
  },
  {
    id: "devops-engineer",
    title: "Marketing Manager",
    location: "New York, NY",
    department: "Growth",
    status: "Active",
    applicants: 24,
    interviewing: 3,
    actionLabel: "Manage",
  },
  {
    id: "data-analyst",
    title: "Customer Success",
    location: "Remote",
    department: "Support",
    status: "Closed",
    applicants: 0,
    interviewing: 0,
    actionLabel: "Archive",
  },
];

export function JobsList() {
  return (
    <div className="overflow-hidden rounded-3xl border border-[#e1e6e3] bg-white shadow-[0_12px_30px_-24px_rgba(15,108,69,0.18)]">
      <div className="overflow-x-auto">
        <table className="min-w-full border-separate border-spacing-0">
          <thead>
            <tr className="bg-[#f7f9f8] text-left text-[11px] uppercase tracking-[0.18em] text-[#6c7a72]">
              <th className="px-6 py-4 font-semibold">Job Title & Location</th>
              <th className="px-6 py-4 font-semibold">Department</th>
              <th className="px-6 py-4 font-semibold">Status</th>
              <th className="px-6 py-4 font-semibold">Applicants</th>
              <th className="px-6 py-4 font-semibold">Interviewing</th>
              <th className="px-6 py-4 font-semibold text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
              <tr key={job.id} className="border-t border-[#edf1ef]">
                <td className="px-6 py-5">
                  <Link
                    to="/dashboard/$jobId"
                    params={{ jobId: job.id }}
                    className="group block"
                  >
                    <p className="text-base font-semibold text-[#1d2c24] group-hover:text-[#0f6c45]">
                      {job.title}
                    </p>
                    <p className="mt-1 text-sm text-[#5a6a61]">
                      {job.location}
                    </p>
                  </Link>
                </td>
                <td className="px-6 py-5 text-sm text-[#2f3b34]">
                  {job.department}
                </td>
                <td className="px-6 py-5">
                  <span
                    className={`inline-flex rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] ${
                      job.status === "Active"
                        ? "bg-[#dff0e5] text-[#0f6c45]"
                        : "bg-[#eef1ef] text-[#64736b]"
                    }`}
                  >
                    {job.status}
                  </span>
                </td>
                <td className="px-6 py-5 text-2xl font-semibold text-[#0f6c45]">
                  {job.applicants || "--"}
                </td>
                <td className="px-6 py-5 text-2xl font-semibold text-[#0f6c45]">
                  {job.interviewing || "--"}
                </td>
                <td className="px-6 py-5 text-right">
                  <Link
                    to="/dashboard/$jobId"
                    params={{ jobId: job.id }}
                    className="inline-flex rounded-xl bg-[#0f6c45] px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-[#0c5c3a]"
                  >
                    {job.actionLabel}
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
