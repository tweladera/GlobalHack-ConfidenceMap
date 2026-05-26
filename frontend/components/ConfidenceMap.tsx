"use client";

import { useCallback, useEffect, useMemo } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Node,
  Edge,
  BackgroundVariant,
  Handle,
  Position,
  NodeProps,
} from "reactflow";
import dagre from "@dagrejs/dagre";
import "reactflow/dist/style.css";
import type { AgentState, Finding, ConfidenceLevel } from "@/types";

// ── Node types ────────────────────────────────────────────────────────────────

function HubNode({ data }: NodeProps) {
  return (
    <div
      className="relative flex items-center justify-center w-24 h-24 rounded-full border-2 border-accent bg-accent-dim"
      role="img"
      aria-label={`Analysis hub: ${data.label}`}
    >
      <Handle type="source" position={Position.Bottom} className="opacity-0" />
      <div className="text-center">
        <div className="text-2xl" aria-hidden="true">
          ◎
        </div>
        <div className="text-[10px] font-mono text-accent mt-1">{data.label}</div>
      </div>
    </div>
  );
}

const STATUS_COLORS = {
  pending: "border-surface-border text-slate-500",
  running: "border-accent text-accent animate-pulse_slow",
  completed: "border-slate-600 text-slate-300",
  error: "border-confidence-red text-confidence-red",
};

const STATUS_BADGE = {
  pending: "bg-surface-border text-slate-500",
  running: "bg-accent-dim text-accent",
  completed: "bg-surface-border text-slate-400",
  error: "bg-confidence-red-dim text-confidence-red",
};

