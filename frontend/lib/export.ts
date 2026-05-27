import type { AgentState, Finding } from "@/types";

export function generateMarkdown(
  agents: AgentState[],
  findings: Finding[],
  globalScore: number | null,
  confidenceDist: { green: number; yellow: number; red: number },
): string {
  const date = new Date().toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  const score = globalScore != null ? `${Math.round(globalScore * 100)}%` : "—";
  const reds = findings.filter((f) => f.confidence === "red");
  const yellows = findings.filter((f) => f.confidence === "yellow");
  const greens = findings.filter((f) => f.confidence === "green");

  const lines: string[] = [
    "# Confidence Map — Analysis Report",
    "",
    `**Date:** ${date}`,
    `**Global Confidence Score:** ${score}`,
    `**Total Findings:** ${findings.length} (${reds.length} critical · ${yellows.length} inferred · ${greens.length} confirmed)`,
    "",
    "---",
    "",
    "## Executive Summary",
    "",
  ];

  for (const agent of agents) {
    if (agent.summary) {
      lines.push(`### ${agent.agent_name}`);
      lines.push(agent.summary);
      lines.push("");
    }
  }

  const addSection = (title: string, fs: Finding[]) => {
    if (fs.length === 0) return;
    lines.push(`## ${title} (${fs.length})`);
    lines.push("");
    for (const f of fs) {
      lines.push(`### ${f.title}`);
      lines.push(
        `**Agent:** ${f.agent_name} · **Category:** ${f.category} · **Confidence:** ${Math.round(f.confidence_score * 100)}%`,
      );
      lines.push("");
      lines.push(f.description);
      lines.push("");
      if (f.evidence) {
        lines.push(`**Evidence:** ${f.evidence}`);
        lines.push("");
      }
      if (f.assumptions.length > 0) {
        lines.push("**Assumptions:**");
        f.assumptions.forEach((a) => lines.push(`- ${a}`));
        lines.push("");
      }
      if (f.needs_validation.length > 0) {
        lines.push("**Needs Validation:**");
        f.needs_validation.forEach((v) => lines.push(`- ${v}`));
        lines.push("");
      }
      if (f.recommended_action) {
        lines.push(`**Recommended Action:** ${f.recommended_action}`);
        lines.push("");
      }
    }
  };

  addSection("Critical — High Uncertainty", reds);
  addSection("Inferred — Reasonably Assumed", yellows);
  addSection("Confirmed — Explicitly Defined", greens);

  return lines.join("\n");
}

export function downloadMarkdown(content: string, filename?: string): void {
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename ?? `confidence-map-${new Date().toISOString().slice(0, 10)}.md`;
  a.click();
  URL.revokeObjectURL(url);
}
