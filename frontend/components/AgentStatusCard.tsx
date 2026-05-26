"use client";

import type { AgentState } from "@/types";

const STATUS_STYLES = {
  pending: "text-slate-500 border-surface-border",
  running: "text-accent border-accent animate-pulse_slow",
  completed: "text-slate-300 border-slate-600",
  error: "text-confidence-red border-confidence-red",
};

const STATUS_LABEL = {
  pending: "Waiting",
  running: "Analyzing...",
  completed: "Done",
  error: "Error",
};

interface AgentStatusCardProps {
  agents: AgentState[];
}

export default function AgentStatusCard({ agents }: AgentStatusCardProps) {
  return (
    <section aria-label="Agent analysis status" className="space-y-2">
      <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">
        Agents
      </h2>
      <ul role="list" className="space-y-2">
        {agents.map((agent) => {
          const style = STATUS_STYLES[agent.status] ?? STATUS_STYLES.pending;
          const label = STATUS_LABEL[agent.status] ?? agent.status;
          const findingCount = agent.findings.length;

          return (
            <li
              key={agent.agent_id}
              className={`bg-surface-card border rounded-xl px-4 py-3 transition-all ${style}`}
              aria-label={`${agent.agent_name}: ${label}${findingCount > 0 ? `, ${findingCount} findings` : ""}`}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium truncate">{agent.agent_name}</span>
                <div className="flex items-center gap-2">
                  {agent.status === "running" && (
                    <span
                      className="w-3 h-3 border-2 border-accent/30 border-t-accent rounded-full animate-spin"
                      aria-hidden="true"
                    />
                  )}
                  <span className="text-xs font-mono">{label}</span>
                </div>
              </div>

              {agent.status === "completed" && findingCount > 0 && (
                <div
                  className="flex gap-2 mt-2"
                  aria-label={`${agent.findings.filter(f => f.confidence === 'green').length} confirmed, ${agent.findings.filter(f => f.confidence === 'yellow').length} inferred, ${agent.findings.filter(f => f.confidence === 'red').length} uncertain`}
                >
                  {(["green", "yellow", "red"] as const).map((level) => {
                    const count = agent.findings.filter((f) => f.confidence === level).length;
                    if (count === 0) return null;
                    const colors = {
                      green: "bg-confidence-green-dim text-confidence-green",
                      yellow: "bg-confidence-yellow-dim text-confidence-yellow",
                      red: "bg-confidence-red-dim text-confidence-red",
                    };
                    return (
                      <span
                        key={level}
                        className={`text-[10px] px-2 py-0.5 rounded font-mono ${colors[level]}`}
                        aria-hidden="true"
                      >
                        {count} {level}
                      </span>
                    );
                  })}
                </div>
              )}

              {agent.status === "error" && agent.error && (
                <p className="text-xs text-confidence-red mt-1 truncate" role="alert">
                  {agent.error}
                </p>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
