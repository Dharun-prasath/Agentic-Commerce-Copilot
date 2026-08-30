import React, { useEffect, useState } from 'react';

interface Customer360Props {
  sessionId: string | null;
  onClose: () => void;
}

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const Customer360: React.FC<Customer360Props> = ({ sessionId, onClose }) => {
  const [details, setDetails] = useState<any>(null);
  const [intentDetails, setIntentDetails] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!sessionId) return;
    
    let isMounted = true;
    const fetchDetails = async () => {
      setLoading(true);
      try {
        const headers = {
          'X-API-Key': import.meta.env.VITE_DASHBOARD_API_KEY || ''
        };
        const [res, intentRes] = await Promise.all([
          fetch(`${API_BASE_URL}/dashboard/sessions/${sessionId}`, { headers, cache: 'no-store' }),
          fetch(`${API_BASE_URL}/intent/${sessionId}`, { headers, cache: 'no-store' })
        ]);
        
        if (res.ok && isMounted) {
          setDetails(await res.json());
        }
        if (intentRes.ok && isMounted) {
          setIntentDetails(await intentRes.json());
        }
      } catch (e) {
        console.error("Failed to fetch session details", e);
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    
    fetchDetails();
    
    const interval = setInterval(fetchDetails, 3000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [sessionId]);

  return (
    <div 
      className={`fixed inset-y-0 right-0 w-full max-w-md bg-[#fafafa] border-l border-gray-200 shadow-2xl transform transition-transform duration-300 ease-in-out z-50 flex flex-col ${
        sessionId ? 'translate-x-0' : 'translate-x-full'
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-5 bg-white border-b border-gray-200 shrink-0">
        <div>
          <h2 className="text-[15px] font-semibold text-gray-900 tracking-tight">Customer 360 View</h2>
          {details?.session_id && (
            <div className="flex items-center gap-1.5 mt-1">
              <span className="text-[11px] text-gray-400 font-medium uppercase tracking-wider">Session</span>
              <span className="text-[12px] text-gray-600 font-mono tracking-tight bg-gray-100 px-1.5 py-0.5 rounded border border-gray-200">
                {details.session_id.substring(0, 12)}
              </span>
            </div>
          )}
        </div>
        <button 
          onClick={onClose}
          className="p-1.5 text-gray-400 hover:text-gray-900 transition-colors rounded-md hover:bg-gray-100"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-8">
        {loading && !details ? (
          <div className="flex justify-center py-10">
            <div className="h-5 w-5 border-2 border-gray-200 border-t-gray-900 rounded-full animate-spin"></div>
          </div>
        ) : !details ? (
          <div className="text-sm text-gray-500 py-10">No details available</div>
        ) : (
          <>
            {/* Intent Intelligence */}
            {intentDetails && (
              <section>
                <h3 className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-3">Intent Intelligence</h3>
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <div className="flex items-baseline gap-1.5">
                        <span className="text-2xl font-semibold text-[#3366ff] tracking-tight">
                          {intentDetails.current_score}%
                        </span>
                      </div>
                      <p className="text-[12px] text-gray-500 mt-0.5">
                        Threshold: {intentDetails.threshold}%
                      </p>
                    </div>
                    
                    <div className="text-right flex flex-col items-end gap-1.5">
                      <div className="flex gap-1.5">
                        {intentDetails.threshold_reached && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold tracking-wide border bg-green-50 text-[#00d26a] border-green-200">
                            HIGH INTENT
                          </span>
                        )}
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold tracking-wide border ${
                          intentDetails.status === 'TERMINATED'
                            ? 'bg-gray-50 text-gray-600 border-gray-200'
                            : 'bg-blue-50 text-[#3366ff] border-blue-200'
                        }`}>
                          {intentDetails.status === 'TERMINATED' ? 'TERMINATED' : 'ACTIVE'}
                        </span>
                      </div>
                      {intentDetails.status === 'TERMINATED' && (
                        <p className="text-[11px] text-gray-500 mt-1 font-medium">
                          Agent: {intentDetails.intent_agent_status || 'NOT TRIGGERED'}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="w-full bg-gray-100 rounded-full h-1.5 mb-2 overflow-hidden">
                    <div 
                      className={`h-1.5 rounded-full transition-all duration-500 ${
                        intentDetails.status === 'TERMINATED' 
                          ? (intentDetails.threshold_reached ? 'bg-[#00d26a]' : 'bg-gray-400')
                          : (intentDetails.threshold_reached ? 'bg-[#00d26a]' : 'bg-[#3366ff]')
                      }`} 
                      style={{ width: `${Math.min(100, (intentDetails.current_score / intentDetails.threshold) * 100)}%` }}
                    />
                  </div>
                  
                  {/* Detailed Agent Output */}
                  {intentDetails.intent_output && (
                    <div className="mt-4 border-t border-gray-100 pt-4 text-[12px] text-gray-700">
                      <div className="grid grid-cols-2 gap-y-3 gap-x-2">
                        <div>
                          <span className="block text-[10px] font-semibold text-gray-400 uppercase tracking-wide">Category</span>
                          <span className="font-medium text-gray-900">{intentDetails.intent_output.intent_category || 'N/A'}</span>
                        </div>
                        <div>
                          <span className="block text-[10px] font-semibold text-gray-400 uppercase tracking-wide">Confidence</span>
                          <span className="font-medium text-gray-900">{intentDetails.intent_output.confidence || '0'}</span>
                        </div>
                        <div className="col-span-2">
                          <span className="block text-[10px] font-semibold text-gray-400 uppercase tracking-wide">Buying Stage</span>
                          <span className="font-medium text-gray-900">{intentDetails.intent_output.buying_stage || 'N/A'}</span>
                        </div>
                        <div className="col-span-2">
                          <span className="block text-[10px] font-semibold text-gray-400 uppercase tracking-wide">Customer Interest</span>
                          <span className="text-gray-800 leading-snug">{intentDetails.intent_output.customer_interest || 'N/A'}</span>
                        </div>
                        <div className="col-span-2">
                          <span className="block text-[10px] font-semibold text-gray-400 uppercase tracking-wide">Behaviour Summary</span>
                          <span className="text-gray-800 leading-snug">{intentDetails.intent_output.behaviour_summary || 'N/A'}</span>
                        </div>
                        <div className="col-span-2 bg-gray-50 p-2 rounded border border-gray-100">
                          <span className="block text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-1">Reasoning</span>
                          <span className="text-gray-700 leading-snug italic">{intentDetails.intent_output.reasoning || 'N/A'}</span>
                        </div>
                        <div className="col-span-2">
                          <span className="block text-[10px] font-semibold text-gray-400 uppercase tracking-wide">Recommended Action</span>
                          <span className="font-bold text-gray-900">{intentDetails.intent_output.recommended_action || 'N/A'}</span>
                        </div>
                        <div className="col-span-2">
                          <span className="block text-[10px] font-semibold text-gray-400 uppercase tracking-wide">Sales Consultant Context</span>
                          <span className="text-gray-800 leading-snug">{intentDetails.intent_output.sales_consultant_context || 'N/A'}</span>
                        </div>
                      </div>
                      
                      <details className="mt-4 border-t border-gray-100 pt-3">
                        <summary className="text-[11px] font-semibold text-blue-600 cursor-pointer hover:text-blue-800 select-none outline-none">
                          [ View JSON ]
                        </summary>
                        <pre className="mt-2 text-[10px] bg-gray-900 text-gray-100 p-3 rounded overflow-auto max-h-64 shadow-inner">
                          {JSON.stringify(intentDetails.intent_output, null, 2)}
                        </pre>
                      </details>
                    </div>
                  )}

                </div>
              </section>
            )}

            {/* Behavioral Events */}
            <section>
              <h3 className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-3">Behavioral Events</h3>
              <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                {details.events && details.events.length > 0 ? (
                  <div className="divide-y divide-gray-100">
                    {details.events.map((evt: any, idx: number) => {
                      const dateObj = new Date(evt.time);
                      const timeString = isNaN(dateObj.getTime()) ? "" : dateObj.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'});
                      
                      return (
                        <div key={idx} className="p-3 hover:bg-gray-50 flex items-start gap-3 transition-colors">
                          <div className="mt-1.5 w-1.5 h-1.5 rounded-full bg-gray-300 shrink-0"></div>
                          <div className="flex-1 min-w-0">
                            <div className="flex justify-between items-baseline mb-0.5">
                              <span className="text-[13px] font-semibold text-gray-800 tracking-tight">{evt.type}</span>
                              <span className="text-[10px] font-mono font-medium text-gray-500 ml-2 shrink-0 bg-gray-50 px-1.5 py-0.5 rounded border border-gray-100">{timeString}</span>
                            </div>
                            {evt.product && (
                              <div className="text-[11px] text-gray-600 font-mono tracking-tight truncate bg-gray-50 border border-gray-200 px-1.5 py-0.5 rounded inline-block mt-1.5 shadow-sm">
                                ID: {evt.product.substring(0, 12)}...
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="text-[13px] text-gray-400 py-4 px-4 text-center">No events tracked.</div>
                )}
              </div>
            </section>

            {/* Conversation History */}
            <section>
              <h3 className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-3">Conversation</h3>
              <div className="bg-white border border-gray-200 rounded-lg p-1">
                {details.messages && details.messages.length > 0 ? (
                  <div className="divide-y divide-gray-100">
                    {details.messages.map((msg: any, idx: number) => (
                      <div key={idx} className="p-3">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`w-1.5 h-1.5 rounded-full ${msg.sender === 'USER' ? 'bg-gray-900' : 'bg-gray-400'}`}></span>
                          <span className="text-[11px] font-medium text-gray-500 uppercase tracking-wider">
                            {msg.sender === 'USER' ? 'Customer' : 'Agent'}
                          </span>
                        </div>
                        <div className="text-[13px] text-gray-800 leading-relaxed pl-3.5">
                          {msg.content}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-[13px] text-gray-400 py-3 px-3 text-center">No messages.</div>
                )}
              </div>
            </section>
            
            {/* Cart Data */}
            {details.cart && details.cart.items && details.cart.items.length > 0 && (
              <section>
                <h3 className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-3">Cart Contents</h3>
                <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                  <table className="w-full text-left border-collapse">
                    <tbody className="divide-y divide-gray-100">
                      {details.cart.items.map((item: any, idx: number) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="p-3">
                            <div className="flex items-center gap-3">
                              {item.product_thumbnail && (
                                <img src={item.product_thumbnail} className="w-8 h-8 rounded bg-gray-100 object-cover border border-gray-200" />
                              )}
                              <div>
                                <div className="text-[13px] font-medium text-gray-900">{item.product_name}</div>
                                <div className="text-[11px] text-gray-500">Qty: {item.quantity}</div>
                              </div>
                            </div>
                          </td>
                          <td className="p-3 text-right text-[13px] font-medium text-gray-900">
                            ₹{item.total_price || (item.unit_price * item.quantity)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-gray-50 border-t border-gray-200">
                      <tr>
                        <td className="p-3 text-[12px] font-medium text-gray-500">Subtotal</td>
                        <td className="p-3 text-right text-[13px] font-semibold text-gray-900">₹{details.cart.subtotal}</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </section>
            )}
            
          </>
        )}
      </div>
    </div>
  );
};

