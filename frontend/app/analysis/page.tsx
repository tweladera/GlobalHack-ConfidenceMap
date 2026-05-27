"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import AgentStatusCard from "@/components/AgentStatusCard";
import FindingDetail from "@/components/FindingDetail";
import AccessibleSummary from "@/components/AccessibleSummary";
import DecisionTable from "@/components/DecisionTable";
import type { AgentState, Finding, SSEEvent } from "@/types";
import { AGENT_DEFINITIONS } from "@/types";
import { useI18n } from "@/lib/i18n";
import LanguageSwitcher from "@/components/LanguageSwitcher";

// React Flow must be loaded client-side only (no SSR)
const ConfidenceMap = dynamic(() => import("@/components/ConfidenceMap"), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full">
      <div className="text-slate-500 text-sm animate-pulse">Loading confidence map...</div>
    </div>
  ),
});

const INITIAL_AGENTS: AgentState[] = AGENT_DEFINITIONS.map((a) => ({
  ...a,
  status: "pending",
  findings: [],
  summary: "",
}));

export default function AnalysisPage() {
  const router = useRouter();
  const { t, lang } = useI18n();
  const [agents, setAgents] = useState<AgentState[]>(INITIAL_AGENTS);
  const [allFindings, setAllFindings] = useState<Finding[]>([]);
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const [confidenceDist, setConfidenceDist] = useState({ green: 0, yellow: 0, red: 0 });
  const [globalScore, setGlobalScore] = useState<number | null>(null);
  const [connectionError, setConnectionError] = useState("");
  const [timeoutWarning, setTimeoutWarning] = useState(false);
  const [showTable, setShowTable] = useState(false);
  const [textMode, setTextMode] = useState(false);
  const [copied, setCopied] = useState(false);
  const [announcement, setAnnouncement] = useState("");
  const [isTranslating, setIsTranslating] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const announceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Prevents translation from firing on the initial analysis_complete event
  const analysisJustCompletedRef = useRef(false);

  const announce = (text: string) => {
    // Clear → re-set so screen readers fire a new announcement even if text is similar
    setAnnouncement("");
    if (announceTimerRef.current) clearTimeout(announceTimerRef.current);
    announceTimerRef.current = setTimeout(() => setAnnouncement(text), 60);
  };

  // Keyboard shortcuts: Alt+1 Map · Alt+2 Table · Alt+3 Text
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (!e.altKey) return;
      if (e.key === "1") { e.preventDefault(); setTextMode(false); setShowTable(false); }
      if (e.key === "2") { e.preventDefault(); setTextMode(false); setShowTable(true); }
      if (e.key === "3") { e.preventDefault(); setTextMode(true); }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, []);

  useEffect(() => {
    const analysisId = sessionStorage.getItem("analysis_id");
    if (!analysisId) {
      router.push("/");
      return;
    }

    const es = new EventSource(`/api/analyze/${analysisId}/stream`);
    eventSourceRef.current = es;

    timeoutRef.current = setTimeout(() => {
      setTimeoutWarning(true);
    }, 90_000);

    es.onmessage = (e) => {
      const event: SSEEvent = JSON.parse(e.data);

      if (event.type === "agent_start" && event.agent_id) {
        const agentName = event.agent_name ?? event.agent_id;
        announce(`${agentName} has started analysis.`);
        setAgents((prev) =>
          prev.map((a) =>
            a.agent_id === event.agent_id ? { ...a, status: "running" } : a
          )
        );
      }

      if (event.type === "agent_complete" && event.agent_id && event.result) {
        const result = event.result;
        announce(
          `${result.agent_name} has completed analysis with ${result.findings.length} finding${result.findings.length !== 1 ? "s" : ""}. ${result.summary}`
        );
        setAgents((prev) =>
          prev.map((a) =>
            a.agent_id === event.agent_id
              ? {
                  ...a,
                  status: result.status,
                  findings: result.findings,
                  summary: result.summary,
                  error: result.error,
                }
              : a
          )
        );
        setAllFindings((prev) => [...prev, ...result.findings]);
      }

      if (event.type === "agent_error" && event.agent_id) {
        setAgents((prev) =>
          prev.map((a) =>
            a.agent_id === event.agent_id
              ? { ...a, status: "error", error: event.error }
              : a
          )
        );
      }

      if (event.type === "analysis_complete") {
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        analysisJustCompletedRef.current = true;
        setIsComplete(true);
        setTimeoutWarning(false);
        if (event.confidence_distribution) {
          setConfidenceDist(event.confidence_distribution);
        }
        if (event.global_confidence_score != null) {
          setGlobalScore(event.global_confidence_score);
        }
        es.close();
      }

      if (event.type === "error") {
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        setConnectionError(event.error ?? "Unknown error");
        es.close();
      }
    };

    es.onerror = () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      setConnectionError("Connection to analysis service lost.");
      es.close();
    };

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (announceTimerRef.current) clearTimeout(announceTimerRef.current);
      es.close();
    };
  }, [router]);

  // Translate displayed results when the user switches language after analysis is complete
  useEffect(() => {
    if (!isComplete) return;

    // Skip the first time isComplete becomes true (results are already in the right language)
    if (analysisJustCompletedRef.current) {
      analysisJustCompletedRef.current = false;
      return;
    }

    const translate = async () => {
      setIsTranslating(true);
      try {
        const res = await fetch("/api/translate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ language: lang }),
        });
        if (!res.ok) return;
        const data: { agents: AgentState[] } = await res.json();
        setAgents((prev) =>
          prev.map((a) => {
            const translated = data.agents.find((ta) => ta.agent_id === a.agent_id);
            if (!translated) return a;
            return { ...a, findings: translated.findings, summary: translated.summary };
          })
        );
        setAllFindings(data.agents.flatMap((a) => a.findings));
        setSelectedFinding(null);
      } finally {
        setIsTranslating(false);
      }
    };

    void translate();
  }, [lang, isComplete]); // eslint-disable-line react-hooks/exhaustive-deps

  const completedCount = agents.filter((a) => a.status === "completed").length;
  const progress = Math.round((completedCount / agents.length) * 100);

  const copyExecutiveSummary = async () => {
    const reds = allFindings.filter((f) => f.confidence === "red");
    const yellows = allFindings.filter((f) => f.confidence === "yellow");
    const greens = allFindings.filter((f) => f.confidence === "green");
    const score = globalScore != null ? `${Math.round(globalScore * 100)}%` : "—";

    const lines = [
      "# Confidence Map — Executive Summary",
      "",
      `Global confidence: ${score}`,
      `Total: ${allFindings.length} findings (${reds.length} critical · ${yellows.length} inferred · ${greens.length} confirmed)`,
      "",
    ];

    if (reds.length > 0) {
      lines.push(`## Critical — High uncertainty (${reds.length})`);
      reds.forEach((f) => {
        lines.push(`- **${f.title}** [${f.agent_name}]`);
        if (f.recommended_action) lines.push(`  → ${f.recommended_action}`);
      });
      lines.push("");
    }
    if (yellows.length > 0) {
      lines.push(`## Inferred — Reasonably assumed (${yellows.length})`);
      yellows.forEach((f) => {
        lines.push(`- **${f.title}** [${f.agent_name}]`);
        if (f.recommended_action) lines.push(`  → ${f.recommended_action}`);
      });
      lines.push("");
    }
    if (greens.length > 0) {
      lines.push(`## Confirmed — Explicitly defined (${greens.length})`);
      greens.forEach((f) => lines.push(`- ${f.title} [${f.agent_name}]`));
    }

    await navigator.clipboard.writeText(lines.join("\n"));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const activeView = textMode ? "text" : showTable ? "table" : "map";

  return (
    <div className="flex flex-col h-screen bg-surface overflow-hidden">
      {/* Progressive narration — assertive so screen readers interrupt current reading */}
      <div
        aria-live="assertive"
        aria-atomic="true"
        className="sr-only"
        role="status"
      >
        {announcement}
      </div>
      {/* Top bar */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-surface-border bg-surface-card flex-shrink-0">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push("/")}
            className="text-slate-500 hover:text-slate-200 text-sm transition-colors flex items-center gap-1"
            aria-label="Back to home"
          >
            ← {t("nav.back")}
          </button>
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded bg-accent flex items-center justify-center" aria-hidden="true">
              <div className="w-2 h-2 rounded-full bg-white" />
            </div>
            <span className="text-sm font-semibold text-slate-200">Confidence Map</span>
          </div>
        </div>

        {/* Progress */}
        <div
          className="flex items-center gap-3"
          aria-label={`Analysis progress: ${completedCount} of ${agents.length} agents complete`}
          role="progressbar"
          aria-valuenow={progress}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          {!isComplete && (
            <div className="w-32 h-1.5 bg-surface-border rounded-full overflow-hidden">
              <div
                className="h-full bg-accent rounded-full transition-all duration-700"
                style={{ width: `${progress}%` }}
              />
            </div>
          )}
          {isComplete ? (
            <span className="text-xs text-confidence-green font-mono">{t("analysis.complete")}</span>
          ) : (
            <span className="text-xs text-slate-500 font-mono">
              {t("analysis.progress", { completed: completedCount, total: agents.length })}
            </span>
          )}
        </div>

        {/* Map / Table / Text toggle */}
        {allFindings.length > 0 && (
          <div
            className="flex items-center rounded-lg border border-surface-border overflow-hidden text-xs font-mono"
            role="group"
            aria-label="View mode (Alt+1 Map, Alt+2 Table, Alt+3 Text)"
          >
            {(["map", "table", "text"] as const).map((view, i) => {
              const labels = {
                map: t("analysis.view_map"),
                table: t("analysis.view_table"),
                text: t("analysis.view_text"),
              };
              const active = activeView === view;
              return (
                <button
                  key={view}
                  onClick={() => {
                    if (view === "map")   { setTextMode(false); setShowTable(false); }
                    if (view === "table") { setTextMode(false); setShowTable(true); }
                    if (view === "text")  { setTextMode(true); }
                  }}
                  className={`px-3 py-1.5 transition-colors border-l first:border-l-0 border-surface-border ${active ? "bg-accent text-white" : "text-slate-400 hover:text-slate-200"}`}
                  aria-pressed={active}
                  title={`Alt+${i + 1}`}
                >
                  {labels[view]}
                </button>
              );
            })}
          </div>
        )}

        <LanguageSwitcher />

        {/* Global confidence score + distribution */}
        {isComplete && (
          <div className="flex items-center gap-4">
            {/* Score global */}
            {globalScore != null && (
              <div
                className="flex items-center gap-2"
                aria-label={`${t("summary.global_confidence")}: ${Math.round(globalScore * 100)}%`}
              >
                <span className="text-xs text-slate-500 font-mono">{t("summary.global_confidence")}</span>
                <span
                  className={`text-lg font-bold font-mono tabular-nums ${
                    globalScore >= 0.7
                      ? "text-confidence-green"
                      : globalScore >= 0.45
                      ? "text-confidence-yellow"
                      : "text-confidence-red"
                  }`}
                >
                  {Math.round(globalScore * 100)}%
                </span>
              </div>
            )}

            {/* Separador */}
            <div className="w-px h-4 bg-surface-border" aria-hidden="true" />

            {/* Distribución */}
            <div
              className="flex gap-3 text-xs font-mono"
              aria-label={`${t("summary.confirmed")}: ${confidenceDist.green}, ${t("summary.inferred")}: ${confidenceDist.yellow}, ${t("summary.critical")}: ${confidenceDist.red}`}
            >
              {(["green", "yellow", "red"] as const).map((level) => (
                <span key={level} className={`flex items-center gap-1 text-confidence-${level}`}>
                  <span className={`w-2 h-2 rounded-full bg-confidence-${level}`} aria-hidden="true" />
                  {confidenceDist[level]}
                </span>
              ))}
            </div>
          </div>
        )}
      </header>

      {/* Main content */}
      <main
        id="main-content"
        className="relative flex flex-1 overflow-hidden"
        aria-label="Confidence map analysis"
      >
        {/* Translation overlay */}
      {isTranslating && (
        <div
          className="absolute inset-0 z-20 flex items-center justify-center bg-surface/80 backdrop-blur-sm"
          aria-live="polite"
          aria-label="Translating results..."
        >
          <div className="flex items-center gap-3 px-5 py-3 rounded-xl bg-surface-card border border-surface-border shadow-lg">
            <div className="w-4 h-4 border-2 border-accent border-t-transparent rounded-full animate-spin" aria-hidden="true" />
            <span className="text-sm text-slate-300 font-mono">{t("analysis.translating")}</span>
          </div>
        </div>
      )}

      {/* Left sidebar — agent status */}
        <aside
          className="w-64 flex-shrink-0 border-r border-surface-border bg-surface-card overflow-y-auto p-4"
          aria-label="Agent status panel"
        >
          <AgentStatusCard agents={agents} />

          {/* Summaries per agent */}
          {agents.some((a) => a.summary) && (
            <div className="mt-6">
              <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">
                {t("analysis.summaries")}
              </h2>
              <div className="space-y-3">
                {agents
                  .filter((a) => a.summary)
                  .map((agent) => (
                    <div key={agent.agent_id}>
                      <p className="text-[10px] font-semibold text-accent uppercase tracking-wide mb-1">
                        {agent.agent_name}
                      </p>
                      <p className="text-xs text-slate-400 leading-relaxed">{agent.summary}</p>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </aside>

        {/* Text mode — full-width accessible document */}
        {textMode && (
          <div
            className="flex-1 overflow-y-auto px-8 py-6 animate-fade-in"
            role="document"
            aria-label="Text view — all findings"
          >
            <div className="max-w-3xl mx-auto">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h1 className="text-lg font-bold text-slate-200">{t("text_view.title")}</h1>
                  <p className="text-xs text-slate-500 font-mono mt-1">
                    {t("text_view.shortcuts")}
                  </p>
                </div>
                {isComplete && (
                  <button
                    onClick={copyExecutiveSummary}
                    className="text-xs px-3 py-1.5 rounded-lg border border-surface-border text-slate-400 hover:text-slate-200 hover:border-slate-600 transition-all font-mono"
                    aria-label="Copy executive summary to clipboard"
                  >
                    {copied ? t("text_view.copied") : t("text_view.copy_summary")}
                  </button>
                )}
              </div>

              {agents.map((agent) => (
                <section
                  key={agent.agent_id}
                  className="mb-10 pb-8 border-b border-surface-border last:border-0"
                  aria-label={`Agent: ${agent.agent_name}`}
                >
                  <div className="flex items-center gap-3 mb-3">
                    <h2 className="text-sm font-bold text-slate-200">{agent.agent_name}</h2>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded-full uppercase ${
                        agent.status === "completed"
                          ? "bg-confidence-green-dim text-confidence-green"
                          : agent.status === "running"
                          ? "bg-accent-dim text-accent"
                          : agent.status === "error"
                          ? "bg-confidence-red-dim text-confidence-red"
                          : "bg-surface-border text-slate-500"
                      }`}
                    >
                      {agent.status}
                    </span>
                  </div>

                  {agent.summary && (
                    <p className="text-sm text-slate-400 leading-relaxed mb-4 pl-3 border-l-2 border-surface-border">
                      {agent.summary}
                    </p>
                  )}

                  {agent.findings.length > 0 ? (
                    <ul className="space-y-4" aria-label={`${agent.findings.length} findings`}>
                      {agent.findings.map((f) => (
                        <li
                          key={f.id}
                          className={`rounded-xl border p-4 ${
                            f.confidence === "red"
                              ? "border-confidence-red/30 bg-confidence-red-dim"
                              : f.confidence === "yellow"
                              ? "border-confidence-yellow/30 bg-confidence-yellow-dim"
                              : "border-confidence-green/30 bg-confidence-green-dim"
                          }`}
                        >
                          <div className="flex items-start gap-2 mb-2">
                            <span
                              className={`w-2 h-2 rounded-full flex-shrink-0 mt-1.5 ${
                                f.confidence === "red"
                                  ? "bg-confidence-red"
                                  : f.confidence === "yellow"
                                  ? "bg-confidence-yellow"
                                  : "bg-confidence-green"
                              }`}
                              aria-hidden="true"
                            />
                            <div>
                              <h3 className="text-sm font-semibold text-slate-200 leading-snug">
                                {f.title}
                              </h3>
                              <p className={`text-[10px] font-mono uppercase mt-0.5 ${
                                f.confidence === "red"
                                  ? "text-confidence-red"
                                  : f.confidence === "yellow"
                                  ? "text-confidence-yellow"
                                  : "text-confidence-green"
                              }`}>
                                {f.confidence} · {Math.round(f.confidence_score * 100)}%
                              </p>
                            </div>
                          </div>
                          <p className="text-xs text-slate-300 leading-relaxed mb-2 ml-4">
                            {f.description}
                          </p>
                          {f.recommended_action && (
                            <p className="text-xs text-slate-200 leading-relaxed ml-4 pl-3 border-l-2 border-accent/40 italic">
                              → {f.recommended_action}
                            </p>
                          )}
                          <button
                            onClick={() => { setSelectedFinding(f); setTextMode(false); }}
                            className="ml-4 mt-2 text-[10px] text-accent hover:underline font-mono"
                            aria-label={`Ver detalle completo de: ${f.title}`}
                          >
                            {t("text_view.view_detail")}
                          </button>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    agent.status === "pending" && (
                      <p className="text-xs text-slate-600 italic pl-3">{t("text_view.waiting")}</p>
                    )
                  )}
                </section>
              ))}
            </div>
          </div>
        )}

        {/* Center — Confidence Map */}
        {!textMode && <div className="flex-1 relative">
          {connectionError ? (
            <div
              className="flex flex-col items-center justify-center h-full gap-4"
              role="alert"
              aria-live="assertive"
            >
              <p className="text-confidence-red text-sm">{connectionError}</p>
              <button
                onClick={() => router.push("/")}
                className="text-accent hover:underline text-sm"
              >
                Return to home
              </button>
            </div>
          ) : showTable ? (
            <DecisionTable
              findings={allFindings}
              onSelect={setSelectedFinding}
              selectedFinding={selectedFinding}
            />
          ) : (
            <>
              {timeoutWarning && (
                <div
                  className="absolute top-3 left-1/2 -translate-x-1/2 z-10 flex items-center gap-2 px-4 py-2 rounded-lg bg-surface-card border border-confidence-yellow text-confidence-yellow text-xs font-mono shadow-lg"
                  role="status"
                  aria-live="polite"
                >
                  <span aria-hidden="true">⏳</span>
                  {t("analysis.timeout")}
                </div>
              )}
              <ConfidenceMap agents={agents} onFindingSelect={setSelectedFinding} />
            </>
          )}
        </div>}

        {/* Right sidebar — finding detail */}
        {!textMode && <aside
          className="w-72 flex-shrink-0 border-l border-surface-border bg-surface-card overflow-y-auto p-4"
          aria-label="Finding details panel"
        >
          {selectedFinding ? (
            <FindingDetail
              finding={selectedFinding}
              onClose={() => setSelectedFinding(null)}
            />
          ) : isComplete ? (
            /* Executive summary */
            <section aria-label="Executive summary" className="animate-fade-in">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-widest">
                  {t("summary.title")}
                </h2>
                <button
                  onClick={copyExecutiveSummary}
                  className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg border border-surface-border text-slate-400 hover:text-slate-200 hover:border-slate-600 transition-all"
                  aria-label="Copy executive summary to clipboard"
                >
                  {copied ? (
                    <span className="text-confidence-green text-[10px] font-mono">{t("summary.copied")}</span>
                  ) : (
                    <span className="text-[10px] font-mono">{t("summary.copy")}</span>
                  )}
                </button>
              </div>

              {/* Score + breakdown */}
              {globalScore != null && (
                <div className="bg-surface border border-surface-border rounded-xl p-4 mb-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs text-slate-500">{t("summary.global_confidence")}</span>
                    <span
                      className={`text-2xl font-bold font-mono tabular-nums ${
                        globalScore >= 0.7
                          ? "text-confidence-green"
                          : globalScore >= 0.45
                          ? "text-confidence-yellow"
                          : "text-confidence-red"
                      }`}
                    >
                      {Math.round(globalScore * 100)}%
                    </span>
                  </div>
                  <div className="flex gap-2 text-xs font-mono">
                    {(["red", "yellow", "green"] as const).map((level) => {
                      const count = allFindings.filter((f) => f.confidence === level).length;
                      const labels = {
                        red: t("summary.critical"),
                        yellow: t("summary.inferred"),
                        green: t("summary.confirmed"),
                      };
                      if (count === 0) return null;
                      return (
                        <div key={level} className={`flex-1 rounded-lg px-2 py-1.5 text-center bg-confidence-${level}-dim text-confidence-${level}`}>
                          <div className="font-bold text-base tabular-nums">{count}</div>
                          <div className="text-[9px] opacity-80">{labels[level]}</div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Top critical findings */}
              {allFindings.filter((f) => f.confidence === "red").length > 0 && (
                <div>
                  <h3 className="text-[10px] font-semibold text-confidence-red uppercase tracking-widest mb-2">
                    {t("summary.critical_findings")}
                  </h3>
                  <ul className="space-y-2">
                    {allFindings
                      .filter((f) => f.confidence === "red")
                      .slice(0, 4)
                      .map((f) => (
                        <li key={f.id}>
                          <button
                            onClick={() => setSelectedFinding(f)}
                            className="w-full text-left group"
                            aria-label={`View finding: ${f.title}`}
                          >
                            <p className="text-xs text-slate-300 group-hover:text-white transition-colors leading-snug">
                              {f.title}
                            </p>
                            <p className="text-[10px] text-slate-500 mt-0.5">{f.agent_name}</p>
                          </button>
                        </li>
                      ))}
                  </ul>
                </div>
              )}
            </section>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center gap-3 text-slate-600">
              <div className="text-4xl" aria-hidden="true">◎</div>
              <p className="text-sm">{t("analysis.no_finding")}</p>
            </div>
          )}

          {/* Findings list */}
          {allFindings.length > 0 && (
            <div className="mt-6">
              <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">
                {t("analysis.all_findings", { count: allFindings.length })}
              </h2>
              <ul
                className="space-y-2"
                role="list"
                aria-label={`${allFindings.length} findings`}
              >
                {allFindings.map((f) => (
                  <li key={f.id}>
                    <button
                      onClick={() => setSelectedFinding(f)}
                      className={`w-full text-left px-3 py-2 rounded-lg border text-xs transition-all hover:brightness-125 ${
                        selectedFinding?.id === f.id
                          ? `border-confidence-${f.confidence} bg-confidence-${f.confidence}-dim`
                          : "border-surface-border hover:border-slate-600"
                      }`}
                      aria-current={selectedFinding?.id === f.id ? "true" : undefined}
                      aria-label={`${f.title} — ${f.confidence} confidence — ${f.agent_name}`}
                    >
                      <div className="flex items-start gap-2">
                        <span
                          className={`w-2 h-2 rounded-full flex-shrink-0 mt-0.5 bg-confidence-${f.confidence}`}
                          aria-hidden="true"
                        />
                        <div>
                          <p className="text-slate-200 leading-snug">{f.title}</p>
                          <p className="text-slate-500 mt-0.5">{f.agent_name}</p>
                        </div>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </aside>}
      </main>

      <AccessibleSummary agents={agents} findings={allFindings} isComplete={isComplete} />
    </div>
  );
}
