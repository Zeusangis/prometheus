// src/main.jsx
import React from "react";
import ReactDOM from "react-dom/client";
import {
  createRouter,
  createRoute,
  createRootRoute,
  RouterProvider,
  Outlet,
} from "@tanstack/react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import NewJob from "./pages/NewJob";
import Dashboard from "./pages/dashboard/Dashboard";
import JobDetail from "./pages/dashboard/JobDetail";
import CandidateDetail from "./pages/dashboard/CandidateDetail";
import NavBar from "./components/NavBar";
import ApplyPage from "./pages/apply/ApplyPage";
import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 1000 * 60, retry: 1 },
  },
});

function RootLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <NavBar />
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
  jobDetailRoute,
  candidateDetailRoute,
  applyRoute,
  newJobRoute,
]);

const router = createRouter({ routeTree });

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>
);