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
  commerce: { name: 'Commerce Agent', desc: 'Executes transactions, applies discounts, modifies cart.' },
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

  const handleCapabilityToggle = (capKey: string) => {
    if (!activeConfig) return;
    const currentCaps = activeConfig.capabilities || {};
    const newValue = !currentCaps[capKey];
    handleUpdate('capabilities', { ...currentCaps, [capKey]: newValue });
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
          {['intent', 'sales', 'product', 'commerce'].map((id) => {
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
              
              {/* Section: General Model Parameters */}
              <section>
                <h4 className="text-[14px] font-bold text-gray-900 uppercase tracking-wider mb-5 pb-2 border-b border-gray-100 flex items-center">
                  <span className="w-1.5 h-4 bg-[#3366ff] rounded mr-2"></span>
                  Model Parameters
                </h4>
                <div className="grid grid-cols-2 gap-8">
                  <div>
                    <label className="block text-[13px] font-bold text-gray-700 mb-2">Language Model</label>
                    <select 
                      value={activeConfig.model_name}
                      onChange={(e) => handleUpdate('model_name', e.target.value)}
                      className="w-full bg-gray-50 border border-gray-200 text-gray-900 text-sm rounded-lg focus:ring-[#3366ff] focus:border-[#3366ff] block p-2.5 outline-none"
                    >
                      <option value="gemini-1.5-flash">Gemini 1.5 Flash (Ultra-fast)</option>
                      <option value="gemini-1.5-pro">Gemini 1.5 Pro (High Reasoning)</option>
                      <option value="gemini-1.5-flash-8b">Gemini 1.5 Flash-8B (Low latency)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[13px] font-bold text-gray-700 mb-2">
                      Temperature ({activeConfig.temperature})
                    </label>
                    <input 
                      type="range" 
                      min="0" max="1" step="0.1" 
                      value={activeConfig.temperature}
                      onChange={(e) => handleUpdate('temperature', parseFloat(e.target.value))}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#3366ff]"
                    />
                    <div className="flex justify-between text-[11px] text-gray-500 mt-1">
                      <span>Precise</span>
                      <span>Creative</span>
                    </div>
                  </div>
                  <div>
                    <label className="block text-[13px] font-bold text-gray-700 mb-2">Max Output Tokens</label>
                    <input 
                      type="number" 
                      value={activeConfig.max_output_tokens}
                      onChange={(e) => handleUpdate('max_output_tokens', parseInt(e.target.value))}
                      className="w-full bg-gray-50 border border-gray-200 text-gray-900 text-sm rounded-lg focus:ring-[#3366ff] focus:border-[#3366ff] block p-2.5 outline-none"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[13px] font-bold text-gray-700 mb-2">Top P</label>
                      <input 
                        type="number" step="0.05" min="0" max="1"
                        value={activeConfig.top_p}
                        onChange={(e) => handleUpdate('top_p', parseFloat(e.target.value))}
                        className="w-full bg-gray-50 border border-gray-200 text-gray-900 text-sm rounded-lg focus:ring-[#3366ff] focus:border-[#3366ff] block p-2.5 outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-[13px] font-bold text-gray-700 mb-2">Top K</label>
                      <input 
                        type="number" min="1" max="100"
                        value={activeConfig.top_k}
                        onChange={(e) => handleUpdate('top_k', parseInt(e.target.value))}
                        className="w-full bg-gray-50 border border-gray-200 text-gray-900 text-sm rounded-lg focus:ring-[#3366ff] focus:border-[#3366ff] block p-2.5 outline-none"
                      />
                    </div>
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
                    rows={6}
                    value={activeConfig.system_prompt}
                    onChange={(e) => handleUpdate('system_prompt', e.target.value)}
                    className="w-full bg-gray-50 border border-gray-200 text-gray-900 text-[13px] rounded-lg focus:ring-[#3366ff] focus:border-[#3366ff] block p-3 outline-none font-mono resize-y"
                    placeholder="Enter the base instructions and persona constraints for this agent..."
                  />
                </div>
                <div className="w-1/2 pr-4">
                  <label className="block text-[13px] font-bold text-gray-700 mb-2">
                    Context Memory Size ({activeConfig.context_memory_size} turns)
                  </label>
                  <input 
                    type="range" 
                    min="0" max="20" step="1" 
                    value={activeConfig.context_memory_size}
                    onChange={(e) => handleUpdate('context_memory_size', parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#00d26a]"
                  />
                  <p className="text-[12px] text-gray-500 mt-2">Number of previous conversation turns to pass into context window.</p>
                </div>
              </section>

              {/* Section: Capabilities & Integration */}
              <section>
                <h4 className="text-[14px] font-bold text-gray-900 uppercase tracking-wider mb-5 pb-2 border-b border-gray-100 flex items-center">
                  <span className="w-1.5 h-4 bg-[#ffb020] rounded mr-2"></span>
                  Capabilities & Integration
                </h4>
                <div className="grid grid-cols-2 gap-10">
                  <div>
                    <label className="block text-[13px] font-bold text-gray-700 mb-4">Tool Access Controls</label>
                    <div className="space-y-3">
                      {[
                        { key: 'search_products', label: 'Search Products Catalog' },
                        { key: 'check_inventory', label: 'Check Real-time Inventory' },
                        { key: 'modify_cart', label: 'Modify Customer Cart' },
                        { key: 'calculate_discount', label: 'Calculate Dynamic Discounts' }
                      ].map(tool => (
                        <label key={tool.key} className="flex items-center cursor-pointer group">
                          <div className="relative flex-shrink-0">
                            <input 
                              type="checkbox" 
                              className="sr-only" 
                              checked={!!(activeConfig.capabilities || {})[tool.key]}
                              onChange={() => handleCapabilityToggle(tool.key)}
                            />
                            <div className={`block w-8 h-5 rounded-full transition-colors ${((activeConfig.capabilities || {})[tool.key]) ? 'bg-[#ffb020]' : 'bg-gray-200'}`}></div>
                            <div className={`dot absolute left-1 top-1 bg-white w-3 h-3 rounded-full transition-transform ${((activeConfig.capabilities || {})[tool.key]) ? 'transform translate-x-3' : ''}`}></div>
                          </div>
                          <div className="ml-3 text-[13px] text-gray-700 group-hover:text-gray-900 font-medium">
                            {tool.label}
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>
                  <div className="space-y-6">
                    <div>
                      <label className="block text-[13px] font-bold text-gray-700 mb-2">Fallback Behavior</label>
                      <select 
                        value={activeConfig.fallback_behavior}
                        onChange={(e) => handleUpdate('fallback_behavior', e.target.value)}
                        className="w-full bg-gray-50 border border-gray-200 text-gray-900 text-sm rounded-lg focus:ring-[#ffb020] focus:border-[#ffb020] block p-2.5 outline-none"
                      >
                        <option value="escalate_to_human">Escalate to Human Agent</option>
                        <option value="return_default">Return Default Safe Message</option>
                        <option value="retry_once">Retry Generation Once</option>
                      </select>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-[13px] font-bold text-gray-700 mb-2">Output Format</label>
                        <select 
                          value={activeConfig.output_formatting}
                          onChange={(e) => handleUpdate('output_formatting', e.target.value)}
                          className="w-full bg-gray-50 border border-gray-200 text-gray-900 text-sm rounded-lg focus:ring-[#ffb020] focus:border-[#ffb020] block p-2.5 outline-none"
                        >
                          <option value="markdown">Markdown</option>
                          <option value="json">JSON</option>
                          <option value="plain_text">Plain Text</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-[13px] font-bold text-gray-700 mb-2">Timeout (ms)</label>
                        <input 
                          type="number" step="100" min="500"
                          value={activeConfig.processing_timeout_ms}
                          onChange={(e) => handleUpdate('processing_timeout_ms', parseInt(e.target.value))}
                          className="w-full bg-gray-50 border border-gray-200 text-gray-900 text-sm rounded-lg focus:ring-[#ffb020] focus:border-[#ffb020] block p-2.5 outline-none"
                        />
                      </div>
                    </div>
                  </div>
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
