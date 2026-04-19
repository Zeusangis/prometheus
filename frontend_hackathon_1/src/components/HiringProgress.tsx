export function HiringProgress() {
  const progress = 41;

  return (
    <div className="bg-card border border-border rounded-2xl p-5">
      <h3 className="font-semibold text-foreground mb-4">Hiring Progress</h3>
      <div className="flex flex-col items-center">
        <div className="relative w-40 h-40">
          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="40" fill="none" stroke="#d8f3dc" strokeWidth="12" />
            <circle
              cx="50"
              cy="50"
              r="40"
              fill="none"
              stroke="url(#progressGradient)"
              strokeWidth="12"
              strokeLinecap="round"
              strokeDasharray={`${progress * 2.51} 251`}
            />
            <defs>
              <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#2d6a4f" />
                <stop offset="100%" stopColor="#52b788" />
              </linearGradient>
            </defs>
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-bold text-foreground">{progress}%</span>
            <span className="text-xs text-muted-foreground">Positions Filled</span>
          </div>
        </div>
        <div className="flex items-center gap-6 mt-4">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-primary" />
            <span className="text-xs text-muted-foreground">Completed</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-blue-500" />
            <span className="text-xs text-muted-foreground">In Progress</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-orange-400" />
            <span className="text-xs text-muted-foreground">Pending</span>
          </div>
        </div>
      </div>
    </div>
  );
}
