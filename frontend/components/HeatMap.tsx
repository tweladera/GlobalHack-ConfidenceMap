"use client";

import { useState } from "react";
import type { Finding } from "@/types";

interface Props {
  findings: Finding[];
  onSelect: (f: Finding) => void;
  selectedFinding: Finding | null;
}

// ── Axis labels ───────────────────────────────────────────────────────────────

const LIKELIHOOD_LABELS = ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"];
const IMPACT_LABELS = ["Negligible", "Minor", "Moderate", "Major", "Catastrophic"];

// ── Category → Impact (X axis) ────────────────────────────────────────────────

const CATEGORY_IMPACT: Record<string, number> = {
  contradiction: 5,
  gap: 4,
  risk: 4,
  pattern: 3,
  cost: 3,
  ambiguity: 3,
  accessibility: 2,
};

// ── Risk matrix: "likelihood,impact" → risk level ─────────────────────────────

const RISK_LEVEL: Record<string, "low" | "medium" | "high" | "critical"> = {
  "1,1": "low",    "1,2": "low",    "1,3": "low",    "1,4": "low",      "1,5": "medium",
  "2,1": "low",    "2,2": "low",    "2,3": "low",    "2,4": "medium",   "2,5": "high",
  "3,1": "low",    "3,2": "low",    "3,3": "medium", "3,4": "high",     "3,5": "high",
  "4,1": "low",    "4,2": "medium", "4,3": "high",   "4,4": "high",     "4,5": "critical",
  "5,1": "medium", "5,2": "high",   "5,3": "high",   "5,4": "critical", "5,5": "critical",
};

const CELL_STYLES: Record<string, { bg: string; border: string; label: string; dot: string }> = {
  low:      { bg: "bg-emerald-950/70",  border: "border-emerald-700/30", label: "text-emerald-600", dot: "bg-emerald-700" },
  medium:   { bg: "bg-yellow-950/70",   border: "border-yellow-700/30",  label: "text-yellow-600",  dot: "bg-yellow-600" },
  high:     { bg: "bg-orange-950/70",   border: "border-orange-700/30",  label: "text-orange-500",  dot: "bg-orange-600" },
  critical: { bg: "bg-red-950/70",      border: "border-red-800/30",     label: "text-red-500",     dot: "bg-red-600" },
};

const RISK_LABEL: Record<string, string> = {
  low: "LOW", medium: "MED", high: "HIGH", critical: "CRIT",
};

const FINDING_STYLES: Record<string, string> = {
  red:    "bg-red-900/40 border-red-600/50 text-red-300 hover:bg-red-800/50",
  yellow: "bg-yellow-900/40 border-yellow-600/50 text-yellow-300 hover:bg-yellow-800/50",
  green:  "bg-emerald-900/40 border-emerald-600/50 text-emerald-300 hover:bg-emerald-800/50",
};

const FINDING_SELECTED: Record<string, string> = {
  red:    "ring-1 ring-red-400",
  yellow: "ring-1 ring-yellow-400",
  green:  "ring-1 ring-emerald-400",
};

// ── Mapping helpers ───────────────────────────────────────────────────────────

function getLikelihood(f: Finding): number {
  if (f.confidence === "red")    return f.confidence_score < 0.1 ? 5 : 4;
  if (f.confidence === "yellow") return f.confidence_score < 0.35 ? 3 : 2;
  return 1;
}

