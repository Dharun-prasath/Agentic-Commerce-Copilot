import type { Node, Edge } from '@xyflow/react';

interface DetailDrawerProps {
  selectedNode: Node | null;
  selectedEdge: Edge | null;
  onClose: () => void;
}

export function DetailDrawer({ selectedNode, selectedEdge, onClose }: DetailDrawerProps) {
  if (!selectedNode && !selectedEdge) return null;

  return (
    <div className="absolute top-4 left-4 bottom-4 w-80 bg-white shadow-xl border border-gray-200 rounded-xl overflow-hidden flex flex-col z-10 animate-in slide-in-from-left-8 duration-200">
      <div className="px-4 py-3 border-b border-gray-100 flex justify-between items-center bg-gray-50">
        <h3 className="font-bold text-gray-700 text-sm tracking-widest uppercase">
          {selectedNode ? 'Component Details' : 'Event Details'}
        </h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 font-bold p-1">
          ✕
        </button>
      </div>
      
      <div className="p-5 overflow-y-auto flex-1 space-y-4 text-sm">
        {selectedNode && (
          <>
            <div>
              <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Component</div>
              <div className="font-bold text-gray-900 text-base">{selectedNode.data.label as string}</div>
            </div>
            
            <div>
              <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Status</div>
              <span className={`inline-block px-2.5 py-1 rounded-[4px] text-[10px] font-bold tracking-widest uppercase border ${
                selectedNode.data.status === 'RUNNING' ? 'text-blue-700 bg-blue-50 border-blue-200' :
                selectedNode.data.status === 'COMPLETED' ? 'text-emerald-700 bg-emerald-50 border-emerald-200' :
                selectedNode.data.status === 'FAILED' ? 'text-red-700 bg-red-50 border-red-200' :
                selectedNode.data.status === 'WAITING' ? 'text-amber-700 bg-amber-50 border-amber-200' :
                'text-gray-500 bg-gray-50 border-gray-200'
              }`}>
                {selectedNode.data.status === 'RUNNING' && '● '}
                {selectedNode.data.status === 'COMPLETED' && '✓ '}
                {selectedNode.data.status === 'FAILED' && '✕ '}
                {selectedNode.data.status === 'IDLE' && '○ '}
                {selectedNode.data.status as string}
              </span>
            </div>
            
            {Object.entries((selectedNode.data.details as Record<string, any>) || {})
              .filter(([key]) => key !== 'error')
              .map(([key, value]) => (
              <div key={key}>
                <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">{key.replace(/_/g, ' ')}</div>
                <div className="font-mono text-[11px] text-gray-700 break-words bg-gray-50 p-2.5 rounded border border-gray-200 overflow-x-auto max-h-[300px] overflow-y-auto shadow-sm">
                  {typeof value === 'object' && value !== null ? (
                    <pre className="whitespace-pre-wrap leading-relaxed">{JSON.stringify(value, null, 2)}</pre>
                  ) : (
                    String(value)
                  )}
                </div>
              </div>
            ))}
            
            {(selectedNode.data.details as any)?.error && (
              <div className="mt-4 p-3 bg-red-50 border border-red-100 rounded-lg">
                <div className="text-[10px] font-bold text-red-400 uppercase tracking-widest mb-1">Error</div>
                <div className="font-mono text-xs text-red-700 break-all">
                  {(selectedNode.data.details as any).error}
                </div>
              </div>
            )}
          </>
        )}
        
        {selectedEdge && (
          <>
            <div>
              <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Connection</div>
              <div className="font-bold text-gray-900 text-sm">
                {selectedEdge.source.split('_').slice(1).join(' ').toUpperCase()} → {selectedEdge.target.split('_').slice(1).join(' ').toUpperCase()}
              </div>
            </div>
            <div>
              <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Status</div>
              <div className="text-gray-700 font-medium">
                {selectedEdge.animated ? 'Transitioning Data...' : 'Completed Transition'}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
