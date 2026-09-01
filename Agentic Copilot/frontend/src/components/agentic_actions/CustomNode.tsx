import { Handle, Position } from '@xyflow/react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function CustomNode({ data }: { data: any }) {
  const isOrchestrator = data.type === 'orchestrator';
  const isAgent = data.type === 'agent';
  
  // Status colors
  const statusColor = 
    data.status === 'RUNNING' ? 'bg-blue-500' :
    data.status === 'FAILED' ? 'bg-red-500' :
    data.status === 'WAITING' ? 'bg-amber-500' :
    'bg-gray-300'; // IDLE, COMPLETED, etc.
    
  // Node type colors (left bar)
  const typeColor = 
    isOrchestrator ? 'bg-indigo-500' :
    isAgent ? 'bg-violet-400' :
    'bg-slate-300';

  return (
    <div className={cn(
      "flex items-center p-3.5 rounded-xl border relative w-[240px] h-[72px] transition-all duration-300 ease-in-out group",
      isOrchestrator 
        ? "bg-white/95 backdrop-blur-sm border-indigo-200 shadow-[0_8px_30px_rgb(0,0,0,0.08)] ring-1 ring-indigo-50 z-10" 
        : "bg-white/90 backdrop-blur-sm border-slate-200/80 shadow-[0_4px_20px_rgb(0,0,0,0.04)] hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] hover:-translate-y-0.5 z-0",
      data.status === 'RUNNING' && "ring-2 ring-blue-400/40 border-blue-300 shadow-[0_0_20px_rgba(59,130,246,0.15)]",
      data.status === 'FAILED' && "ring-2 ring-red-400/40 border-red-300 shadow-[0_0_20px_rgba(239,68,68,0.15)]"
    )}>
      {/* Sleek left color bar */}
      <div className={cn("absolute left-0 top-0 bottom-0 w-1 rounded-l-xl opacity-80 group-hover:opacity-100 transition-opacity", typeColor)} />
      
      {/* 4-way Handles (Invisible for clean center-routing) */}
      <Handle type="target" position={Position.Top} id="t-top" className="opacity-0" />
      <Handle type="source" position={Position.Top} id="s-top" className="opacity-0" />
      
      <Handle type="target" position={Position.Bottom} id="t-bottom" className="opacity-0" />
      <Handle type="source" position={Position.Bottom} id="s-bottom" className="opacity-0" />
      
      <Handle type="target" position={Position.Left} id="t-left" className="opacity-0" />
      <Handle type="source" position={Position.Left} id="s-left" className="opacity-0" />
      
      <Handle type="target" position={Position.Right} id="t-right" className="opacity-0" />
      <Handle type="source" position={Position.Right} id="s-right" className="opacity-0" />

      <div className="ml-3 flex-1 flex flex-col justify-center">
        <div className="text-[9px] font-bold text-slate-400 uppercase tracking-[0.2em] mb-0.5">
          {data.type}
        </div>
        <div className={cn(
          "font-semibold text-slate-800 leading-tight whitespace-pre-wrap",
          isOrchestrator ? "text-[13px]" : "text-xs"
        )}>
          {data.label.replace('\n', ' - ')}
        </div>
        
        {/* Inline Status */}
        {data.id !== 'n_session' ? (
          <div className="mt-1 flex items-center text-[9px] font-semibold text-slate-500 uppercase tracking-wider">
            <span className={cn("w-1.5 h-1.5 rounded-full mr-1.5 shadow-sm", statusColor, data.status === 'RUNNING' && "animate-pulse")} />
            {data.status}
          </div>
        ) : (
          <div className="mt-1 flex flex-col gap-0.5 text-[9px] font-medium text-slate-500">
            {data.details?.session_id && <div>ID: {data.details.session_id.substring(0, 8)}...</div>}
            {data.details?.intent_score !== undefined && <div>Intent: {data.details.intent_score}%</div>}
          </div>
        )}
      </div>
    </div>
  );
}
