import { useState, useEffect, useCallback } from 'react';
import { 
  ReactFlow, 
  Controls, 
  Background, 
  useNodesState, 
  useEdgesState, 
  MarkerType,
  ConnectionMode
} from '@xyflow/react';
import type { Node, Edge, OnSelectionChangeParams } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { CustomNode } from './CustomNode';
import { DetailDrawer } from './DetailDrawer';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const nodeTypes = {
  component: CustomNode,
  orchestrator: CustomNode,
  agent: CustomNode,
  engine: CustomNode
};

const FIXED_POSITIONS: Record<string, { x: number, y: number }> = {
  n_session: { x: 50, y: 450 },
  n_rule_intent: { x: 350, y: 450 },
  n_orchestrator: { x: 650, y: 450 },
  n_intent_agent: { x: 1050, y: 150 },
  n_sales_consultant: { x: 1050, y: 300 },
  n_product_intelligence: { x: 1050, y: 450 },
  n_commerce: { x: 1050, y: 600 },
  n_telegram: { x: 1050, y: 750 }
};

export function ExecutionGraph({ sessionId }: { sessionId: string }) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<Edge | null>(null);

  useEffect(() => {
    if (!sessionId) {
      setNodes([]);
      setEdges([]);
      return;
    }

    const processData = (data: any) => {
      // Map nodes
      const rfNodes: Node[] = data.nodes.map((n: any) => ({
        id: n.id,
        type: n.type,
        position: FIXED_POSITIONS[n.id] || { x: 0, y: 0 },
        data: n,
        draggable: false // Strict architecture rule
      }));

      // Map edges
      // Map edges with exact handle targets to ensure clean 4-way layout
      const getHandleIds = (source: string, target: string) => {
        // All forward edges flow from Right to Left
        if (source === 'n_session' && target === 'n_rule_intent') return { sh: 's-right', th: 't-left' };
        if (source === 'n_rule_intent' && target === 'n_orchestrator') return { sh: 's-right', th: 't-left' };
        
        // Orchestrator -> Agents
        if (source === 'n_orchestrator' && target === 'n_intent_agent') return { sh: 's-right', th: 't-left' };
        if (source === 'n_orchestrator' && target === 'n_sales_consultant') return { sh: 's-right', th: 't-left' };
        if (source === 'n_orchestrator' && target === 'n_product_intelligence') return { sh: 's-right', th: 't-left' };
        if (source === 'n_orchestrator' && target === 'n_commerce') return { sh: 's-right', th: 't-left' };
        if (source === 'n_orchestrator' && target === 'n_telegram') return { sh: 's-right', th: 't-left' };
        
        // Agents -> Orchestrator (Return edges)
        // Curve back from Left to Right
        if (source === 'n_intent_agent' && target === 'n_orchestrator') return { sh: 's-left', th: 't-right' };
        if (source === 'n_sales_consultant' && target === 'n_orchestrator') return { sh: 's-left', th: 't-right' };
        if (source === 'n_product_intelligence' && target === 'n_orchestrator') return { sh: 's-left', th: 't-right' };
        
        return { sh: 's-right', th: 't-left' };
      };

      const rfEdges: Edge[] = data.edges.map((e: any) => {
        // Force Telegram to connect from Orchestrator for all sessions (backwards compatibility)
        if (e.target === 'n_telegram') {
          e.source = 'n_orchestrator';
        }

        let isActive = data.active_edges.includes(e.id);
        let isReturn = e.id.includes('to_orch') && e.id !== 'e_rule_to_orch'; // E.g., agent to orchestrator
        
        // Special logic for Commerce Engine using same edge for forward and backward
        let isReversedAnimation = false;
        if (e.id === 'e_orch_to_com' && isActive) {
            const commerceNode = data.nodes.find((n: any) => n.id === 'n_commerce');
            if (commerceNode && commerceNode.status === 'IDLE') {
                isReturn = true;
                isReversedAnimation = true;
            }
        }

        const handles = getHandleIds(e.source, e.target);

        return {
          id: e.id,
          source: e.source,
          target: e.target,
          sourceHandle: handles.sh,
          targetHandle: handles.th,
          type: 'default',
          animated: isActive,
          style: {
            stroke: isActive ? (isReturn ? '#a855f7' : '#3b82f6') : '#cbd5e1',
            strokeWidth: isActive ? 2.5 : 1.5,
            strokeDasharray: isReturn ? '6,6' : 'none',
            transition: 'all 0.3s ease',
            animationDirection: isReversedAnimation ? 'reverse' : 'normal'
          },
          markerEnd: isReversedAnimation ? undefined : {
            type: MarkerType.ArrowClosed,
            color: isActive ? (isReturn ? '#a855f7' : '#3b82f6') : '#cbd5e1',
          },
          markerStart: isReversedAnimation ? {
            type: MarkerType.ArrowClosed,
            color: '#a855f7',
            orient: 'auto-start-reverse'
          } : undefined
        };
      });

      setNodes(rfNodes);
      setEdges(rfEdges);
      
      // Update selected states if they exist
      if (selectedNode) {
        const updatedNode = rfNodes.find(n => n.id === selectedNode.id);
        if (updatedNode) setSelectedNode(updatedNode);
      }
      if (selectedEdge) {
        const updatedEdge = rfEdges.find(e => e.id === selectedEdge.id);
        if (updatedEdge) setSelectedEdge(updatedEdge);
      }
    };

    const fetchGraph = async () => {
      try {
        const headers = { 'X-API-Key': import.meta.env.VITE_DASHBOARD_API_KEY || '' };
        const res = await fetch(`${API_BASE_URL}/dashboard/execution/${sessionId}`, { headers });
        if (res.ok) {
          processData(await res.json());
        }
      } catch (e) {
        console.error(e);
      }
    };

    fetchGraph();

    const eventSource = new EventSource(`${API_BASE_URL}/dashboard/execution/${sessionId}/stream`);
    eventSource.onmessage = (event) => {
      try {
        processData(JSON.parse(event.data));
      } catch (e) {}
    };

    return () => eventSource.close();
  }, [sessionId, setNodes, setEdges]); // Removed selectedNode/selectedEdge to avoid refetch loops

  const onSelectionChange = useCallback((params: OnSelectionChangeParams) => {
    setSelectedNode(params.nodes[0] || null);
    setSelectedEdge(params.edges[0] || null);
  }, []);

  if (!sessionId) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50 text-gray-400">
        <p>Select a session from the queue to view execution</p>
      </div>
    );
  }

  return (
    <div className="h-full w-full bg-[#f8fafc] flex">
      {/* React Flow Canvas Area */}
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onSelectionChange={onSelectionChange}
          connectionMode={ConnectionMode.Loose}
          fitView
          fitViewOptions={{ padding: 0.35 }}
          className="bg-slate-50/50"
          minZoom={0.5}
          maxZoom={1.5}
          nodesDraggable={false} // Architecture must remain fixed
          nodesConnectable={false}
          elementsSelectable={true}
          panOnDrag={false}
          zoomOnScroll={false}
          zoomOnPinch={false}
          zoomOnDoubleClick={false}
        >
          <Background color="#e2e8f0" gap={24} size={1} />
          <Controls className="!border-slate-200 !shadow-sm !rounded-md overflow-hidden" />
        </ReactFlow>

        <DetailDrawer 
          selectedNode={selectedNode}
          selectedEdge={selectedEdge}
          onClose={() => { setSelectedNode(null); setSelectedEdge(null); }}
        />
      </div>
    </div>
  );
}
