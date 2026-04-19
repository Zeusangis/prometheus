import React from "react";
import ReactDOM from "react-dom/client";
import {
  createRootRoute,
  createRoute,
  createRouter,
  RouterProvider,
  Outlet,
} from "@tanstack/react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import NewJob from "./pages/NewJob";
import Dashboard from "./pages/dashboard/Dashboard";
import JobsPage from "./pages/dashboard/JobsPage";
import JobDetail from "./pages/dashboard/JobDetail";
import CandidateDetail from "./pages/dashboard/CandidateDetail";
import ProfilePage from "./pages/dashboard/ProfilePage";
import InterviewSummaryPage from "./pages/dashboard/InterviewSummaryPage";
import ApplyPage from "./pages/apply/ApplyPage";
import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 60_000, retry: 1 },
  },
});

function RootLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <Outlet />
    </QueryClientProvider>
  );
}

const rootRoute = createRootRoute({ component: RootLayout });

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: Dashboard,
});

const dashboardRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/dashboard",
  component: Dashboard,
});

const jobsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/dashboard/jobs",
  component: JobsPage,
});

const jobDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/dashboard/$jobId",
  component: JobDetail,
});

const candidateDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/candidate/$candidateId",
  component: CandidateDetail,
});

const profileRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/profile/$candidateId",
  component: ProfilePage,
});

const interviewSummaryRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/profile/$candidateId/interview-summary",
  component: InterviewSummaryPage,
});

const applyRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/apply/$jobId",
  component: ApplyPage,
});

const newJobRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/jobs/new",
  component: NewJob,
});

const routeTree = rootRoute.addChildren([
  indexRoute,
  dashboardRoute,
  jobsRoute,
  jobDetailRoute,
  candidateDetailRoute,
  profileRoute,
  interviewSummaryRoute,
  applyRoute,
  newJobRoute,
]);

const router = createRouter({ routeTree });

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
);
