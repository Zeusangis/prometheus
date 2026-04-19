export function Reminders() {
  return (
    <div className="bg-card border border-border rounded-2xl p-5">
      <h3 className="font-semibold text-foreground mb-4">Reminders</h3>
      <div className="space-y-3">
        <h4 className="text-lg font-bold text-foreground">Interview with Sarah Chen</h4>
        <p className="text-sm text-muted-foreground">Time : 02.00 pm - 03.00 pm</p>
        <button className="w-full bg-primary hover:bg-primary-light text-white font-semibold py-3 rounded-xl transition-colors flex items-center justify-center gap-2 mt-4">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
            />
          </svg>
          Start Interview
        </button>
      </div>
    </div>
  );
}
