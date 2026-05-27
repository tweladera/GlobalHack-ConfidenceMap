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
      <div aria-live="polite" aria-atomic="false" className="sr-only" role="status">
        {statusText}
      </div>

      {/* Inline toggle — embedded in the left sidebar by the parent */}
      <div className="mt-4 border-t border-surface-border pt-4">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full flex items-center justify-between text-xs text-slate-500 hover:text-slate-300 transition-colors font-mono py-1"
          aria-expanded={isOpen}
          aria-controls="accessible-summary-panel"
          aria-label={isOpen ? "Hide text summary" : "Show text summary"}
        >
          <span className="flex items-center gap-1.5">
            <span aria-hidden="true">◎</span>
            Text summary
          </span>
          <span aria-hidden="true" className="text-slate-600">{isOpen ? "▲" : "▼"}</span>
        </button>

        {isOpen && (
          <div
            id="accessible-summary-panel"
            className="mt-3 space-y-3"
            role="region"
            aria-label="Accessible text summary of confidence map"
          >
            <p className="text-xs text-slate-400 leading-relaxed">{statusText}</p>

            {findings.length > 0 && (
              <>
                <div
                  className="grid grid-cols-3 gap-1.5"
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
                      <div className={`text-base font-bold text-confidence-${level}`}>{count}</div>
                      <div className="text-[9px] text-slate-500">{label}</div>
                    </div>
                  ))}
                </div>

                {redCount > 0 && (
                  <div>
                    <p className="text-[10px] font-semibold text-confidence-red uppercase tracking-wide mb-1">
                      High-priority
                    </p>
                    <ul className="space-y-1">
                      {findings
                        .filter((f) => f.confidence === "red")
                        .slice(0, 3)
                        .map((f) => (
                          <li key={f.id} className="text-[10px] text-slate-400 leading-snug">
                            <span className="text-confidence-red mr-1">!</span>
                            {f.title}
                          </li>
                        ))}
                    </ul>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </>
  );
}
