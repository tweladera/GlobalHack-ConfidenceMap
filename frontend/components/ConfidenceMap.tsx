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
  const score = data.globalScore as number | null | undefined;
  const hasScore = score != null;
  const scoreCol = !hasScore ? "text-accent"
    : score >= 0.7 ? "text-confidence-green"
    : score >= 0.45 ? "text-confidence-yellow"
    : "text-confidence-red";

  return (
    <div
      className="relative flex items-center justify-center w-28 h-28 rounded-full border-2 border-accent bg-accent-dim shadow-lg shadow-accent/20"
      role="img"
      aria-label={hasScore ? `Analysis hub: global confidence ${Math.round(score! * 100)}%` : `Analysis hub: ${data.label}`}
    >
      <Handle type="source" position={Position.Bottom} className="opacity-0" />
      <div className="text-center px-2">
        {hasScore ? (
          <>
            <div className={`text-xl font-bold font-mono tabular-nums leading-none ${scoreCol}`}>
              {Math.round(score! * 100)}%
            </div>
            <div className="text-[8px] font-mono text-slate-500 uppercase tracking-widest mt-1">confidence</div>
          </>
        ) : (
          <>
            <div className="text-3xl animate-pulse" aria-hidden="true">◎</div>
            <div className="text-[9px] font-mono text-accent mt-1 uppercase tracking-wide">{data.label}</div>
          </>
        )}
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
  const total = (data.greenCount as number) + (data.yellowCount as number) + (data.redCount as number);
  const greenPct = total > 0 ? ((data.greenCount as number) / total) * 100 : 0;
  const yellowPct = total > 0 ? ((data.yellowCount as number) / total) * 100 : 0;
  const redPct = total > 0 ? ((data.redCount as number) / total) * 100 : 0;

  return (
    <div
      className={`relative w-44 bg-surface-card border-2 rounded-xl p-3 transition-all ${colorClass} ${isRunning ? "agent-glow" : ""}`}
      role="region"
      aria-label={`Agent: ${data.label}, status: ${data.status}, ${data.findingCount} findings`}
    >
      <Handle type="target" position={Position.Top} className="opacity-0" />
      <Handle type="source" position={Position.Bottom} className="opacity-0" />

      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold truncate leading-tight">{data.label}</span>
        <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-mono uppercase flex-shrink-0 ml-1 ${badgeClass}`}>
          {data.status === "running" ? "···" : data.status}
        </span>
      </div>

      {data.findingCount > 0 && (
        <div
          className="space-y-1.5"
          aria-label={`${data.greenCount} confirmed, ${data.yellowCount} inferred, ${data.redCount} high uncertainty`}
        >
          {/* Stacked severity bar */}
          <div className="flex h-2 rounded-full overflow-hidden gap-px bg-surface-border">
            {data.greenCount > 0 && (
              <div className="bg-confidence-green transition-all duration-700" style={{ width: `${greenPct}%` }} />
            )}
            {data.yellowCount > 0 && (
              <div className="bg-confidence-yellow transition-all duration-700" style={{ width: `${yellowPct}%` }} />
            )}
            {data.redCount > 0 && (
              <div className="bg-confidence-red transition-all duration-700" style={{ width: `${redPct}%` }} />
            )}
          </div>
          {/* Count badges */}
          <div className="flex gap-1">
            {data.greenCount > 0 && (
              <span className="text-[9px] px-1.5 py-0.5 rounded bg-confidence-green-dim text-confidence-green font-mono">
                {data.greenCount}✓
              </span>
            )}
            {data.yellowCount > 0 && (
              <span className="text-[9px] px-1.5 py-0.5 rounded bg-confidence-yellow-dim text-confidence-yellow font-mono">
                {data.yellowCount}~
              </span>
            )}
            {data.redCount > 0 && (
              <span className="text-[9px] px-1.5 py-0.5 rounded bg-confidence-red-dim text-confidence-red font-mono">
                {data.redCount}!
              </span>
            )}
          </div>
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
  const confidence = data.confidence as ConfidenceLevel;
  const borderClass = CONFIDENCE_BORDER[confidence] ?? "border-surface-border";
  const textClass = CONFIDENCE_TEXT[confidence] ?? "text-slate-400";
  const score = Math.round((data.confidence_score as number) * 100);
  const isRed = confidence === "red";
  const accentW = isRed ? "w-1.5" : "w-1";
  const accentBg = `bg-confidence-${confidence}`;
  const borderWeight = isRed ? "border-2" : "border";

  return (
    <button
      onClick={data.onClick}
      className={`relative w-52 bg-surface-card ${borderWeight} rounded-xl pl-4 pr-3 py-3 text-left cursor-pointer hover:brightness-125 transition-all animate-fade-in overflow-hidden ${borderClass}`}
      aria-label={`Finding: ${data.label}. Confidence: ${confidence}, ${score}%. Click to view details.`}
    >
      <Handle type="target" position={Position.Top} className="opacity-0" />

      {/* Left severity accent strip */}
      <div
        className={`absolute left-0 top-0 bottom-0 ${accentW} ${accentBg}`}
        aria-hidden="true"
      />

      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-slate-200 leading-snug line-clamp-2">{data.label}</p>
        <div className="mt-2 flex items-center gap-1.5">
          <div
            className="flex-1 h-1.5 bg-surface-border rounded-full overflow-hidden"
            aria-hidden="true"
          >
            <div
              className={`h-full rounded-full bg-confidence-${confidence} transition-all duration-700`}
              style={{ width: `${score}%` }}
            />
          </div>
          <span className={`text-xs font-bold font-mono tabular-nums ${textClass}`}>{score}%</span>
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
      width: node.id === "hub" ? 112 : node.type === "agent" ? 176 : 208,
      height: node.id === "hub" ? 112 : node.type === "agent" ? 90 : 72,
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
        x: pos.x - (node.id === "hub" ? 56 : node.type === "agent" ? 88 : 104),
        y: pos.y - (node.id === "hub" ? 56 : node.type === "agent" ? 45 : 36),
      },
    };
  });

  return { nodes: layoutedNodes, edges };
}

// ── Main component ────────────────────────────────────────────────────────────

interface ConfidenceMapProps {
  agents: AgentState[];
  onFindingSelect: (finding: Finding) => void;
  globalScore?: number | null;
}

export default function ConfidenceMap({ agents, onFindingSelect, globalScore }: ConfidenceMapProps) {
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
      data: { label: "ANALYSIS", globalScore: globalScore ?? null },
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
  }, [agents, globalScore, onFindingSelect, setNodes, setEdges]);

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
