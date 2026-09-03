import React, { useState, useEffect } from 'react';

const API_BASE_URL = 'http://localhost:8000/api/v1';

interface AgentConfig {
  id: string;
  agent_id: string;
  is_active: boolean;
  model_name: string;
  temperature: number;
  top_p: number;
  top_k: number;
  max_output_tokens: number;
  system_prompt: string;
  context_memory_size: number;
  capabilities: Record<string, any>;
  fallback_behavior: string;
  output_formatting: string;
  processing_timeout_ms: number;
}

const AGENT_META = {
  intent: { name: 'Intent Agent', desc: 'Analyzes user messages to determine buying intent.' },
  sales: { name: 'Sales Consultant', desc: 'Engages in conversational sales and handles objections.' },
  product: { name: 'Product Intelligence', desc: 'Expert on product catalog, features, and comparisons.' },
};

export const AgentsConfigView: React.FC = () => {
  const [configs, setConfigs] = useState<AgentConfig[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<string>('intent');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    const fetchConfigs = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/agents/config`);
        if (res.ok) {
          const data = await res.json();
          setConfigs(data);
        }
      } catch (err) {
        console.error("Failed to fetch agent configs:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchConfigs();
  }, []);

  const activeConfig = configs.find(c => c.agent_id === selectedAgentId);

  const handleUpdate = (field: keyof AgentConfig, value: any) => {
    setConfigs(prev => prev.map(c => 
      c.agent_id === selectedAgentId ? { ...c, [field]: value } : c
    ));
    setSaveSuccess(false);
  };


  const handleSave = async () => {
    if (!activeConfig) return;
    setSaving(true);
    try {
      const res = await fetch(`${API_BASE_URL}/agents/config/${selectedAgentId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(activeConfig)
      });
      if (res.ok) {
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 3000);
      }
    } catch (err) {
      console.error("Failed to save config:", err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="p-12 text-center text-gray-500">Loading configurations...</div>;
  }

  return (
    <div className="max-w-[1400px] mx-auto bg-white rounded-2xl shadow-[0_2px_8px_rgba(0,0,0,0.04)] border border-gray-100 flex overflow-hidden min-h-[750px]">
      {/* Sidebar */}
      <div className="w-[300px] bg-gray-50 border-r border-gray-100 flex flex-col">
        <div className="p-6 border-b border-gray-100">
          <h2 className="text-[18px] font-bold text-gray-900">Agent Systems</h2>
          <p className="text-[13px] text-gray-500 mt-1">Configure live agent behavior</p>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {['intent', 'sales', 'product'].map((id) => {
            const meta = AGENT_META[id as keyof typeof AGENT_META];
            const isActive = selectedAgentId === id;
            return (
              <button
                key={id}
                onClick={() => setSelectedAgentId(id)}
                className={`w-full text-left p-4 rounded-xl transition-all duration-200 ${
                  isActive 
                    ? 'bg-white shadow-sm border border-[#3366ff]/20 ring-1 ring-[#3366ff]' 
                    : 'hover:bg-gray-100/80 border border-transparent'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center space-x-2">
                    <span className={`font-bold text-[14px] ${isActive ? 'text-[#3366ff]' : 'text-gray-900'}`}>
                      {meta.name}
                    </span>
                  </div>
                  {/* Status dot */}
                  <div className={`w-2 h-2 rounded-full ${configs.find(c => c.agent_id === id)?.is_active ? 'bg-[#00d26a]' : 'bg-gray-400'}`} />
                </div>
                <p className="text-[12px] text-gray-500 line-clamp-2">{meta.desc}</p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col bg-white">
        {activeConfig ? (
          <>
            <div className="p-6 border-b border-gray-100 flex items-center justify-between bg-white sticky top-0 z-10">
              <div>
                <h3 className="text-[20px] font-bold text-gray-900 flex items-center">
                  <span>{AGENT_META[selectedAgentId as keyof typeof AGENT_META].name}</span>
                </h3>
              </div>
              <div className="flex items-center space-x-4">
                <label className="flex items-center cursor-pointer">
                  <div className="relative">
                    <input 
                      type="checkbox" 
                      className="sr-only" 
                      checked={activeConfig.is_active}
                      onChange={(e) => handleUpdate('is_active', e.target.checked)}
                    />
                    <div className={`block w-10 h-6 rounded-full transition-colors ${activeConfig.is_active ? 'bg-[#00d26a]' : 'bg-gray-300'}`}></div>
                    <div className={`dot absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform ${activeConfig.is_active ? 'transform translate-x-4' : ''}`}></div>
                  </div>
                  <div className="ml-3 text-[14px] font-bold text-gray-700">
                    {activeConfig.is_active ? 'Active' : 'Paused'}
                  </div>
                </label>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className={`px-5 py-2 text-[14px] font-bold rounded-lg transition-colors flex items-center ${
                    saveSuccess 
                      ? 'bg-[#00d26a] text-white' 
                      : 'bg-[#3366ff] hover:bg-[#2b56d9] text-white shadow-sm'
                  }`}
                >
                  {saving ? 'Saving...' : saveSuccess ? 'Saved!' : 'Save Configuration'}
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-8 space-y-10">
              
              {/* Section: Model Parameters */}
              <section>
                <h4 className="text-[14px] font-bold text-gray-900 uppercase tracking-wider mb-5 pb-2 border-b border-gray-100 flex items-center">
                  <span className="w-1.5 h-4 bg-[#3366ff] rounded mr-2"></span>
                  Model
                </h4>
                <div className="w-1/2">
                  <label className="block text-[13px] font-bold text-gray-700 mb-2">Language Model</label>
                  <select 
                    value={activeConfig.model_name}
                    onChange={(e) => handleUpdate('model_name', e.target.value)}
                    className="w-full bg-gray-50 border border-gray-200 text-gray-900 text-sm rounded-lg focus:ring-[#3366ff] focus:border-[#3366ff] block p-2.5 outline-none mb-3"
                  >
                    {selectedAgentId === 'sales' ? (
                      <option value="gemini-1.5-flash">Gemini Live API — Cloud / Live</option>
                    ) : (
                      <>
                        <option value="gemma3:1b">Gemma 3 1B — Local</option>
                        <option value="gemma3:4b">Gemma 3 4B — Local</option>
                        <option value="llama3.1">Llama 3.1 — Local</option>
                        <option value="llama3.1:8b">Llama 3.1 8B — Local</option>
                        <option value="gemini-1.5-flash">Gemini Live API — Cloud / Live</option>
                      </>
                    )}
                  </select>
                  
                  <div className="flex items-center text-[13px] text-gray-600 font-medium mt-2">
                    <div className={`w-2 h-2 rounded-full mr-2 ${activeConfig.model_name.includes('gemini') ? 'bg-[#3366ff]' : 'bg-[#00d26a]'}`} />
                    {activeConfig.model_name.includes('gemini') ? 'Cloud / Live Model' : 'Local Model'}
                  </div>
                </div>
              </section>

              {/* Section: Behavior & Instructions */}
              <section>
                <h4 className="text-[14px] font-bold text-gray-900 uppercase tracking-wider mb-5 pb-2 border-b border-gray-100 flex items-center">
                  <span className="w-1.5 h-4 bg-[#00d26a] rounded mr-2"></span>
                  Behavior & Instructions
                </h4>
                <div className="mb-6">
                  <label className="block text-[13px] font-bold text-gray-700 mb-2">System Prompt / Persona</label>
                  <textarea 
                    rows={8}
                    value={activeConfig.system_prompt}
                    onChange={(e) => handleUpdate('system_prompt', e.target.value)}
                    className="w-full bg-gray-50 border border-gray-200 text-gray-900 text-[13px] rounded-lg focus:ring-[#3366ff] focus:border-[#3366ff] block p-4 outline-none font-mono resize-y leading-relaxed"
                    placeholder="Enter the base instructions and persona constraints for this agent..."
                  />
                </div>
              </section>

              {/* Section: Memory */}
              <section>
                <h4 className="text-[14px] font-bold text-gray-900 uppercase tracking-wider mb-5 pb-2 border-b border-gray-100 flex items-center">
                  <span className="w-1.5 h-4 bg-[#ffb020] rounded mr-2"></span>
                  Memory
                </h4>
                <div className="flex items-center justify-between w-1/2 p-4 bg-gray-50 rounded-xl border border-gray-100">
                  <div>
                    <div className="text-[14px] font-bold text-gray-900">Conversation Memory</div>
                    <div className="text-[12px] text-gray-500 mt-1">Allow the agent to remember context from recent turns.</div>
                  </div>
                  <label className="flex items-center cursor-pointer">
                    <div className="relative">
                      <input 
                        type="checkbox" 
                        className="sr-only" 
                        checked={activeConfig.context_memory_size > 0}
                        onChange={(e) => handleUpdate('context_memory_size', e.target.checked ? 10 : 0)}
                      />
                      <div className={`block w-12 h-7 rounded-full transition-colors ${activeConfig.context_memory_size > 0 ? 'bg-[#00d26a]' : 'bg-gray-300'}`}></div>
                      <div className={`dot absolute left-1 top-1 bg-white w-5 h-5 rounded-full transition-transform shadow-sm ${activeConfig.context_memory_size > 0 ? 'transform translate-x-5' : ''}`}></div>
                    </div>
                  </label>
                </div>
              </section>

            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-400">
            Select an agent from the sidebar to configure
          </div>
        )}
      </div>
    </div>
  );
};
