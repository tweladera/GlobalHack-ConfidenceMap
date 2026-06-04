"use client";

import { useState } from "react";
import type { AgentState } from "@/types";

const BADGE_COLORS = {
  green: "bg-confidence-green-dim text-confidence-green",
  yellow: "bg-confidence-yellow-dim text-confidence-yellow",
  red: "bg-confidence-red-dim text-confidence-red",
} as const;

interface AgentStatusCardProps {
  agents: AgentState[];
  completionOrder: string[];
}

export default function AgentStatusCard({ agents, completionOrder }: AgentStatusCardProps) {
  const [expandedThinking, setExpandedThinking] = useState<string | null>(null);
  const completedCount = agents.filter((a) => a.status === "completed").length;
  const total = agents.length;

  return (
    <section aria-label="Agent analysis status">
      {/* Header + progress bar */}
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-widest">
          Agents
        </h2>
        <span className="text-[10px] font-mono text-slate-600">{completedCount}/{total}</span>
      </div>
      <div className="h-1 bg-surface-border rounded-full overflow-hidden mb-4" aria-hidden="true">
        <div
          className="h-full bg-accent rounded-full transition-all duration-700"
          style={{ width: `${(completedCount / total) * 100}%` }}
        />
      </div>

      {/* Timeline */}
      <ul role="list" className="relative">
        {/* Vertical connector line */}
        <div
          className="absolute left-[7px] top-2 bottom-2 w-px bg-surface-border"
          aria-hidden="true"
        />

        {agents.map((agent) => {
          const isCompleted = agent.status === "completed";
          const isRunning = agent.status === "running";
          const isError = agent.status === "error";
          const rank = completionOrder.indexOf(agent.agent_id);
          const hasThinking = !!(agent.thinking && agent.thinking.length > 0);
          const isExpanded = expandedThinking === agent.agent_id;

          const dotClass = isCompleted
            ? "bg-confidence-green border-confidence-green"
            : isRunning
            ? "bg-accent border-accent"
            : isError
            ? "bg-confidence-red border-confidence-red"
            : "bg-surface border-surface-border";

          const nameClass = isCompleted
            ? "text-slate-300"
            : isRunning
            ? "text-accent"
            : isError
            ? "text-confidence-red"
            : "text-slate-600";

          return (
            <li
              key={agent.agent_id}
              className="relative pl-6 pb-4 last:pb-0"
              aria-label={`${agent.agent_name}: ${agent.status}${agent.findings.length > 0 ? `, ${agent.findings.length} findings` : ""}`}
            >
              {/* Status dot */}
              <div
                className={`absolute left-0 top-1 w-3.5 h-3.5 rounded-full border-2 z-10 transition-colors duration-300 ${dotClass}`}
                aria-hidden="true"
              >
                {isRunning && (
                  <span className="absolute inset-0 rounded-full animate-ping bg-accent opacity-25" />
                )}
              </div>

              {/* Agent name + rank/spinner */}
              <div className="flex items-start justify-between gap-1 min-w-0">
                <span className={`text-xs font-medium leading-snug truncate ${nameClass}`}>
                  {agent.agent_name}
                </span>
                <div className="flex items-center gap-1 flex-shrink-0 mt-0.5">
                  {isRunning && (
                    <span
                      className="w-3 h-3 border border-accent/30 border-t-accent rounded-full animate-spin"
                      aria-hidden="true"
                    />
                  )}
                  {isCompleted && rank >= 0 && (
                    <span className="text-[9px] font-mono text-slate-600">#{rank + 1}</span>
                  )}
                </div>
              </div>

              {/* Findings mini-distribution */}
              {isCompleted && agent.findings.length > 0 && (
                <div
                  className="flex gap-1 mt-1"
                  aria-label={`Findings: ${agent.findings.filter(f => f.confidence === "green").length} confirmed, ${agent.findings.filter(f => f.confidence === "yellow").length} inferred, ${agent.findings.filter(f => f.confidence === "red").length} uncertain`}
                >
                  {(["green", "yellow", "red"] as const).map((level) => {
                    const count = agent.findings.filter((f) => f.confidence === level).length;
                    if (count === 0) return null;
                    return (
                      <span
                        key={level}
                        className={`text-[9px] px-1.5 py-0.5 rounded font-mono ${BADGE_COLORS[level]}`}
                        aria-hidden="true"
                      >
                        {count}{level === "green" ? "✓" : level === "yellow" ? "~" : "!"}
                      </span>
                    );
                  })}
                </div>
              )}

              {/* Error message */}
              {isError && agent.error && (
                <p className="text-[10px] text-confidence-red mt-0.5 truncate" role="alert">
                  {agent.error}
                </p>
              )}

              {/* Extended thinking toggle */}
              {hasThinking && (
                <>
                  <button
                    onClick={() => setExpandedThinking(isExpanded ? null : agent.agent_id)}
                    className="mt-1 text-[10px] text-accent/60 hover:text-accent font-mono flex items-center gap-1 transition-colors"
                    aria-expanded={isExpanded}
                    aria-controls={`thinking-${agent.agent_id}`}
                  >
                    <span aria-hidden="true">{isExpanded ? "▾" : "▸"}</span>
                    {isExpanded ? "Hide reasoning" : "Show reasoning"}
                  </button>
                  {isExpanded && (
                    <div
                      id={`thinking-${agent.agent_id}`}
                      role="region"
                      aria-label={`${agent.agent_name} chain of thought`}
                      className="mt-1.5 text-[10px] text-slate-500 font-mono whitespace-pre-wrap leading-relaxed max-h-40 overflow-y-auto bg-surface rounded-lg p-2 border border-surface-border animate-fade-in"
                    >
                      {agent.thinking}
                    </div>
                  )}
                </>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
