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

// ── PDF export via styled print window ────────────────────────────────────────

function esc(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function findingCard(f: Finding, cls: string, badgeLabel: string, badgeCls: string): string {
  const validations =
    f.needs_validation.length > 0
      ? `<div class="checklist">
           <div class="checklist-label">Needs Validation</div>
           ${f.needs_validation.map((v) => `<div class="checklist-item">☐ ${esc(v)}</div>`).join("")}
         </div>`
      : "";
  const action = f.recommended_action
    ? `<div class="finding-action">→ ${esc(f.recommended_action)}</div>`
    : "";
  return `
    <div class="finding ${cls}">
      <div class="finding-header">
        <div class="finding-title">${esc(f.title)}</div>
        <span class="badge ${badgeCls}">${badgeLabel} · ${Math.round(f.confidence_score * 100)}%</span>
      </div>
      <div class="finding-meta">${esc(f.agent_name)} &nbsp;·&nbsp; ${esc(f.category)}</div>
      <div class="finding-desc">${esc(f.description)}</div>
      ${action}${validations}
    </div>`;
}

function findingsSection(
  title: string,
  fs: Finding[],
  cls: string,
  badge: string,
  badgeCls: string,
  dotCls: string,
): string {
  if (fs.length === 0) return "";
  return `
    <div class="section-heading">
      <span class="dot ${dotCls}"></span>
      ${esc(title)} <span class="section-count">(${fs.length})</span>
    </div>
    ${fs.map((f) => findingCard(f, cls, badge, badgeCls)).join("\n")}`;
}

export function exportPdf(
  agents: AgentState[],
  findings: Finding[],
  globalScore: number | null,
  confidenceDist: { green: number; yellow: number; red: number },
): void {
  const date = new Date().toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  const score = globalScore != null ? `${Math.round(globalScore * 100)}%` : "—";
  const reds = findings.filter((f) => f.confidence === "red");
  const yellows = findings.filter((f) => f.confidence === "yellow");
  const greens = findings.filter((f) => f.confidence === "green");

  const scoreColor =
    globalScore == null ? "#94a3b8"
    : globalScore >= 0.7 ? "#22c55e"
    : globalScore >= 0.45 ? "#f59e0b"
    : "#ef4444";

  const agentSummaries = agents
    .filter((a) => a.summary)
    .map(
      (a) => `
      <div class="agent-block">
        <div class="agent-name">${esc(a.agent_name)}</div>
        <div class="agent-text">${esc(a.summary)}</div>
      </div>`,
    )
    .join("");

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Confidence Map — Analysis Report</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#0f172a;background:#fff;font-size:10.5px;line-height:1.65}
  /* Cover */
  .cover{background:linear-gradient(135deg,#312e81 0%,#4f46e5 100%);color:#fff;padding:44px 44px 36px;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .cover-eyebrow{font-size:9px;letter-spacing:.18em;text-transform:uppercase;opacity:.7;margin-bottom:10px;font-family:monospace}
  .cover-title{font-size:24px;font-weight:800;margin-bottom:6px;letter-spacing:-.3px}
  .cover-date{font-size:10px;opacity:.75;font-family:monospace}
  .cover-score{display:inline-flex;flex-direction:column;margin-top:22px;background:rgba(255,255,255,.13);border-radius:10px;padding:14px 22px}
  .cover-score-num{font-size:30px;font-weight:900;font-family:monospace;color:${scoreColor};-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .cover-score-label{font-size:9px;text-transform:uppercase;letter-spacing:.1em;opacity:.7;margin-top:2px}
  .cover-stats{display:flex;gap:28px;margin-top:20px}
  .stat-val{font-size:18px;font-weight:800;font-family:monospace}
  .stat-red{color:#fca5a5;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .stat-yellow{color:#fcd34d;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .stat-green{color:#86efac;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .stat-label{font-size:9px;text-transform:uppercase;letter-spacing:.08em;opacity:.65;margin-top:1px}
  /* Body */
  .body{padding:32px 44px 48px;max-width:780px;margin:0 auto}
  h2{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.14em;color:#64748b;margin:28px 0 10px;border-bottom:1px solid #e2e8f0;padding-bottom:5px;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  /* Agent summaries */
  .agent-block{margin-bottom:10px}
  .agent-name{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#6366f1;margin-bottom:3px;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .agent-text{color:#475569}
  /* Section headings */
  .section-heading{display:flex;align-items:center;gap:8px;font-size:11px;font-weight:700;margin:26px 0 10px;color:#1e293b}
  .section-count{font-weight:400;color:#94a3b8;margin-left:2px}
  .dot{width:9px;height:9px;border-radius:50%;flex-shrink:0;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .dot-red{background:#ef4444}
  .dot-yellow{background:#f59e0b}
  .dot-green{background:#22c55e}
  /* Finding cards */
  .finding{border-left:3px solid #cbd5e1;padding:10px 14px;margin-bottom:9px;border-radius:0 6px 6px 0;page-break-inside:avoid;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .finding.f-red{border-color:#ef4444;background:#fff5f5}
  .finding.f-yellow{border-color:#f59e0b;background:#fffbeb}
  .finding.f-green{border-color:#22c55e;background:#f0fdf4}
  .finding-header{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;margin-bottom:4px}
  .finding-title{font-weight:700;font-size:11px;color:#0f172a;flex:1}
  .badge{font-size:8.5px;font-weight:700;text-transform:uppercase;padding:2px 7px;border-radius:4px;flex-shrink:0;font-family:monospace;letter-spacing:.04em;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .badge-red{background:#fecaca;color:#991b1b}
  .badge-yellow{background:#fef3c7;color:#78350f}
  .badge-green{background:#bbf7d0;color:#14532d}
  .finding-meta{font-size:9px;color:#94a3b8;font-family:monospace;margin-bottom:5px}
  .finding-desc{color:#334155;margin-bottom:5px}
  .finding-action{color:#1e293b;font-style:italic;padding-left:10px;border-left:2px solid #6366f1;margin-top:6px;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .checklist{margin-top:7px}
  .checklist-label{font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:.07em;color:#94a3b8;margin-bottom:3px}
  .checklist-item{color:#475569;margin-bottom:2px}
  /* Print */
  @media print{
    .print-btn{display:none!important}
    body{-webkit-print-color-adjust:exact;print-color-adjust:exact}
    h2{page-break-after:avoid}
    .section-heading{page-break-after:avoid}
  }
  /* Print button (screen only) */
  .print-btn{position:fixed;bottom:24px;right:24px;background:#6366f1;color:#fff;border:none;border-radius:10px;padding:12px 26px;font-size:13px;font-weight:600;cursor:pointer;box-shadow:0 4px 16px rgba(99,102,241,.35);font-family:inherit}
  .print-btn:hover{background:#4f46e5}
</style>
</head>
<body>
<div class="cover">
  <div class="cover-eyebrow">Confidence Map · Analysis Report</div>
  <div class="cover-title">Architecture &amp; Delivery Intelligence</div>
  <div class="cover-date">${esc(date)} &nbsp;·&nbsp; ${findings.length} findings across ${agents.length} agents</div>
  <div class="cover-score">
    <div class="cover-score-num">${esc(score)}</div>
    <div class="cover-score-label">Global Confidence Score</div>
  </div>
  <div class="cover-stats">
    <div>
      <div class="stat-val stat-red">${confidenceDist.red}</div>
      <div class="stat-label">Critical</div>
    </div>
    <div>
      <div class="stat-val stat-yellow">${confidenceDist.yellow}</div>
      <div class="stat-label">Inferred</div>
    </div>
    <div>
      <div class="stat-val stat-green">${confidenceDist.green}</div>
      <div class="stat-label">Confirmed</div>
    </div>
  </div>
</div>

<div class="body">
  ${agentSummaries.length > 0 ? `<h2>Executive Summary</h2>${agentSummaries}` : ""}
  ${findingsSection("Critical — High Uncertainty", reds, "f-red", "Critical", "badge-red", "dot-red")}
  ${findingsSection("Inferred — Reasonably Assumed", yellows, "f-yellow", "Inferred", "badge-yellow", "dot-yellow")}
  ${findingsSection("Confirmed — Explicitly Defined", greens, "f-green", "Confirmed", "badge-green", "dot-green")}
</div>

<button class="print-btn" onclick="window.print()">Save as PDF</button>
</body>
</html>`;

  const win = window.open("", "_blank");
  if (!win) {
    alert("Allow popups to export PDF");
    return;
  }
  win.document.write(html);
  win.document.close();
}
