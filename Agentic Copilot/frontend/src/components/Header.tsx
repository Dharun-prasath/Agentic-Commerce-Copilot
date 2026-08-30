import { Search } from 'lucide-react';

export function Header({ activeTab, setActiveTab }: { activeTab: string, setActiveTab: (id: string) => void }) {
  const navItems = [
    { id: 'overview', label: 'Overview' },
    { id: 'live', label: 'Live Sessions' },
    { id: 'calls', label: 'Calls' },
    { id: 'commerce', label: 'Commerce Actions' },
    { id: 'agents', label: 'Agents' },
    { id: 'api', label: 'API' },
  ];

  return (
    <header className="h-[60px] flex items-center shrink-0 z-20 relative border-b border-gray-200 bg-white">
      {/* Left: Logo Section */}
      <div className="flex items-center w-auto px-5 shrink-0">
        <img src="/logo.png" alt="Agentic Copilot Logo" className="w-12 h-12 mr-2 object-contain" />
        <h1 className="text-[15px] font-bold tracking-wide text-gray-900 mr-8">
          Agentic Copilot
        </h1>
      </div>

      {/* Center: Navigation Links */}
      <div className="flex items-center space-x-6 h-full flex-1">
        {navItems.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`text-[13px] font-medium transition-colors ${
                isActive 
                  ? 'text-gray-900 font-bold border-b-2 border-[#3366ff] h-[60px] translate-y-[1px]' 
                  : 'text-gray-500 hover:text-gray-900 h-[60px]'
              }`}
            >
              {item.label}
            </button>
          );
        })}
      </div>

      {/* Right: Search and Action Buttons */}
      <div className="flex items-center space-x-4 px-6 h-full">
        <div className="relative flex items-center mr-2">
          <Search size={14} className="absolute left-3.5 text-gray-400" />
          <input 
            type="text" 
            placeholder="Search..." 
            className="w-[240px] h-9 pl-10 pr-4 text-[13px] bg-gray-50 border border-gray-200 rounded-full focus:outline-none focus:border-[#3366ff] placeholder-gray-400 transition-colors shadow-[inset_0_1px_2px_rgba(0,0,0,0.02)]"
          />
        </div>
        
        <button className="text-[13px] font-medium text-gray-500 hover:text-gray-900 transition-colors">
          Support
        </button>
        <button className="text-[13px] font-medium text-gray-500 hover:text-gray-900 transition-colors">
          Docs
        </button>
        <span className="text-gray-300">|</span>
        <button 
          onClick={() => {
            fetch('http://127.0.0.1:3456/simulate', { method: 'POST' }).catch(e => console.error(e))
          }}
          className="h-8 px-4 text-[12px] bg-[#3366ff] hover:bg-[#2b56d9] text-white rounded-full font-bold transition-colors shadow-sm tracking-wide"
        >
          Simulate Call
        </button>
      </div>
    </header>
  );
}