function getImpact(f: Finding): number {
  return CATEGORY_IMPACT[f.category?.toLowerCase() ?? ""] ?? 3;
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function HeatMap({ findings, onSelect, selectedFinding }: Props) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  // Build cell map: "likelihood,impact" → Finding[]
  const cellMap = new Map<string, Finding[]>();
  for (const f of findings) {
    const key = `${getLikelihood(f)},${getImpact(f)}`;
    if (!cellMap.has(key)) cellMap.set(key, []);
    cellMap.get(key)!.push(f);
  }

  return (
    <div className="flex flex-1 flex-col h-full overflow-auto p-6 animate-fade-in">
      <div className="w-full max-w-5xl mx-auto">

        {/* Header */}
        <div className="mb-5 flex items-end justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-200">Risk Heat Map</h2>
            <p className="text-xs text-slate-500 mt-0.5 font-mono">
              {findings.length} findings · Likelihood × Impact
            </p>
          </div>
          {/* Legend */}
          <div className="flex items-center gap-3">
            {(["low", "medium", "high", "critical"] as const).map((r) => (
              <div key={r} className="flex items-center gap-1.5">
                <div className={`w-2.5 h-2.5 rounded-sm ${CELL_STYLES[r].bg} border ${CELL_STYLES[r].border}`} />
                <span className={`text-[10px] font-mono uppercase ${CELL_STYLES[r].label}`}>
                  {RISK_LABEL[r]}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="flex gap-2">
          {/* Y-axis vertical label */}
          <div className="flex items-center justify-center w-5 flex-shrink-0">
            <span
              className="text-[9px] font-mono text-slate-600 uppercase tracking-widest select-none"
              style={{ writingMode: "vertical-rl", transform: "rotate(180deg)" }}
            >
              Probability / Likelihood
            </span>
          </div>

          {/* Main grid area */}
          <div className="flex flex-col gap-1 flex-1">

            {/* Rows: y=5 (top) → y=1 (bottom) */}
            {[5, 4, 3, 2, 1].map((y) => (
              <div key={y} className="flex gap-1 items-stretch" style={{ minHeight: "90px" }}>

                {/* Y-axis row label */}
                <div className="w-24 flex-shrink-0 flex items-center justify-end pr-2">
                  <div className="text-right">
                    <div className="text-[9px] font-mono text-slate-600 uppercase">{y}</div>
                    <div className="text-[9px] text-slate-500 leading-tight">{LIKELIHOOD_LABELS[y - 1]}</div>
                  </div>
                </div>

                {/* 5 cells for this row */}
                {[1, 2, 3, 4, 5].map((x) => {
                  const key = `${y},${x}`;
                  const risk = RISK_LEVEL[key] ?? "low";
                  const s = CELL_STYLES[risk];
                  const cellFindings = cellMap.get(key) ?? [];

                  return (
                    <div
                      key={x}
                      className={`flex-1 rounded-lg border p-1.5 relative flex flex-col gap-1 ${s.bg} ${s.border}`}
                    >
                      {/* Risk watermark when empty */}
                      {cellFindings.length === 0 && (
                        <span className={`absolute top-1 right-1.5 text-[8px] font-mono opacity-25 select-none ${s.label}`}>
                          {RISK_LABEL[risk]}
                        </span>
                      )}

                      {/* Count badge when has findings */}
                      {cellFindings.length > 0 && (
                        <span className={`absolute top-1 right-1.5 text-[8px] font-mono font-bold ${s.label}`}>
                          {cellFindings.length}
                        </span>
                      )}

                      {/* Findings */}
                      {cellFindings.map((f) => {
                        const isSelected = selectedFinding?.id === f.id;
                        const isHovered = hoveredId === f.id;
                        const fs = FINDING_STYLES[f.confidence] ?? FINDING_STYLES.green;
                        const fsel = FINDING_SELECTED[f.confidence] ?? "";

                        return (
                          <div key={f.id} className="relative">
                            <button
                              onClick={() => onSelect(f)}
                              onMouseEnter={() => setHoveredId(f.id)}
                              onMouseLeave={() => setHoveredId(null)}
                              className={`
                                w-full text-left px-1.5 py-1 rounded border text-[9px]
                                leading-snug transition-all font-mono
                                ${fs} ${isSelected ? fsel : ""}
                              `}
                              aria-label={`${f.title} — ${f.confidence} — ${f.agent_name}`}
                              aria-current={isSelected ? "true" : undefined}
                            >
                              <span className="line-clamp-2">{f.title}</span>
                            </button>

                            {/* Tooltip */}
                            {isHovered && (
                              <div className="absolute z-50 bottom-full left-0 mb-1.5 w-60 bg-surface-card border border-surface-border rounded-xl p-3 shadow-2xl pointer-events-none">
                                <p className="text-[11px] text-slate-200 leading-snug font-medium">{f.title}</p>
                                <div className="flex items-center gap-1.5 mt-1.5">
                                  <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                                    f.confidence === "red" ? "bg-confidence-red" :
                                    f.confidence === "yellow" ? "bg-confidence-yellow" : "bg-confidence-green"
                                  }`} />
                                  <span className="text-[9px] font-mono text-slate-400">
                                    {f.agent_name} · {f.category} · {Math.round(f.confidence_score * 100)}%
                                  </span>
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  );
                })}
              </div>
            ))}

            {/* X-axis labels */}
            <div className="flex gap-1 mt-1">
              <div className="w-24 flex-shrink-0" />
              {IMPACT_LABELS.map((label, i) => (
                <div key={i} className="flex-1 text-center">
                  <div className="text-[9px] font-mono text-slate-600 uppercase">{i + 1}</div>
                  <div className="text-[9px] text-slate-500 leading-tight">{label}</div>
                </div>
              ))}
            </div>

            {/* X-axis label */}
            <div className="flex gap-1 mt-0.5">
              <div className="w-24 flex-shrink-0" />
              <div className="flex-1 text-center">
                <span className="text-[9px] font-mono text-slate-600 uppercase tracking-widest">
                  Severity / Impact
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Summary bar */}
        <div className="mt-5 pl-[6.5rem] flex gap-4 text-[10px] font-mono text-slate-500">
          {(["critical", "high", "medium", "low"] as const).map((r) => {
            const count = findings.filter((f) => {
              const key = `${getLikelihood(f)},${getImpact(f)}`;
              return (RISK_LEVEL[key] ?? "low") === r;
            }).length;
            return (
              <span key={r} className={count > 0 ? CELL_STYLES[r].label : "opacity-30"}>
                {RISK_LABEL[r]}: {count}
              </span>
            );
          })}
        </div>
      </div>
    </div>
  );
}
