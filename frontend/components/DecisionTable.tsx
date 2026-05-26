"use client";

import { useState } from "react";
import type { Finding, ConfidenceLevel } from "@/types";
import { CONFIDENCE_LABELS } from "@/types";

interface DecisionTableProps {
  findings: Finding[];
  onSelect: (finding: Finding) => void;
  selectedFinding: Finding | null;
}

const LEVEL_STYLES: Record<ConfidenceLevel, string> = {
  green: "bg-confidence-green-dim text-confidence-green border-confidence-green/30",
  yellow: "bg-confidence-yellow-dim text-confidence-yellow border-confidence-yellow/30",
  red: "bg-confidence-red-dim text-confidence-red border-confidence-red/30",
};

const DOT_STYLES: Record<ConfidenceLevel, string> = {
  green: "bg-confidence-green",
  yellow: "bg-confidence-yellow",
  red: "bg-confidence-red",
};

type Filter = "all" | ConfidenceLevel;

const FILTERS: { key: Filter; label: string }[] = [
  { key: "all", label: "All" },
  { key: "red", label: "Critical" },
  { key: "yellow", label: "Inferred" },
  { key: "green", label: "Confirmed" },
];

export default function DecisionTable({ findings, onSelect, selectedFinding }: DecisionTableProps) {
  const [filter, setFilter] = useState<Filter>("all");

  const filtered = filter === "all" ? findings : findings.filter((f) => f.confidence === filter);

  const counts = {
    all: findings.length,
    red: findings.filter((f) => f.confidence === "red").length,
    yellow: findings.filter((f) => f.confidence === "yellow").length,
    green: findings.filter((f) => f.confidence === "green").length,
  };

  if (findings.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500 text-sm">
        No findings yet — waiting for agents to complete
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Filter bar */}
      <div
        className="flex-shrink-0 flex items-center gap-2 px-6 py-3 border-b border-surface-border bg-surface-card"
        role="toolbar"
        aria-label="Filter findings by confidence level"
      >
        {FILTERS.map(({ key, label }) => {
          const active = filter === key;
          const count = counts[key];
          return (
            <button
              key={key}
              onClick={() => setFilter(key)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${
                active
                  ? key === "all"
                    ? "bg-accent text-white"
                    : key === "red"
                    ? "bg-confidence-red text-white"
                    : key === "yellow"
                    ? "bg-confidence-yellow text-black"
                    : "bg-confidence-green text-black"
                  : "bg-surface border border-surface-border text-slate-400 hover:border-slate-600"
              }`}
              aria-pressed={active}
            >
              {key !== "all" && (
                <span
                  className={`w-1.5 h-1.5 rounded-full ${active ? "bg-current opacity-60" : DOT_STYLES[key as ConfidenceLevel]}`}
                  aria-hidden="true"
                />
              )}
              {label}
              <span className={`tabular-nums ${active ? "opacity-70" : "text-slate-500"}`}>
                {count}
              </span>
            </button>
          );
        })}
        <span className="ml-auto text-xs text-slate-500 font-mono">
          {filtered.length} of {findings.length} findings
        </span>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-y-auto">
        <table className="w-full text-xs" role="grid" aria-label="Decision findings table">
          <thead className="sticky top-0 z-10">
            <tr className="bg-surface-card border-b border-surface-border text-slate-500 uppercase tracking-widest text-[10px]">
              <th className="text-left px-4 py-2.5 font-semibold w-8">#</th>
              <th className="text-left px-4 py-2.5 font-semibold">Finding</th>
              <th className="text-left px-4 py-2.5 font-semibold w-36">Agent</th>
              <th className="text-left px-4 py-2.5 font-semibold w-28">Level</th>
              <th className="text-right px-4 py-2.5 font-semibold w-16">Score</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((finding, idx) => {
              const isSelected = selectedFinding?.id === finding.id;
              const score = Math.round(finding.confidence_score * 100);
              return (
                <tr
                  key={finding.id}
                  onClick={() => onSelect(finding)}
                  className={`border-b border-surface-border cursor-pointer transition-all ${
                    isSelected
                      ? "bg-accent-dim"
                      : "hover:bg-surface-hover"
                  }`}
                  aria-selected={isSelected}
                  role="row"
                  tabIndex={0}
                  onKeyDown={(e) => e.key === "Enter" && onSelect(finding)}
                >
                  <td className="px-4 py-3 text-slate-600 font-mono tabular-nums">{idx + 1}</td>
                  <td className="px-4 py-3">
                    <p className="text-slate-200 leading-snug font-medium">{finding.title}</p>
                    {finding.recommended_action && (
                      <p className="text-slate-500 mt-0.5 leading-relaxed line-clamp-1">
                        → {finding.recommended_action}
                      </p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-400">{finding.agent_name}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[10px] font-mono uppercase ${
                        LEVEL_STYLES[finding.confidence]
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${DOT_STYLES[finding.confidence]}`}
                        aria-hidden="true"
                      />
                      {CONFIDENCE_LABELS[finding.confidence].split(" ")[0]}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span
                      className={`font-mono tabular-nums font-semibold ${
                        finding.confidence === "green"
                          ? "text-confidence-green"
                          : finding.confidence === "yellow"
                          ? "text-confidence-yellow"
                          : "text-confidence-red"
                      }`}
                    >
                      {score}%
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
