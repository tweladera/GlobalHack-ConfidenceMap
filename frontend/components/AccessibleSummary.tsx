"use client";

import { useState } from "react";
import type { AgentState, Finding } from "@/types";

interface AccessibleSummaryProps {
  agents: AgentState[];
  findings: Finding[];
  isComplete: boolean;
}

export default function AccessibleSummary({ agents, findings, isComplete }: AccessibleSummaryProps) {
  const [isOpen, setIsOpen] = useState(false);

  const greenCount = findings.filter((f) => f.confidence === "green").length;
  const yellowCount = findings.filter((f) => f.confidence === "yellow").length;
  const redCount = findings.filter((f) => f.confidence === "red").length;

  const completedAgents = agents.filter((a) => a.status === "completed");
  const runningAgents = agents.filter((a) => a.status === "running");

  const statusText = isComplete
    ? `Analysis complete. Found ${findings.length} total findings: ${greenCount} explicitly defined, ${yellowCount} reasonably inferred, and ${redCount} with high uncertainty or contradiction.`
    : `Analysis in progress. ${completedAgents.length} of ${agents.length} agents have completed. ${runningAgents.map((a) => a.agent_name).join(" and ")} ${runningAgents.length === 1 ? "is" : "are"} currently analyzing.`;

  return (
    <>
      {/* Live region for screen readers — updates as agents complete */}
      <div
        aria-live="polite"
        aria-atomic="false"
        className="sr-only"
        role="status"
      >
        {statusText}
      </div>

      {/* Accessible summary panel — visible toggle */}
      <div className="fixed bottom-4 left-4 z-50">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="bg-surface-card border border-surface-border rounded-full px-4 py-2 text-sm text-slate-300 hover:text-white hover:border-slate-500 transition-all shadow-lg flex items-center gap-2"
          aria-expanded={isOpen}
          aria-controls="accessible-summary-panel"
          aria-label={isOpen ? "Hide text summary" : "Show text summary for screen readers"}
        >
          <span aria-hidden="true">{isOpen ? "▶" : "◎"}</span>
          {isOpen ? "Hide summary" : "Text summary"}
        </button>

        {isOpen && (
          <div
            id="accessible-summary-panel"
            className="absolute bottom-12 left-0 w-80 bg-surface-card border border-surface-border rounded-xl p-4 shadow-xl animate-slide-up"
            role="region"
            aria-label="Accessible text summary of confidence map"
          >
            <h2 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
              <span aria-hidden="true">◎</span>
              Analysis Summary
            </h2>

            <p className="text-sm text-slate-300 leading-relaxed mb-4">{statusText}</p>

            {findings.length > 0 && (
              <>
                <div
                  className="grid grid-cols-3 gap-2 mb-4"
                  role="group"
                  aria-label="Finding counts by confidence level"
                >
                  {[
                    { level: "green", label: "Confirmed", count: greenCount },
                    { level: "yellow", label: "Inferred", count: yellowCount },
                    { level: "red", label: "Uncertain", count: redCount },
                  ].map(({ level, label, count }) => (
                    <div
                      key={level}
                      className={`text-center p-2 rounded-lg bg-confidence-${level}-dim`}
                      aria-label={`${count} ${label} findings`}
                    >
                      <div className={`text-xl font-bold text-confidence-${level}`}>{count}</div>
                      <div className="text-[10px] text-slate-400">{label}</div>
                    </div>
                  ))}
                </div>

                {redCount > 0 && (
                  <div className="mb-3">
                    <h3 className="text-xs font-semibold text-confidence-red uppercase tracking-wide mb-2">
                      High-priority findings
                    </h3>
                    <ul className="space-y-1" aria-label="High uncertainty findings">
                      {findings
                        .filter((f) => f.confidence === "red")
                        .slice(0, 3)
                        .map((f) => (
                          <li key={f.id} className="text-xs text-slate-400 leading-snug">
                            <span className="text-confidence-red font-mono mr-1">!</span>
                            {f.title} — {f.agent_name}
                          </li>
                        ))}
                    </ul>
                  </div>
                )}

                <div>
                  <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                    Agent summaries
                  </h3>
                  <ul className="space-y-2" aria-label="Agent summaries">
                    {completedAgents.map((agent) => (
                      <li key={agent.agent_id}>
                        <span className="text-xs font-semibold text-slate-300">{agent.agent_name}: </span>
                        <span className="text-xs text-slate-400 leading-snug">{agent.summary}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </>
  );
}
