// src/components/NavBar.jsx
import { Link, useNavigate } from "@tanstack/react-router";

export default function NavBar() {
  const navigate = useNavigate();

  return (
    <nav className="bg-white border-b border-gray-100 px-6 h-14 flex items-center justify-between sticky top-0 z-10">

      {/* Logo */}
      <button
        onClick={() => navigate({ to: "/dashboard" })}
        className="flex items-center gap-2 cursor-pointer"
      >
        <div className="w-7 h-7 bg-green-700 rounded-lg flex items-center justify-center">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <circle cx="7" cy="7" r="4" stroke="white" strokeWidth="1.5"/>
            <path d="M7 3V7L9.5 9.5" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
        </div>
        <span className="text-sm font-semibold text-gray-900 tracking-tight">Prometheus</span>
      </button>

      {/* Links */}
      <div className="flex items-center gap-1">
        <Link
          to="/dashboard"
          className="text-sm text-gray-400 hover:text-gray-700 hover:bg-gray-50 px-3 py-1.5 rounded-lg transition-all"
          activeProps={{ className: "text-sm text-green-700 bg-green-50 px-3 py-1.5 rounded-lg font-medium" }}
        >
          Dashboard
        </Link>
        <Link
          to="/jobs/new"
          className="text-sm text-gray-400 hover:text-gray-700 hover:bg-gray-50 px-3 py-1.5 rounded-lg transition-all"
          activeProps={{ className: "text-sm text-green-700 bg-green-50 px-3 py-1.5 rounded-lg font-medium" }}
        >
          New job
        </Link>
      </div>

      {/* Right side */}
      <button
        onClick={() => navigate({ to: "/jobs/new" })}
        className="text-sm px-4 py-1.5 bg-green-700 text-white rounded-lg hover:bg-green-600 cursor-pointer transition-all"
      >
        + New job
      </button>

    </nav>
  );
}