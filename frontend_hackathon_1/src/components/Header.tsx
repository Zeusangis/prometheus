export function Header() {
  return (
    <header className="flex items-center justify-between py-4 px-6">
      {/* Search */}
      <div className="relative flex-1 max-w-md">
        <svg
          className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <input
          type="text"
          placeholder="Search candidates, jobs..."
          className="w-full pl-12 pr-16 py-3 bg-card border border-border rounded-xl text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
        />
        <span className="absolute right-4 top-1/2 -translate-y-1/2 text-xs text-muted-foreground bg-secondary px-2 py-1 rounded">
          Ctrl F
        </span>
      </div>

      {/* Right Section */}
      <div className="flex items-center gap-4 ml-6">
        {/* Mail */}
        <button className="w-10 h-10 bg-card border border-border rounded-xl flex items-center justify-center hover:bg-secondary transition-colors">
          <svg className="w-5 h-5 text-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
            />
          </svg>
        </button>

        {/* Notifications */}
        <button className="relative w-10 h-10 bg-card border border-border rounded-xl flex items-center justify-center hover:bg-secondary transition-colors">
          <svg className="w-5 h-5 text-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
            />
          </svg>
          <span className="absolute -top-1 -right-1 w-4 h-4 bg-danger text-white text-xs rounded-full flex items-center justify-center">
            3
          </span>
        </button>

        {/* User Profile */}
        <div className="flex items-center gap-3 pl-4 border-l border-border">
          <img
            src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop&crop=face"
            alt="User avatar"
            className="w-10 h-10 rounded-full object-cover"
          />
          <div>
            <p className="font-semibold text-foreground text-sm">John Mitchell</p>
            <p className="text-xs text-muted-foreground">HR Manager</p>
          </div>
        </div>
      </div>
    </header>
  );
}
