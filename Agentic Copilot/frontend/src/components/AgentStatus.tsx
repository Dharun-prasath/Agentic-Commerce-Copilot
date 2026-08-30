interface AgentStatusProps {
  name: string;
  reqs: string;
  health: 'optimal' | 'idle' | 'warning';
}

export function AgentStatus({ name, reqs, health }: AgentStatusProps) {
  const getStatusColor = () => {
    if (health === 'optimal') return 'bg-[#00d26a]';
    if (health === 'warning') return 'bg-[#f5a623]';
    return 'bg-gray-300';
  };

  return (
    <div className="flex items-center justify-between py-2.5 border-b border-gray-100 last:border-0 hover:bg-gray-50/50 transition-colors px-1">
      <div className="flex items-center">
        <div className={`w-2 h-2 rounded-full mr-3 ${getStatusColor()} ${health === 'optimal' ? 'shadow-[0_0_6px_rgba(0,210,106,0.5)]' : ''}`} />
        <span className="text-[14px] font-semibold text-gray-900">{name}</span>
      </div>
      <span className="text-[12px] font-bold text-gray-500 bg-gray-50 px-2 py-0.5 rounded border border-gray-200">
        {reqs}
      </span>
    </div>
  );
}
