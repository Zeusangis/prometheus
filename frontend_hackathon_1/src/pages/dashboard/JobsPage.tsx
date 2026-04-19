import { useQuery } from "@tanstack/react-query";
import { Sidebar } from "../../components/Sidebar";
import { Header } from "../../components/Header";
import { JobsList } from "../../components/JobsList";
import { getCompanyJobs } from "../../api/jobs";

const filters = ["All Jobs", "Active", "Closed"];

export default function JobsPage() {
  const {
    data: jobs = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ["company-jobs"],
    queryFn: getCompanyJobs,
  });

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        <Header />

        <main className="px-4 pb-8 pt-4 md:px-6">
          <div className="mx-auto max-w-6xl space-y-5">
            <section className="rounded-3xl border border-[#e1e6e3] bg-[#f7f9f8] p-5">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#0f6c45]">
                    Job Openings
                  </p>
                  <h1 className="mt-2 text-4xl font-semibold leading-tight text-foreground">
                    Manage active roles
                  </h1>
                  <p className="mt-2 max-w-2xl text-base text-[#425349]">
                    Review, track, and manage the hiring pipeline for current
                    openings.
                  </p>
                </div>

                <div className="flex flex-wrap gap-2 rounded-2xl border border-[#e1e6e3] bg-white p-2">
                  {filters.map((filter, index) => (
                    <button
                      key={filter}
                      className={`rounded-xl px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] transition-colors ${
                        index === 0
                          ? "bg-white text-[#0f6c45] shadow-sm"
                          : "text-[#2f3b34] hover:bg-[#f2f6f4]"
                      }`}
                    >
                      {filter}
                    </button>
                  ))}
                </div>
              </div>
            </section>
            {isLoading ? (
              <div className="rounded-3xl border border-[#e1e6e3] bg-white p-10 text-center text-[#5a6a61]">
                Loading jobs...
              </div>
            ) : error ? (
              <div className="rounded-3xl border border-[#f3d7d6] bg-[#fff6f6] p-10 text-center text-[#9a3530]">
                Failed to load jobs. Please make sure the backend is running.
              </div>
            ) : (
              <JobsList jobs={jobs} />
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
