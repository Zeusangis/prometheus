import React from "react";
import ReactDOM from "react-dom/client";
import {
  createRootRoute,
  createRoute,
  createRouter,
  RouterProvider,
  Outlet,
  useLocation,
  Navigate,
} from "@tanstack/react-router";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import NewJob from "./pages/NewJob";
import Dashboard from "./pages/dashboard/Dashboard";
import JobsPage from "./pages/dashboard/JobsPage";
import JobDetail from "./pages/dashboard/JobDetail";
import CandidateDetail from "./pages/dashboard/CandidateDetail";
import ProfilePage from "./pages/dashboard/ProfilePage";
import InterviewSummaryPage from "./pages/dashboard/InterviewSummaryPage";
import ApplyPage from "./pages/apply/ApplyPage";
import "./index.css";
import LoginPage from "./pages/LoginPage";
import { authMe } from "./api/auth";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 60_000, retry: 1 },
  },
});

function RootLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <SessionGate />
    </QueryClientProvider>
  );
}

function SessionGate() {
  const location = useLocation();
  const publicPage = location.pathname.startsWith("/apply/") || location.pathname === "/login";
  const { data: identity, isLoading, error } = useQuery({
    queryKey: ["auth-me"], queryFn: authMe, enabled: !publicPage, retry: false,
    staleTime: 0, refetchOnWindowFocus: true,
  });
  if (publicPage) return <Outlet />;
  if (isLoading) return <p className="p-8">Loading recruiter session…</p>;
  if (error) return <p role="alert" className="p-8">Session unavailable. Please refresh.</p>;
  if (!identity) return <Navigate to="/login" />;
  return <Outlet />;
}

const rootRoute = createRootRoute({ component: RootLayout });
const loginRoute = createRoute({ getParentRoute: () => rootRoute, path: "/login", component: LoginPage });

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
  loginRoute,
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
