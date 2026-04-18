// src/components/NavBar.jsx
import { Link, useNavigate } from "@tanstack/react-router";

export default function NavBar() {
  const navigate = useNavigate();

  return (
    <nav className="bg-white border-b border-gray-100 px-6 h-14 flex items-center justify-between sticky top-0 z-10">
      
      {/* Logo */}
      <button
        onClick={() => navigate({ to: "/dashboard" })}
        className="text-sm font-semibold text-gray-900 tracking-tight cursor-pointer"
      >
        Prometheus
      </button>

      {/* Links */}
      <div className="flex items-center gap-6">
        <Link
          to="/dashboard"
          className="text-sm text-gray-400 hover:text-gray-700 transition-colors"
          activeProps={{ className: "text-sm text-gray-900 font-medium" }}
        >
          Dashboard
        </Link>
        <Link
          to="/jobs/new"
          className="text-sm text-gray-400 hover:text-gray-700 transition-colors"
          activeProps={{ className: "text-sm text-gray-900 font-medium" }}
        >
          New job
        </Link>
      </div>

    </nav>
  );
}