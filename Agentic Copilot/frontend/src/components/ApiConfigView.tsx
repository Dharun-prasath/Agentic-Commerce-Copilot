import React, { useState, useEffect } from 'react';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const ApiConfigView: React.FC = () => {
  const [geminiKey, setGeminiKey] = useState('');
  const [telegramToken, setTelegramToken] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    const fetchKeys = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/system/keys`);
        if (res.ok) {
          const data = await res.json();
          setGeminiKey(data.gemini_api_key || '');
          setTelegramToken(data.telegram_bot_token || '');
        }
      } catch (err) {
        console.error("Failed to fetch API keys:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchKeys();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await fetch(`${API_BASE_URL}/system/keys`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          gemini_api_key: geminiKey,
          telegram_bot_token: telegramToken
        })
      });
      if (res.ok) {
        const data = await res.json();
        setGeminiKey(data.gemini_api_key || '');
        setTelegramToken(data.telegram_bot_token || '');
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 3000);
      }
    } catch (err) {
      console.error("Failed to save API keys:", err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="p-12 text-center text-gray-500">Loading API configurations...</div>;
  }

  return (
    <div className="max-w-[800px] mx-auto bg-white rounded-2xl shadow-[0_2px_8px_rgba(0,0,0,0.04)] border border-gray-100 flex flex-col overflow-hidden">
      <div className="p-6 border-b border-gray-100 flex items-center justify-between bg-white">
        <div>
          <h3 className="text-[20px] font-bold text-gray-900">API Configurations</h3>
          <p className="text-[13px] text-gray-500 mt-1">Manage external API keys and tokens for the system</p>
        </div>
        <div>
          <button
            onClick={handleSave}
            disabled={saving}
            className={`px-6 py-2 text-[14px] font-bold rounded-lg transition-colors flex items-center ${
              saveSuccess 
                ? 'bg-[#00d26a] text-white' 
                : 'bg-[#3366ff] hover:bg-[#2b56d9] text-white shadow-sm'
            }`}
          >
            {saving ? 'Saving...' : saveSuccess ? 'Saved!' : 'Save Keys'}
          </button>
        </div>
      </div>

      <div className="p-8 space-y-8">
        <section>
          <h4 className="text-[14px] font-bold text-gray-900 uppercase tracking-wider mb-5 pb-2 border-b border-gray-100 flex items-center">
            <span className="w-1.5 h-4 bg-[#3366ff] rounded mr-2"></span>
            Language Models (LLM)
          </h4>
          <div className="mb-4">
            <label className="block text-[13px] font-bold text-gray-700 mb-2">Gemini API Key</label>
            <input 
              type="text" 
              value={geminiKey}
              onChange={(e) => setGeminiKey(e.target.value)}
              className="w-full bg-gray-50 border border-gray-200 text-gray-900 text-sm rounded-lg focus:ring-[#3366ff] focus:border-[#3366ff] block p-3 outline-none font-mono"
              placeholder="AIzaSy..."
            />
            <p className="text-[12px] text-gray-500 mt-2">Required for the core reasoning agents and intent classification.</p>
          </div>
        </section>

        <section>
          <h4 className="text-[14px] font-bold text-gray-900 uppercase tracking-wider mb-5 pb-2 border-b border-gray-100 flex items-center">
            <span className="w-1.5 h-4 bg-[#00d26a] rounded mr-2"></span>
            Integrations
          </h4>
          <div className="mb-4">
            <label className="block text-[13px] font-bold text-gray-700 mb-2">Telegram Bot Token</label>
            <input 
              type="text" 
              value={telegramToken}
              onChange={(e) => setTelegramToken(e.target.value)}
              className="w-full bg-gray-50 border border-gray-200 text-gray-900 text-sm rounded-lg focus:ring-[#00d26a] focus:border-[#00d26a] block p-3 outline-none font-mono"
              placeholder="123456789:ABCDefGHIjklmNOPqRSTuVwxYZ..."
            />
            <p className="text-[12px] text-gray-500 mt-2">Required to operate the Telegram commerce bot.</p>
          </div>
        </section>
      </div>
    </div>
  );
};
