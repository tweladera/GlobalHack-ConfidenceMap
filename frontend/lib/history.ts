import type { AgentState } from "@/types";

export interface AnalysisRecord {
  id: string;
  timestamp: number;
  specPreview: string;
  globalScore: number | null;
  totalFindings: number;
  confidenceDist: { green: number; yellow: number; red: number };
  agents: AgentState[];
}

const KEY = "cm_history";
const MAX = 5;

export function saveAnalysis(record: Omit<AnalysisRecord, "id">): AnalysisRecord {
  const entry: AnalysisRecord = { ...record, id: crypto.randomUUID() };
  const existing = getHistory();
  const updated = [entry, ...existing].slice(0, MAX);
  localStorage.setItem(KEY, JSON.stringify(updated));
  return entry;
}

export function getHistory(): AnalysisRecord[] {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as AnalysisRecord[]) : [];
  } catch {
    return [];
  }
}

export function clearHistory(): void {
  localStorage.removeItem(KEY);
}