function AgentNode({ data }: NodeProps) {
  const colorClass = STATUS_COLORS[data.status as keyof typeof STATUS_COLORS] ?? STATUS_COLORS.pending;
  const badgeClass = STATUS_BADGE[data.status as keyof typeof STATUS_BADGE] ?? STATUS_BADGE.pending;
  const isRunning = data.status === "running";

  return (
    <div
      className={`relative w-44 bg-surface-card border-2 rounded-xl p-3 transition-all ${colorClass} ${isRunning ? "agent-glow" : ""}`}
      role="region"
      aria-label={`Agent: ${data.label}, status: ${data.status}, ${data.findingCount} findings`}
    >
      <Handle type="target" position={Position.Top} className="opacity-0" />
      <Handle type="source" position={Position.Bottom} className="opacity-0" />

      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-semibold truncate">{data.label}</span>
        <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-mono uppercase ${badgeClass}`}>
          {data.status === "running" ? "..." : data.status}
        </span>
      </div>

      {data.findingCount > 0 && (
        <div className="flex gap-1 mt-2" aria-label={`Findings: ${data.greenCount} confirmed, ${data.yellowCount} inferred, ${data.redCount} high uncertainty`}>
          {data.greenCount > 0 && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-confidence-green-dim text-confidence-green font-mono">
              {data.greenCount} ✓
            </span>
          )}
          {data.yellowCount > 0 && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-confidence-yellow-dim text-confidence-yellow font-mono">
              {data.yellowCount} ~
            </span>
          )}
          {data.redCount > 0 && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-confidence-red-dim text-confidence-red font-mono">
              {data.redCount} !
            </span>
          )}
        </div>
      )}
    </div>
  );
}

const CONFIDENCE_BORDER: Record<ConfidenceLevel, string> = {
  green: "border-confidence-green",
  yellow: "border-confidence-yellow",
  red: "border-confidence-red",
};

const CONFIDENCE_TEXT: Record<ConfidenceLevel, string> = {
  green: "text-confidence-green",
  yellow: "text-confidence-yellow",
  red: "text-confidence-red",
};

const CONFIDENCE_DOT: Record<ConfidenceLevel, string> = {
  green: "bg-confidence-green",
  yellow: "bg-confidence-yellow",
  red: "bg-confidence-red",
};

function FindingNode({ data }: NodeProps) {
  const borderClass = CONFIDENCE_BORDER[data.confidence as ConfidenceLevel] ?? "border-surface-border";
  const textClass = CONFIDENCE_TEXT[data.confidence as ConfidenceLevel] ?? "text-slate-400";
  const dotClass = CONFIDENCE_DOT[data.confidence as ConfidenceLevel] ?? "bg-slate-400";
  const score = Math.round((data.confidence_score as number) * 100);

  return (
    <button
      onClick={data.onClick}
      className={`w-52 bg-surface-card border rounded-xl p-3 text-left cursor-pointer hover:brightness-125 transition-all animate-fade-in ${borderClass}`}
      aria-label={`Finding: ${data.label}. Confidence: ${data.confidence}, ${score}%. Click to view details.`}
    >
      <Handle type="target" position={Position.Top} className="opacity-0" />

      <div className="flex items-start gap-2">
        <span
          className={`mt-1 w-2 h-2 rounded-full flex-shrink-0 ${dotClass}`}
          aria-hidden="true"
        />
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-slate-200 leading-snug">{data.label}</p>
          <p className={`text-[10px] mt-1 font-mono uppercase ${textClass}`}>
            {data.confidence}
          </p>
          <div className="mt-2 flex items-center gap-1.5">
            <div
              className="flex-1 h-1 bg-surface-border rounded-full overflow-hidden"
              aria-hidden="true"
            >
              <div
                className={`h-full rounded-full bg-confidence-${data.confidence as string} transition-all duration-700`}
                style={{ width: `${score}%` }}
              />
            </div>
            <span className={`text-[9px] font-mono tabular-nums ${textClass}`}>{score}%</span>
          </div>
        </div>
      </div>
    </button>
  );
}

const nodeTypes = {
  hub: HubNode,
  agent: AgentNode,
  finding: FindingNode,
};

// ── Dagre layout ──────────────────────────────────────────────────────────────

const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

function getLayoutedElements(nodes: Node[], edges: Edge[]) {
  dagreGraph.setGraph({ rankdir: "TB", ranksep: 80, nodesep: 40 });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, {
      width: node.id === "hub" ? 96 : node.type === "agent" ? 176 : 208,
      height: node.id === "hub" ? 96 : node.type === "agent" ? 80 : 72,
    });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const pos = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: pos.x - (node.id === "hub" ? 48 : node.type === "agent" ? 88 : 104),
        y: pos.y - (node.id === "hub" ? 48 : node.type === "agent" ? 40 : 36),
      },
    };
  });

  return { nodes: layoutedNodes, edges };
}

// ── Main component ────────────────────────────────────────────────────────────

interface ConfidenceMapProps {
  agents: AgentState[];
  onFindingSelect: (finding: Finding) => void;
}

export default function ConfidenceMap({ agents, onFindingSelect }: ConfidenceMapProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const buildGraph = useCallback(() => {
    const rawNodes: Node[] = [];
    const rawEdges: Edge[] = [];

    // Hub
    rawNodes.push({
      id: "hub",
      type: "hub",
      position: { x: 0, y: 0 },
      data: { label: "ANALYSIS" },
    });

    // Agent nodes
    agents.forEach((agent) => {
      const greenCount = agent.findings.filter((f) => f.confidence === "green").length;
      const yellowCount = agent.findings.filter((f) => f.confidence === "yellow").length;
      const redCount = agent.findings.filter((f) => f.confidence === "red").length;

      rawNodes.push({
        id: agent.agent_id,
        type: "agent",
        position: { x: 0, y: 0 },
        data: {
          label: agent.agent_name,
          status: agent.status,
          findingCount: agent.findings.length,
          greenCount,
          yellowCount,
          redCount,
        },
      });

      rawEdges.push({
        id: `hub-${agent.agent_id}`,
        source: "hub",
        target: agent.agent_id,
        animated: agent.status === "running",
        style: { stroke: agent.status === "running" ? "#6366f1" : "#2d2d4e" },
      });

      // Finding nodes
      agent.findings.forEach((finding) => {
        rawNodes.push({
          id: finding.id,
          type: "finding",
          position: { x: 0, y: 0 },
          data: {
            label: finding.title,
            confidence: finding.confidence,
            confidence_score: finding.confidence_score,
            onClick: () => onFindingSelect(finding),
          },
        });

        rawEdges.push({
          id: `${agent.agent_id}-${finding.id}`,
          source: agent.agent_id,
          target: finding.id,
          style: { stroke: "#2d2d4e" },
        });
      });
    });

    const { nodes: ln, edges: le } = getLayoutedElements(rawNodes, rawEdges);
    setNodes(ln);
    setEdges(le);
  }, [agents, onFindingSelect, setNodes, setEdges]);

  useEffect(() => {
    buildGraph();
  }, [buildGraph]);

  return (
    <div className="w-full h-full" role="img" aria-label="Confidence map visualization showing agents and their findings">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.3}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
      >
        <Background variant={BackgroundVariant.Dots} gap={24} size={1} color="#1e1e2e" />
        <Controls aria-label="Map controls: zoom in, zoom out, fit view" />
        <MiniMap
          nodeColor={(n) => {
            if (n.type === "hub") return "#6366f1";
            if (n.type === "finding") {
              const c = (n.data as { confidence?: string }).confidence;
              if (c === "green") return "#22c55e";
              if (c === "yellow") return "#eab308";
              if (c === "red") return "#ef4444";
            }
            return "#1e1e2e";
          }}
          maskColor="#0d0d1a80"
        />
      </ReactFlow>
    </div>
  );
}
