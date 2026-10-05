import { useState, useEffect } from 'react';

export function TimeTracker() {
  const [time, setTime] = useState(5048); // Starting at 01:24:08
  const [isRunning, setIsRunning] = useState(true);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | undefined;
    if (isRunning) {
      interval = setInterval(() => {
        setTime((prev) => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isRunning]);

  const formatTime = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  return (
    <div className="bg-gradient-to-br from-primary-dark to-primary rounded-2xl p-5 text-white overflow-hidden relative">
      {/* Decorative circles */}
      <div className="absolute -right-8 -bottom-8 w-32 h-32 border-4 border-white/10 rounded-full" />
      <div className="absolute -right-4 -bottom-4 w-24 h-24 border-4 border-white/10 rounded-full" />
      <div className="absolute -right-0 -bottom-0 w-16 h-16 border-4 border-white/10 rounded-full" />

      <h3 className="font-semibold mb-4 relative z-10">Time Tracker</h3>
      <p className="text-4xl font-bold mb-6 font-mono tracking-wider relative z-10">{formatTime(time)}</p>
      <div className="flex gap-3 relative z-10">
        <button
          onClick={() => setIsRunning(!isRunning)}
          className="w-12 h-12 bg-white/20 hover:bg-white/30 rounded-xl flex items-center justify-center transition-colors"
        >
          {isRunning ? (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
          )}
        </button>
        <button
          onClick={() => {
            setIsRunning(false);
            setTime(0);
          }}
          className="w-12 h-12 bg-white/20 hover:bg-white/30 rounded-xl flex items-center justify-center transition-colors"
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M6 6h12v12H6z" />
          </svg>
        </button>
      </div>
    </div>
  );
}
