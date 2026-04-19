interface StatCardProps {
  title: string;
  value: string | number;
  subtitle: string;
  highlighted?: boolean;
}

export function StatCard({ title, value, subtitle, highlighted = false }: StatCardProps) {
  return (
    <div
      className={`rounded-2xl p-5 transition-all duration-200 ${
        highlighted
          ? 'bg-gradient-to-br from-primary to-primary-light text-white'
          : 'bg-card border border-border hover:border-primary/30'
      }`}
    >
      <div className="flex items-start justify-between mb-4">
        <h3 className={`text-sm font-medium ${highlighted ? 'text-white/80' : 'text-muted-foreground'}`}>
          {title}
        </h3>
        <button
          className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${
            highlighted ? 'bg-white/20 hover:bg-white/30' : 'bg-secondary hover:bg-accent'
          }`}
        >
          <svg
            className={`w-4 h-4 ${highlighted ? 'text-white' : 'text-foreground'}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 17L17 7M17 7H7M17 7V17" />
          </svg>
        </button>
      </div>
      <p className={`text-4xl font-bold mb-2 ${highlighted ? 'text-white' : 'text-foreground'}`}>{value}</p>
      <div className="flex items-center gap-2">
        <span
          className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full ${
            highlighted ? 'bg-white/20 text-white' : 'bg-secondary text-primary'
          }`}
        >
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
          </svg>
        </span>
        <span className={`text-xs ${highlighted ? 'text-white/80' : 'text-muted-foreground'}`}>{subtitle}</span>
      </div>
    </div>
  );
}
