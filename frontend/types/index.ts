export type ConfidenceLevel = "green" | "yellow" | "red";

export type AgentStatus = "pending" | "running" | "completed" | "error";

export interface Finding {
  id: string;
  title: string;
  description: string;
  confidence: ConfidenceLevel;
  confidence_score: number;
  evidence: string;
  assumptions: string[];
  needs_validation: string[];
  recommended_action: string;
  category: string;
  agent_id: string;
  agent_name: string;
}

export interface AgentState {
  agent_id: string;
  agent_name: string;
  agent_icon: string;
  status: AgentStatus;
  findings: Finding[];
  summary: string;
  error?: string;
  thinking?: string;  // Extended thinking chain-of-thought (populated when ENABLE_THINKING=true)
}

export interface Contradiction {
  topic: string;
  agents: string[];
  description: string;
  resolution: string;
}

export interface ConfirmedCritical {
  topic: string;
  agents: string[];
  combined_evidence: string;
}

export interface Redundancy {
  topic: string;
  agents: string[];
  kept: string;
}

export interface ConsolidatorResult {
  contradictions: Contradiction[];
  confirmed_criticals: ConfirmedCritical[];
  redundancies: Redundancy[];
  audit_summary: string;
}

export interface SSEEvent {
  type:
    | "agent_start"
    | "agent_complete"
    | "agent_error"
    | "analysis_complete"
    | "consolidation_start"
    | "consolidation_complete"
    | "error";
  agent_id?: string;
  agent_name?: string;
  result?: AgentState;
  total_findings?: number;
  confidence_distribution?: { green: number; yellow: number; red: number };
  global_confidence_score?: number;
  consolidation?: ConsolidatorResult;
  error?: string;
}

export const AGENT_DEFINITIONS: Pick<AgentState, "agent_id" | "agent_name" | "agent_icon">[] = [
  { agent_id: "spec_analyst", agent_name: "Spec Analyst", agent_icon: "FileSearch" },
  { agent_id: "arch_validator", agent_name: "Architecture Validator", agent_icon: "GitBranch" },
  { agent_id: "risk_intelligence", agent_name: "Risk Intelligence", agent_icon: "Shield" },
  { agent_id: "business_impact", agent_name: "Business Impact", agent_icon: "TrendingUp" },
  { agent_id: "accessibility_advocate", agent_name: "Accessibility Advocate", agent_icon: "Eye" },
  { agent_id: "delivery_historian", agent_name: "Delivery Historian", agent_icon: "History" },
];

export const CONFIDENCE_COLORS: Record<ConfidenceLevel, { bg: string; border: string; text: string; badge: string }> = {
  green: {
    bg: "bg-confidence-green-dim",
    border: "border-confidence-green",
    text: "text-confidence-green",
    badge: "bg-confidence-green text-black",
  },
  yellow: {
    bg: "bg-confidence-yellow-dim",
    border: "border-confidence-yellow",
    text: "text-confidence-yellow",
    badge: "bg-confidence-yellow text-black",
  },
  red: {
    bg: "bg-confidence-red-dim",
    border: "border-confidence-red",
    text: "text-confidence-red",
    badge: "bg-confidence-red text-white",
  },
};

export const CONFIDENCE_LABELS: Record<ConfidenceLevel, string> = {
  green: "Explicitly defined",
  yellow: "Reasonably inferred",
  red: "High uncertainty",
};
