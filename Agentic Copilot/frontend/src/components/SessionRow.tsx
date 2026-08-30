interface SessionRowProps {
  id: string;
  user: string;
  intent: string;
  status: string;
  action: string;
  time: string;
  active?: boolean | 'green';
  onClick?: () => void;
}

export function SessionRow({ id, user, intent, status, action, time, active, onClick }: SessionRowProps) {
  return (
    <div 
      onClick={onClick}
      className="flex items-center justify-between py-3.5 border-b border-gray-100 last:border-0 hover:bg-gray-50/50 transition-colors px-1 cursor-pointer"
    >
      <div className="flex items-center w-[30%]">
        <div className={`w-2 h-2 rounded-full mr-3 ${
          active === 'green' ? 'bg-[#00d26a] shadow-[0_0_6px_rgba(0,210,106,0.5)]' : 
          active ? 'bg-[#3366ff] shadow-[0_0_6px_rgba(51,102,255,0.5)]' : 
          'bg-gray-300'
        }`} />
        <div>
          <div className="text-[14px] font-bold text-gray-900">{user}</div>
          <div className="text-[12px] text-gray-500 font-medium">{id}</div>
        </div>
      </div>
      
      <div className="w-[30%] flex flex-col">
        <div className="flex items-center">
          <span className="text-[13px] font-bold text-gray-700 w-10">{intent}</span>
          <div className="w-24 bg-gray-200 h-1.5 rounded-full overflow-hidden ml-2">
            <div 
              className={`h-full rounded-full ${
                active === 'green' ? 'bg-[#00d26a]' : 
                active ? 'bg-[#3366ff]' : 
                'bg-gray-400'
              }`} 
              style={{ width: intent }}
            />
          </div>
        </div>
        <span className={`text-[11px] font-bold uppercase tracking-wider mt-1 ${
          active === 'green' ? 'text-[#00d26a]' : 
          active ? 'text-[#3366ff]' : 
          'text-gray-400'
        }`}>{status}</span>
      </div>
      
      <div className="w-[25%]">
        <div className="text-[13px] font-semibold text-gray-800">{action}</div>
      </div>

      <div className="w-[15%] text-right">
        <span className="text-[12px] font-medium text-gray-500">{time}</span>
      </div>
    </div>
  );
}
