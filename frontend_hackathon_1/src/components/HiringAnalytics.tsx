const weekData = [
  { day: 'S', value: 45, label: '45%' },
  { day: 'M', value: 60, label: '60%' },
  { day: 'T', value: 78, label: '78%' },
  { day: 'W', value: 55, label: '55%' },
  { day: 'T', value: 70, label: '70%' },
  { day: 'F', value: 65, label: '65%' },
  { day: 'S', value: 40, label: '40%' },
];

export function HiringAnalytics() {
  return (
    <div className="bg-card border border-border rounded-2xl p-5">
      <h3 className="font-semibold text-foreground mb-6">Hiring Analytics</h3>
      <div className="flex items-end justify-between gap-2 h-40">
        {weekData.map((item, index) => (
          <div key={index} className="flex flex-col items-center gap-2 flex-1">
            <div className="relative w-full flex justify-center">
              {item.value === 78 && (
                <span className="absolute -top-6 text-xs font-medium text-primary">{item.label}</span>
              )}
              <div
                className="w-8 rounded-t-lg transition-all duration-300 hover:opacity-80"
                style={{
                  height: `${item.value * 1.5}px`,
                  background:
                    item.value === 78
                      ? 'linear-gradient(to top, #2d6a4f, #40916c)'
                      : 'repeating-linear-gradient(to top, #d8f3dc 0px, #d8f3dc 4px, transparent 4px, transparent 8px)',
                }}
              />
            </div>
            <span className="text-xs text-muted-foreground font-medium">{item.day}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
