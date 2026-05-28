"use client";

import { useState } from "react";
import type { Finding } from "@/types";

interface Props {
  findings: Finding[];
  onClose: () => void;
}

function generateTicket(f: Finding, index: number): string {
  const priority = f.confidence === "red" ? "Critical" : "High";
  const lines = [
    `## TICKET-${String(index + 1).padStart(3, "0")}: ${f.title}`,
    "",
    `**Priority:** ${priority}`,
    `**Agent:** ${f.agent_name}`,
    `**Category:** ${f.category}`,
    "",
    "### Description",
    f.description,
    "",
  ];
  if (f.recommended_action) {
    lines.push("### Implementation Notes");
    lines.push(f.recommended_action);
    lines.push("");
  }
  if (f.needs_validation.length > 0) {
    lines.push("### Acceptance Criteria");
    f.needs_validation.forEach((v) => lines.push(`- [ ] ${v}`));
    lines.push("");
  }
  if (f.assumptions.length > 0) {
    lines.push("### Assumptions to Resolve");
    f.assumptions.forEach((a) => lines.push(`- ${a}`));
    lines.push("");
  }
  return lines.join("\n");
}

export default function BacklogModal({ findings, onClose }: Props) {
  const actionable = findings.filter(
    (f) => f.confidence === "red" || f.confidence === "yellow",
  );
  const [filter, setFilter] = useState<"all" | "red" | "yellow">("all");
  const [copied, setCopied] = useState(false);

  const visible =
    filter === "all" ? actionable : actionable.filter((f) => f.confidence === filter);
  const content = visible.map((f, i) => generateTicket(f, i)).join("\n---\n\n");

  const copyAll = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const download = () => {
    const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `confidence-map-backlog-${new Date().toISOString().slice(0, 10)}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const criticalCount = actionable.filter((f) => f.confidence === "red").length;
  const highCount = actionable.filter((f) => f.confidence === "yellow").length;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in"
      role="dialog"
      aria-modal="true"
      aria-label="Generated backlog tickets"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="w-full max-w-3xl max-h-[85vh] flex flex-col bg-surface-card border border-surface-border rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-surface-border flex-shrink-0">
          <div>
            <h2 className="text-sm font-semibold text-slate-200">Generated Backlog</h2>
            <p className="text-xs text-slate-500 font-mono mt-0.5">
              {visible.length} tickets · {criticalCount} critical · {highCount} high
            </p>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center rounded-lg border border-surface-border overflow-hidden text-xs font-mono">
              {(["all", "red", "yellow"] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`px-3 py-1.5 transition-colors border-l first:border-l-0 border-surface-border ${filter === f ? "bg-accent text-white" : "text-slate-400 hover:text-slate-200"}`}
                >
                  {f === "all" ? "All" : f === "red" ? "Critical" : "High"}
                </button>
              ))}
            </div>
            <button
              onClick={() => void copyAll()}
              className="text-xs px-3 py-1.5 rounded-lg border border-surface-border text-slate-400 hover:text-slate-200 transition-colors font-mono"
            >
              {copied ? "Copied!" : "Copy all"}
            </button>
            <button
              onClick={download}
              className="text-xs px-3 py-1.5 rounded-lg border border-surface-border text-slate-400 hover:text-slate-200 transition-colors font-mono"
            >
              Download .md
            </button>
            <button
              onClick={onClose}
              className="text-slate-500 hover:text-slate-200 transition-colors px-2 text-sm"
              aria-label="Close backlog modal"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Ticket list */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {visible.length === 0 ? (
            <p className="text-slate-500 text-sm text-center py-8">
              No findings match this filter.
            </p>
          ) : (
            visible.map((f, i) => (
              <div
                key={f.id}
                className={`rounded-xl border p-4 ${
                  f.confidence === "red"
                    ? "border-confidence-red/30 bg-confidence-red-dim"
                    : "border-confidence-yellow/30 bg-confidence-yellow-dim"
                }`}
              >
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div>
                    <span className="text-[10px] font-mono text-slate-500">
                      TICKET-{String(i + 1).padStart(3, "0")}
                    </span>
                    <h3 className="text-sm font-semibold text-slate-200 leading-snug">
                      {f.title}
                    </h3>
                    <p className="text-[10px] font-mono text-slate-500 mt-0.5">
                      {f.agent_name} · {f.category}
                    </p>
                  </div>
                  <span
                    className={`flex-shrink-0 text-[9px] font-mono font-bold px-2 py-1 rounded uppercase ${
                      f.confidence === "red"
                        ? "bg-red-900 text-red-300"
                        : "bg-yellow-900 text-yellow-300"
                    }`}
                  >
                    {f.confidence === "red" ? "Critical" : "High"}
                  </span>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed mb-3">{f.description}</p>

                {f.recommended_action && (
                  <p className="text-xs text-slate-200 pl-3 border-l-2 border-accent/40 italic mb-3">
                    → {f.recommended_action}
                  </p>
                )}

                {f.needs_validation.length > 0 && (
                  <div>
                    <p className="text-[10px] font-mono text-slate-500 uppercase mb-1">
                      Acceptance Criteria
                    </p>
                    <ul className="space-y-0.5">
                      {f.needs_validation.map((v, vi) => (
                        <li key={vi} className="text-xs text-slate-400 flex items-start gap-1.5">
                          <span className="mt-0.5 text-slate-600 flex-shrink-0">☐</span>
                          {v}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
