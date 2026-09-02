import { useState, useEffect } from 'react';
import { ExecutionGraph } from './ExecutionGraph';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { Play, Pause, SkipForward, RotateCcw } from 'lucide-react';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const API_BASE_URL = 'http://localhost:8000/api/v1';

export function AgenticActionsView() {
  const [activeSession, setActiveSession] = useState<string | null>(null);
  const [queue, setQueue] = useState<any[]>([]);
  const [config, setConfig] = useState<any>({ delay_seconds: 30, is_paused: false, countdown_remaining: 0, is_counting_down: false });

  const fetchQueue = async () => {
    try {
      const headers = { 'X-API-Key': import.meta.env.VITE_DASHBOARD_API_KEY || '' };
      const res = await fetch(`${API_BASE_URL}/dashboard/queue`, { headers, cache: 'no-store' });
      if (res.ok) {
        const data = await res.json();
        setQueue(data);
        if (data.length > 0 && !activeSession) {
          setActiveSession(data[0].session_id);
        }
      }
    } catch (e) {
      console.error("Failed to fetch queue", e);
    }
  };

  const fetchConfig = async () => {
    try {
      const headers = { 'X-API-Key': import.meta.env.VITE_DASHBOARD_API_KEY || '' };
      const res = await fetch(`${API_BASE_URL}/dashboard/queue/config`, { headers, cache: 'no-store' });
      if (res.ok) {
        setConfig(await res.json());
      }
    } catch (e) {
      console.error("Failed to fetch config", e);
    }
  };

  useEffect(() => {
    fetchQueue();
    fetchConfig();
    const interval = setInterval(() => {
      fetchQueue();
      fetchConfig();
    }, 1000); // Poll fast for countdown
    return () => clearInterval(interval);
  }, [activeSession]);

  const setDelay = async (delay: number) => {
    await fetch(`${API_BASE_URL}/dashboard/queue/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': import.meta.env.VITE_DASHBOARD_API_KEY || '' },
      body: JSON.stringify({ delay_seconds: delay })
    });
    fetchConfig();
  };

  const togglePause = async () => {
    const endpoint = config.is_paused ? 'resume' : 'pause';
    await fetch(`${API_BASE_URL}/dashboard/queue/${endpoint}`, {
      method: 'POST',
      headers: { 'X-API-Key': import.meta.env.VITE_DASHBOARD_API_KEY || '' }
    });
    fetchConfig();
  };

  const skipNext = async () => {
    await fetch(`${API_BASE_URL}/dashboard/queue/next`, {
      method: 'POST',
      headers: { 'X-API-Key': import.meta.env.VITE_DASHBOARD_API_KEY || '' }
    });
    fetchConfig();
  };

  const retrySession = async () => {
    if (!activeSession) return;
    await fetch(`${API_BASE_URL}/dashboard/execution/${activeSession}/retry`, {
      method: 'POST',
      headers: { 'X-API-Key': import.meta.env.VITE_DASHBOARD_API_KEY || '' }
    });
    fetchQueue();
  };

  return (
    <div className="flex flex-col h-full w-full bg-slate-50 relative">
      {/* Top Bar - Mission Control */}
      <div className="h-20 bg-white border-b border-slate-200 px-6 flex items-center justify-between shadow-sm z-10 shrink-0">
        
        {/* Left: Queue Status */}
        <div className="flex items-center gap-6">
          <div className="flex flex-col">
            <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider">Mission Control</h2>
            <div className="text-xs text-slate-500 font-medium">Session Queue</div>
          </div>
          
          <div className="flex gap-2 items-center overflow-x-auto max-w-[400px] py-2">
            {queue.map(q => (
              <button 
                key={q.session_id}
                onClick={() => setActiveSession(q.session_id)}
                className={cn(
                  "flex flex-col text-left px-3 py-1.5 rounded-lg border min-w-[120px] transition-all",
                  activeSession === q.session_id 
                    ? "bg-blue-50 border-blue-200 ring-1 ring-blue-500" 
                    : "bg-white border-slate-200 hover:border-slate-300"
                )}
              >
                <div className="flex justify-between items-center w-full">
                  <span className="text-[10px] font-bold text-slate-500">#{q.position}</span>
                  <span className={cn("w-1.5 h-1.5 rounded-full", 
                    q.status === 'RUNNING' ? 'bg-blue-500 animate-pulse' :
                    q.status === 'WAITING' ? 'bg-amber-500' :
                    q.status === 'FAILED' ? 'bg-red-500' :
                    'bg-slate-300'
                  )} />
                </div>
                <div className="text-xs font-semibold text-slate-700 truncate">{q.session_id.substring(0, 8)}...</div>
              </button>
            ))}
            {queue.length === 0 && (
              <div className="text-xs text-slate-400 italic">No high-intent sessions</div>
            )}
          </div>
        </div>

        {/* Right: Controls & Countdown */}
        <div className="flex items-center gap-4">
          
          {config.is_counting_down && (
            <div className="flex flex-col items-center justify-center mr-4">
              <span className="text-[10px] font-bold text-amber-600 uppercase tracking-widest">Next In</span>
              <span className="text-lg font-black text-slate-700 font-mono leading-none">{config.countdown_remaining}s</span>
            </div>
          )}

          <div className="flex items-center bg-slate-100 rounded-lg p-1 border border-slate-200 shadow-inner">
            <input 
              type="number"
              min="1"
              value={
                config.delay_seconds >= 3600 && config.delay_seconds % 3600 === 0 ? config.delay_seconds / 3600 :
                config.delay_seconds >= 60 && config.delay_seconds % 60 === 0 ? config.delay_seconds / 60 :
                config.delay_seconds
              }
              onChange={(e) => {
                const val = parseInt(e.target.value) || 1;
                const unit = 
                  config.delay_seconds >= 3600 && config.delay_seconds % 3600 === 0 ? 3600 :
                  config.delay_seconds >= 60 && config.delay_seconds % 60 === 0 ? 60 : 1;
                setDelay(val * unit);
              }}
              className="w-12 bg-transparent border-none text-xs font-bold text-slate-700 focus:ring-0 outline-none text-center p-0"
            />
            <select
              value={
                config.delay_seconds >= 3600 && config.delay_seconds % 3600 === 0 ? 3600 :
                config.delay_seconds >= 60 && config.delay_seconds % 60 === 0 ? 60 : 1
              }
              onChange={(e) => {
                const unit = parseInt(e.target.value);
                const currentVal = 
                  config.delay_seconds >= 3600 && config.delay_seconds % 3600 === 0 ? config.delay_seconds / 3600 :
                  config.delay_seconds >= 60 && config.delay_seconds % 60 === 0 ? config.delay_seconds / 60 :
                  config.delay_seconds;
                setDelay(currentVal * unit);
              }}
              className="bg-transparent border-none text-xs font-semibold text-slate-500 focus:ring-0 cursor-pointer outline-none p-0 pr-6 ml-1"
            >
              <option value="1">Seconds</option>
              <option value="60">Minutes</option>
              <option value="3600">Hours</option>
            </select>
          </div>

          <div className="flex gap-1">
            <button 
              onClick={togglePause}
              className={cn("p-2 rounded-md transition-colors", 
                config.is_paused ? "bg-amber-100 text-amber-700" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              )}
              title={config.is_paused ? "Resume Queue" : "Pause Queue"}
            >
              {config.is_paused ? <Play size={16} /> : <Pause size={16} />}
            </button>
            
            <button 
              onClick={skipNext}
              disabled={!config.is_counting_down}
              className="p-2 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Start Next Now"
            >
              <SkipForward size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Main Execution Graph Area */}
      <div className="flex-1 relative bg-white">
        {activeSession ? (
          <ExecutionGraph sessionId={activeSession} />
        ) : (
          <div className="h-full flex items-center justify-center text-slate-400">
            <p>Waiting for sessions...</p>
          </div>
        )}
      </div>

      {/* Retry Button Overlay */}
      {activeSession && (
        <button
          onClick={retrySession}
          className="absolute bottom-6 right-6 flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-full shadow-lg font-semibold text-sm transition-transform hover:-translate-y-0.5 active:translate-y-0 z-50"
        >
          <RotateCcw size={16} />
          Retry Session
        </button>
      )}
    </div>
  );
}
