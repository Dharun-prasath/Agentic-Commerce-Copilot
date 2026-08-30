import { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { KpiCard } from './components/KpiCard';
import { SessionRow } from './components/SessionRow';
import { AgentStatus } from './components/AgentStatus';
import { Customer360 } from './components/Customer360';
import { AgentsConfigView } from './components/AgentsConfigView';
import { ApiConfigView } from './components/ApiConfigView';

const API_BASE_URL = 'http://localhost:8000/api/v1';

function App() {
  const [activeTab, setActiveTab] = useState('overview');
  
  const [stats, setStats] = useState({
    active_sessions: "0",
    high_intent: "0",
    calls_triggered: "0",
    revenue: "₹0"
  });
  
  const [sessions, setSessions] = useState<any[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [agentConfigs, setAgentConfigs] = useState<any[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const headers = {
          'X-API-Key': import.meta.env.VITE_DASHBOARD_API_KEY || ''
        };
        
        const statsRes = await fetch(`${API_BASE_URL}/dashboard/stats`, { headers, cache: 'no-store' });
        if (statsRes.ok) {
          setStats(await statsRes.json());
        }
        
        const sessionsRes = await fetch(`${API_BASE_URL}/dashboard/sessions`, { headers, cache: 'no-store' });
        if (sessionsRes.ok) {
          setSessions(await sessionsRes.json());
        }

        const configsRes = await fetch(`${API_BASE_URL}/agents/config`, { headers, cache: 'no-store' });
        if (configsRes.ok) {
          setAgentConfigs(await configsRes.json());
        }
      } catch (e) {
        console.error("Failed to fetch dashboard data", e);
      }
    };
    
    // Initial fetch
    fetchData();
    
    // Poll every 5 seconds
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-screen flex flex-col text-gray-900 bg-[#f3f4f6] font-sans selection:bg-[#3366ff]/20 overflow-hidden relative">
      {/* Top Navbar spans full width */}
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />
      
      {/* Main Layout Area below Navbar */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto w-full">
          <div className="p-8">
            <div className="max-w-[1200px] mx-auto">
              {activeTab === 'overview' ? (
                <>
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-[22px] font-bold text-gray-900">
                      Dashboard Overview
                    </h2>
                    <div className="flex items-center space-x-2 text-sm bg-white border border-gray-200 px-3 py-1.5 rounded-full shadow-sm">
                      <span className="h-2 w-2 rounded-full bg-[#00d26a] shadow-[0_0_6px_rgba(0,210,106,0.4)]"></span>
                      <span className="text-gray-900 font-bold text-[12px] uppercase tracking-wide">System Online</span>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-5 mb-8">
                    <KpiCard 
                      title="Active Sessions" 
                      value={stats.active_sessions} 
                    />
                    <KpiCard 
                      title="High Intent Detected" 
                      value={stats.high_intent} 
                    />
                    <KpiCard 
                      title="Calls Triggered" 
                      value={stats.calls_triggered} 
                    />
                    <KpiCard 
                      title="Commerce Actions" 
                      value={stats.revenue} 
                    />
                  </div>

                  <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                    <div className="xl:col-span-2 bg-white rounded-2xl p-6 shadow-[0_2px_8px_rgba(0,0,0,0.04)] border border-gray-100">
                      <div className="flex items-center justify-between mb-6">
                        <h3 className="text-[16px] font-bold text-gray-900">
                          Live Customer Journeys
                        </h3>
                        <button 
                          onClick={() => setActiveTab('live')}
                          className="text-[13px] font-bold text-[#3366ff] hover:text-[#2b56d9] transition-colors"
                        >
                          View All
                        </button>
                      </div>
                      
                      <div className="border-t border-gray-100 min-h-[300px]">
                        {sessions.length > 0 ? (
                          sessions.map((s) => (
                            <SessionRow 
                              key={s.id}
                              id={s.id.substring(0, 8)} 
                              user={s.user} 
                              intent={s.intent} 
                              status={s.status} 
                              action={s.action}
                              time={s.time}
                              active={s.active}
                              onClick={() => setSelectedSessionId(s.id)}
                            />
                          ))
                        ) : (
                          <div className="p-8 text-center text-gray-500">No active sessions found.</div>
                        )}
                      </div>
                    </div>

                    <div className="bg-white rounded-2xl p-6 shadow-[0_2px_8px_rgba(0,0,0,0.04)] border border-gray-100">
                      <h3 className="text-[16px] font-bold text-gray-900 mb-6">
                        Agent Systems
                      </h3>
                      
                      <div className="border-t border-gray-100">
                        {agentConfigs.length > 0 ? (
                          agentConfigs.map((cfg) => {
                            const meta = {
                              intent: 'Intent Agent',
                              sales: 'Sales Consultant',
                              product: 'Product Intelligence',
                              commerce: 'Commerce Agent'
                            }[cfg.agent_id] || cfg.agent_id;
                            
                            return (
                              <AgentStatus 
                                key={cfg.agent_id}
                                name={meta} 
                                reqs={cfg.is_active ? "Online" : "Paused"} 
                                health={cfg.is_active ? "optimal" : "idle"} 
                              />
                            );
                          })
                        ) : (
                          <div className="py-4 text-center text-gray-500 text-sm">Loading Agents...</div>
                        )}
                      </div>
                    </div>
                  </div>
                </>
              ) : activeTab === 'live' ? (
                <>
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-[22px] font-bold text-gray-900">
                      Live Customer Journeys
                    </h2>
                  </div>
                  <div className="bg-white rounded-2xl p-6 shadow-[0_2px_8px_rgba(0,0,0,0.04)] border border-gray-100 min-h-[600px]">
                    <div className="border-b border-gray-100 pb-4 mb-4 grid grid-cols-12 gap-4 text-[12px] font-bold text-gray-500 uppercase tracking-wider">
                      <div className="col-span-3">Customer</div>
                      <div className="col-span-2">Intent Score</div>
                      <div className="col-span-3">Status</div>
                      <div className="col-span-2">Last Action</div>
                      <div className="col-span-2 text-right">Time</div>
                    </div>
                    {sessions.length > 0 ? (
                      sessions.map((s) => (
                        <SessionRow 
                          key={s.id}
                          id={s.id.substring(0, 8)} 
                          user={s.user} 
                          intent={s.intent} 
                          status={s.status} 
                          action={s.action}
                          time={s.time}
                          active={s.active}
                          onClick={() => setSelectedSessionId(s.id)}
                        />
                      ))
                    ) : (
                      <div className="p-12 text-center text-gray-500 text-lg">No active sessions found.</div>
                    )}
                  </div>
                </>
              ) : activeTab === 'agents' ? (
                <AgentsConfigView />
              ) : activeTab === 'api' ? (
                <ApiConfigView />
              ) : (
                <div className="p-12 text-center text-gray-500 text-lg">
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">Coming Soon</h2>
                  <p>This module is currently under development.</p>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
      
      {/* Overlay for Customer360 panel */}
      {selectedSessionId && (
        <div 
          className="fixed inset-0 bg-black/20 z-40 transition-opacity" 
          onClick={() => setSelectedSessionId(null)}
        />
      )}
      <Customer360 
        sessionId={selectedSessionId} 
        onClose={() => setSelectedSessionId(null)} 
      />
    </div>
  );
}

export default App;
