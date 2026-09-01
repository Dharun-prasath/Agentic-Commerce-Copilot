import { useState, useEffect } from 'react';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export function CallsView() {
  const [calls, setCalls] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCalls = async () => {
      try {
        const headers = {
          'X-API-Key': import.meta.env.VITE_DASHBOARD_API_KEY || ''
        };
        const res = await fetch(`${API_BASE_URL}/dashboard/calls`, { headers, cache: 'no-store' });
        if (res.ok) {
          setCalls(await res.json());
        }
      } catch (e) {
        console.error("Failed to fetch calls", e);
      } finally {
        setLoading(false);
      }
    };
    
    fetchCalls();
    const interval = setInterval(fetchCalls, 5000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    if (status.includes("TRIGGERED")) return "text-blue-600 bg-blue-50 border-blue-200";
    if (status.includes("READY") || status.includes("REQUESTED")) return "text-green-600 bg-green-50 border-green-200";
    if (status.includes("COMPLETED")) return "text-emerald-700 bg-emerald-50 border-emerald-200";
    if (status.includes("FAILED") || status.includes("ERROR")) return "text-red-600 bg-red-50 border-red-200";
    if (status.includes("INTERESTED")) return "text-gray-600 bg-gray-50 border-gray-200";
    return "text-purple-600 bg-purple-50 border-purple-200";
  };

  return (
    <>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-[22px] font-bold text-gray-900">
          Sales Consultant Calls History
        </h2>
      </div>
      <div className="bg-white rounded-2xl shadow-[0_2px_8px_rgba(0,0,0,0.04)] border border-gray-100 overflow-hidden min-h-[600px]">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-100 text-[12px] font-bold text-gray-500 uppercase tracking-wider">
              <th className="px-6 py-4">Job ID</th>
              <th className="px-6 py-4">Customer</th>
              <th className="px-6 py-4">Session ID</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4">Time</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 text-sm">
            {loading ? (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-gray-500">Loading calls...</td>
              </tr>
            ) : calls.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-12 text-center text-gray-500 text-lg">No calls found in the system.</td>
              </tr>
            ) : (
              calls.map((call) => (
                <tr key={call.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 font-mono text-gray-500">{call.id.substring(0, 8)}</td>
                  <td className="px-6 py-4 font-bold text-gray-900">{call.user}</td>
                  <td className="px-6 py-4 font-mono text-gray-500">{call.session_id.substring(0, 8)}</td>
                  <td className="px-6 py-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getStatusColor(call.status)}`}>
                      {call.status}
                    </span>
                    {call.error && (
                      <div className="mt-1 text-xs text-red-500 max-w-xs truncate">{call.error}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 text-gray-500">{call.time}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
