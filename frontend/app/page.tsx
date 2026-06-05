"use client";

import { useState, useRef, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { DEMO_SPEC, DEMO_ARCHITECTURE, DEMO_SPEC_AUTH, DEMO_ARCH_AUTH } from "@/lib/demo-spec";
import { useI18n } from "@/lib/i18n";
import { getHistory, clearHistory } from "@/lib/history";
import type { AnalysisRecord } from "@/lib/history";
import { getConfig, saveConfig, DEFAULT_CONFIG } from "@/lib/config";
import type { AnalysisConfig } from "@/lib/config";
import { AGENT_DEFINITIONS } from "@/types";

// ── Static preview data ──────────────────────────────────────────────────────

const PREVIEW_AGENTS = [
  { name: "Spec Analyst",          rank: 1, g: 2, y: 1, r: 1 },
  { name: "Arch Validator",        rank: 2, g: 1, y: 2, r: 2 },
  { name: "Risk Intelligence",     rank: 3, g: 0, y: 2, r: 3 },
  { name: "Business Impact",       rank: 4, g: 2, y: 2, r: 0 },
  { name: "Accessibility",         rank: 5, g: 1, y: 1, r: 1 },
  { name: "Delivery Historian",    rank: 6, g: 2, y: 1, r: 0 },
] as const;

type PreviewLevel = "green" | "yellow" | "red";

const PREVIEW_FINDINGS: { title: string; score: number; level: PreviewLevel }[] = [
  { title: "No SLA documented for CoreBanking calls",          score: 28, level: "red"    },
  { title: "Transaction idempotency mechanism absent",          score: 32, level: "red"    },
  { title: "FraudShield latency may breach 10 s SLA",          score: 44, level: "yellow" },
  { title: "SendGrid called directly — no retry on failure",    score: 55, level: "yellow" },
  { title: "PCI-DSS Level 1 explicitly required in spec",       score: 84, level: "green"  },
];

const PREVIEW_BADGE = {
  green:  "bg-confidence-green-dim  text-confidence-green",
  yellow: "bg-confidence-yellow-dim text-confidence-yellow",
  red:    "bg-confidence-red-dim    text-confidence-red",
} as const;

const PREVIEW_TEXT = {
  green: "text-confidence-green", yellow: "text-confidence-yellow", red: "text-confidence-red",
} as const;

// ── Page component ────────────────────────────────────────────────────────────

function HomePageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { t } = useI18n();
  const [spec, setSpec] = useState("");
  const [architecture, setArchitecture] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState<AnalysisRecord[]>([]);
  const [activePane, setActivePane] = useState<"spec" | "arch">("spec");
  const [showConfig, setShowConfig] = useState(false);
  const [config, setConfig] = useState<AnalysisConfig>(DEFAULT_CONFIG);
  const specRef = useRef<HTMLTextAreaElement>(null);

  const specLines = spec ? spec.split("\n").length : 0;
  const archLines = architecture ? architecture.split("\n").length : 0;
  const fmt = (n: number) => (n >= 1000 ? `${(n / 1000).toFixed(1)}k` : `${n}`);
  const specStats = spec ? `${specLines} lines · ${fmt(spec.length)} chars` : "empty";
  const archStats = architecture ? `${archLines} lines · ${fmt(architecture.length)} chars` : "empty";

  useEffect(() => {
    setHistory(getHistory());
    setConfig(getConfig());
  }, []);

  // Auto-load preset from URL on mount: ?spec=payments | ?spec=auth
  useEffect(() => {
    const preset = searchParams.get("spec");
    if (preset === "payments") { setSpec(DEMO_SPEC); setArchitecture(DEMO_ARCHITECTURE); }
    else if (preset === "auth") { setSpec(DEMO_SPEC_AUTH); setArchitecture(DEMO_ARCH_AUTH); }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const updateConfig = (patch: Partial<AnalysisConfig>) => {
    setConfig((prev) => {
      const next = { ...prev, ...patch };
      saveConfig(next);
      return next;
    });
  };

  const loadPreset = (preset: "payments" | "auth") => {
    if (preset === "payments") {
      setSpec(DEMO_SPEC);
      setArchitecture(DEMO_ARCHITECTURE);
    } else {
      setSpec(DEMO_SPEC_AUTH);
      setArchitecture(DEMO_ARCH_AUTH);
    }
    setError("");
    router.replace(`?spec=${preset}`, { scroll: false });
    specRef.current?.focus();
  };

  const handleAnalyze = async () => {
    if (!spec.trim()) {
      setError(t("home.error_empty"));
      specRef.current?.focus();
      return;
    }
    setError("");
    setIsLoading(true);

    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ spec, architecture }),
      });

      if (!res.ok) throw new Error("Failed to start analysis");

      const { analysis_id, demo_mode } = await res.json();
      sessionStorage.setItem("analysis_id", analysis_id);
      sessionStorage.setItem("analysis_spec", spec);
      sessionStorage.setItem("demo_mode", demo_mode ? "true" : "false");
      router.push("/analysis");
    } catch (e) {
      setError(t("home.error_connect"));
      setIsLoading(false);
    }
  };

  return (
    <main
      id="main-content"
      className="min-h-screen flex flex-col items-center justify-center px-4 py-16"
    >
      {/* Header */}
      <header className="text-center mb-12 animate-fade-in">
        <div className="flex items-center justify-center gap-2 mb-4">
          <div
            className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center"
            aria-hidden="true"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="3" fill="white" />
              <circle cx="12" cy="12" r="8" stroke="white" strokeWidth="1.5" strokeDasharray="3 2" />
              <circle cx="12" cy="12" r="11" stroke="white" strokeOpacity="0.4" strokeWidth="1" />
            </svg>
          </div>
          <span className="text-sm font-mono text-slate-400 uppercase tracking-widest">
            Confidence Map
          </span>
        </div>

        <h1 className="text-4xl md:text-5xl font-bold text-white mb-4 leading-tight">
          {t("home.title")}
        </h1>
        <p className="text-slate-400 text-lg max-w-2xl mx-auto">
          {t("home.subtitle")}
        </p>
      </header>

      {/* Input area */}
      <section
        className="w-full max-w-5xl bg-surface-card border border-surface-border rounded-2xl p-6 animate-slide-up"
        aria-label="Specification input"
      >
        {/* Top bar: legend + mobile pane tabs */}
        <div className="flex items-center justify-between mb-4">
          <div
            className="flex gap-4 text-xs"
            role="note"
            aria-label="Confidence level legend"
          >
            {([
              { level: "green", key: "legend.green" },
              { level: "yellow", key: "legend.yellow" },
              { level: "red", key: "legend.red" },
            ] as const).map(({ level, key }) => (
              <div key={level} className="flex items-center gap-1.5">
                <span className={`w-2 h-2 rounded-full bg-confidence-${level}`} aria-hidden="true" />
                <span className="text-slate-400">{t(key)}</span>
              </div>
            ))}
          </div>

          {/* Mobile-only tabs */}
          <div className="flex md:hidden gap-1">
            {(["spec", "arch"] as const).map((pane) => (
              <button
                key={pane}
                onClick={() => setActivePane(pane)}
                className={`text-xs px-3 py-1 rounded-lg font-mono transition-colors ${
                  activePane === pane
                    ? "bg-accent text-white"
                    : "text-slate-500 hover:text-slate-300"
                }`}
              >
                {pane === "spec" ? "PRD" : "Architecture"}
              </button>
            ))}
          </div>
        </div>

        {/* Split editor */}
        <div className="flex flex-col md:flex-row gap-3 mb-6">
          {/* ── Spec pane ── */}
          <div className={`flex-1 flex flex-col ${activePane !== "spec" ? "hidden md:flex" : "flex"}`}>
            <div className="flex items-center justify-between px-3 py-2 bg-surface rounded-t-xl border border-surface-border border-b-0">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-300">{t("home.spec_label")}</span>
                <span className="text-confidence-red text-xs font-bold" aria-label="required">*</span>
              </div>
              <span className="text-[10px] font-mono text-slate-600" aria-live="polite">{specStats}</span>
            </div>
            <textarea
              id="spec-input"
              ref={specRef}
              value={spec}
              onChange={(e) => setSpec(e.target.value)}
              placeholder={t("home.spec_placeholder")}
              className="h-72 bg-surface border border-surface-border rounded-b-xl px-4 py-3 text-slate-200 placeholder-slate-600 font-mono text-sm resize-none focus:border-accent focus:outline-none transition-colors"
              aria-required="true"
              aria-describedby={error ? "spec-error" : undefined}
            />
          </div>

          {/* ── Architecture pane ── */}
          <div className={`flex-1 flex flex-col ${activePane !== "arch" ? "hidden md:flex" : "flex"}`}>
            <div className="flex items-center justify-between px-3 py-2 bg-surface rounded-t-xl border border-surface-border border-b-0">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-300">{t("home.arch_label")}</span>
                <span className="text-[10px] text-slate-500 font-normal">{t("home.arch_optional")}</span>
              </div>
              <span className="text-[10px] font-mono text-slate-600" aria-live="polite">{archStats}</span>
            </div>
            <textarea
              id="arch-input"
              value={architecture}
              onChange={(e) => setArchitecture(e.target.value)}
              placeholder={t("home.arch_placeholder")}
              className="h-72 bg-surface border border-surface-border rounded-b-xl px-4 py-3 text-slate-200 placeholder-slate-600 font-mono text-sm resize-none focus:border-accent focus:outline-none transition-colors"
            />
          </div>
        </div>

        {error && (
          <p
            id="spec-error"
            role="alert"
            className="text-confidence-red text-sm mb-4 flex items-center gap-2"
          >
            <span aria-hidden="true">⚠</span> {error}
          </p>
        )}

        {/* Actions */}
        <div className="space-y-3">
          <button
            onClick={handleAnalyze}
            disabled={isLoading}
            className="w-full bg-accent hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 rounded-xl transition-colors flex items-center justify-center gap-2"
            aria-busy={isLoading}
            aria-label={isLoading ? "Analysis in progress..." : "Start confidence map analysis"}
          >
            {isLoading ? (
              <>
                <span
                  className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"
                  aria-hidden="true"
                />
                {t("home.running")}
              </>
            ) : (
              <>
                <span aria-hidden="true">&#9654;</span>
                {t("home.run")}
              </>
            )}
          </button>

          {/* Preset selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 flex-shrink-0">{t("home.preset_label")}</span>
            <div className="flex gap-2 flex-1">
              <button
                onClick={() => loadPreset("payments")}
                className="flex-1 py-2 px-3 text-xs text-slate-400 hover:text-slate-200 border border-surface-border hover:border-accent/50 rounded-lg transition-colors text-left group"
                aria-label="Load NovaBank international payments demo specification"
              >
                <span className="text-accent font-mono mr-1.5 group-hover:text-accent">▸</span>
                {t("home.preset_payments")}
                <span className="ml-1.5 text-[9px] px-1.5 py-0.5 rounded bg-confidence-green-dim text-confidence-green font-mono uppercase">demo</span>
              </button>
              <button
                onClick={() => loadPreset("auth")}
                className="flex-1 py-2 px-3 text-xs text-slate-400 hover:text-slate-200 border border-surface-border hover:border-accent/50 rounded-lg transition-colors text-left group"
                aria-label="Load NovaBank MFA authentication demo specification"
              >
                <span className="text-accent font-mono mr-1.5 group-hover:text-accent">▸</span>
                {t("home.preset_auth")}
              </button>
            </div>
          </div>

          {/* Settings toggle */}
          <div>
            <button
              onClick={() => setShowConfig((v) => !v)}
              className="flex items-center gap-1.5 text-[11px] font-mono text-slate-600 hover:text-slate-400 transition-colors"
              aria-expanded={showConfig}
              aria-controls="config-panel"
            >
              <span aria-hidden="true">{showConfig ? "▾" : "▸"}</span>
              Analysis settings
            </button>

            {showConfig && (
              <div
                id="config-panel"
                className="mt-3 p-4 bg-surface border border-surface-border rounded-xl space-y-4 animate-fade-in"
              >
                {/* Default view */}
                <div>
                  <p className="text-[10px] font-mono text-slate-500 uppercase tracking-widest mb-2">
                    Default view
                  </p>
                  <div className="flex gap-1.5">
                    {(["map", "table", "text", "heat"] as const).map((v) => (
                      <button
                        key={v}
                        onClick={() => updateConfig({ defaultView: v })}
                        className={`text-xs px-3 py-1 rounded-lg font-mono capitalize transition-colors ${
                          config.defaultView === v
                            ? "bg-accent text-white"
                            : "border border-surface-border text-slate-500 hover:text-slate-300"
                        }`}
                      >
                        {v}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Options */}
                <div>
                  <p className="text-[10px] font-mono text-slate-500 uppercase tracking-widest mb-2">
                    Options
                  </p>
                  <label className="flex items-center gap-2 cursor-pointer group">
                    <input
                      type="checkbox"
                      checked={config.autoHideRedundant}
                      onChange={(e) => updateConfig({ autoHideRedundant: e.target.checked })}
                      className="w-3.5 h-3.5 accent-indigo-500"
                    />
                    <span className="text-xs text-slate-500 group-hover:text-slate-300 transition-colors">
                      Auto-hide redundant findings
                    </span>
                  </label>
                </div>

                {/* Agent selection */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">
                      Agents
                    </p>
                    <button
                      onClick={() => updateConfig({ enabledAgents: [] })}
                      className="text-[10px] font-mono text-slate-600 hover:text-slate-400 transition-colors"
                    >
                      reset all
                    </button>
                  </div>
                  <div className="grid grid-cols-2 gap-y-1.5 gap-x-4">
                    {AGENT_DEFINITIONS.map((agent) => {
                      const isEnabled =
                        config.enabledAgents.length === 0 ||
                        config.enabledAgents.includes(agent.agent_id);
                      return (
                        <label
                          key={agent.agent_id}
                          className="flex items-center gap-2 cursor-pointer group"
                        >
                          <input
                            type="checkbox"
                            checked={isEnabled}
                            onChange={(e) => {
                              const allIds = AGENT_DEFINITIONS.map((a) => a.agent_id);
                              // Start from full list if currently "all enabled"
                              const current =
                                config.enabledAgents.length === 0 ? allIds : config.enabledAgents;
                              const next = e.target.checked
                                ? [...current, agent.agent_id]
                                : current.filter((id) => id !== agent.agent_id);
                              // If all are checked, collapse back to [] (all-enabled shorthand)
                              updateConfig({
                                enabledAgents: next.length === allIds.length ? [] : next,
                              });
                            }}
                            className="w-3.5 h-3.5 accent-indigo-500"
                          />
                          <span className="text-xs text-slate-500 group-hover:text-slate-300 transition-colors truncate">
                            {agent.agent_name}
                          </span>
                        </label>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Agents preview / Output preview */}
      <section className="mt-10 w-full max-w-5xl" aria-label="Analysis preview">
        <p className="text-center text-slate-500 text-sm mb-4">
          {spec || architecture ? t("home.agents_subtitle") : "Preview of your analysis output"}
        </p>

        {spec || architecture ? (
          /* Agents grid — shown once the user has started filling in content */
          <ul
            className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3"
            role="list"
            aria-label="Analysis agents"
          >
            {([
              { name: "Spec Analyst",           descKey: "agent.spec_analyst_desc"   },
              { name: "Architecture Validator",  descKey: "agent.arch_validator_desc" },
              { name: "Risk Intelligence",       descKey: "agent.risk_intel_desc"     },
              { name: "Business Impact",         descKey: "agent.biz_impact_desc"     },
              { name: "Accessibility Advocate",  descKey: "agent.access_advocate_desc"},
              { name: "Delivery Historian",      descKey: "agent.delivery_hist_desc"  },
            ] as const).map((agent) => (
              <li key={agent.name} className="bg-surface-card border border-surface-border rounded-xl p-4">
                <div className="font-medium text-sm text-slate-200">{agent.name}</div>
                <div className="text-xs text-slate-500 mt-0.5">{t(agent.descKey)}</div>
              </li>
            ))}
          </ul>
        ) : (
          /* Empty-state visual preview — illustrates what the analysis produces */
          <div className="animate-fade-in" aria-hidden="true">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

              {/* Left — agent timeline */}
              <div className="bg-surface-card border border-surface-border rounded-2xl p-5">
                <div className="text-[10px] font-mono text-slate-600 uppercase tracking-widest mb-4">
                  Agent Timeline
                </div>
                {/* Progress bar */}
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-mono text-slate-600">6/6 complete</span>
                  <span className="text-[10px] font-mono text-confidence-green">✓ done</span>
                </div>
                <div className="h-1 bg-surface-border rounded-full overflow-hidden mb-4">
                  <div className="h-full w-full bg-accent rounded-full" />
                </div>
                {/* Timeline entries */}
                <ul className="relative space-y-0">
                  <div className="absolute left-[7px] top-2 bottom-2 w-px bg-surface-border" />
                  {PREVIEW_AGENTS.map((a) => (
                    <li key={a.name} className="relative pl-6 pb-3 last:pb-0">
                      <div className="absolute left-0 top-1 w-3.5 h-3.5 rounded-full border-2 bg-confidence-green border-confidence-green" />
                      <div className="flex items-start justify-between gap-1">
                        <span className="text-xs text-slate-400 leading-snug">{a.name}</span>
                        <span className="text-[9px] font-mono text-slate-600 flex-shrink-0">#{a.rank}</span>
                      </div>
                      <div className="flex gap-1 mt-1">
                        {a.g > 0 && <span className={`text-[9px] px-1.5 py-0.5 rounded font-mono ${PREVIEW_BADGE.green}`}>{a.g}✓</span>}
                        {a.y > 0 && <span className={`text-[9px] px-1.5 py-0.5 rounded font-mono ${PREVIEW_BADGE.yellow}`}>{a.y}~</span>}
                        {a.r > 0 && <span className={`text-[9px] px-1.5 py-0.5 rounded font-mono ${PREVIEW_BADGE.red}`}>{a.r}!</span>}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Right — sample findings */}
              <div className="bg-surface-card border border-surface-border rounded-2xl p-5">
                <div className="text-[10px] font-mono text-slate-600 uppercase tracking-widest mb-4">
                  Findings · 18 total
                </div>
                <ul className="space-y-2">
                  {PREVIEW_FINDINGS.map((f) => (
                    <li
                      key={f.title}
                      className={`relative px-3 py-2.5 rounded-lg border pl-4 overflow-hidden ${
                        f.level === "red" ? "border-2 border-confidence-red" : `border border-confidence-${f.level}`
                      }`}
                    >
                      {/* Accent strip */}
                      <div
                        className={`absolute left-0 top-0 bottom-0 bg-confidence-${f.level} ${f.level === "red" ? "w-1.5" : "w-1"}`}
                      />
                      <p className="text-xs text-slate-300 font-medium leading-snug line-clamp-1">{f.title}</p>
                      <div className="mt-1.5 flex items-center gap-1.5">
                        <div className="flex-1 h-1.5 bg-surface-border rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full bg-confidence-${f.level}`}
                            style={{ width: `${f.score}%` }}
                          />
                        </div>
                        <span className={`text-xs font-bold font-mono tabular-nums ${PREVIEW_TEXT[f.level]}`}>
                          {f.score}%
                        </span>
                      </div>
                    </li>
                  ))}
                </ul>

                {/* Global score footer */}
                <div className="mt-4 pt-3 border-t border-surface-border flex items-center justify-between">
                  <span className="text-[10px] font-mono text-slate-600">Global confidence</span>
                  <span className="text-sm font-bold font-mono text-confidence-yellow">72%</span>
                </div>
              </div>
            </div>

            {/* Fade overlay — signals this is a preview */}
            <div className="mt-3 flex items-center gap-3 opacity-50">
              <div className="h-px flex-1 bg-surface-border" />
              <span className="text-[10px] font-mono text-slate-600 uppercase tracking-widest">
                sample output · paste your spec above to begin
              </span>
              <div className="h-px flex-1 bg-surface-border" />
            </div>
          </div>
        )}
      </section>
      {/* History */}
      {history.length > 0 && (
        <section className="mt-8 w-full max-w-5xl" aria-label="Recent analyses">
          <div className="flex items-center justify-between mb-3">
            <p className="text-slate-500 text-sm">Recent analyses</p>
            <button
              onClick={() => { clearHistory(); setHistory([]); }}
              className="text-xs text-slate-600 hover:text-slate-400 transition-colors font-mono"
            >
              Clear history
            </button>
          </div>
          <ul className="space-y-2" role="list">
            {history.map((record) => (
              <li key={record.id}>
                <button
                  onClick={() => {
                    sessionStorage.setItem("analysis_spec", record.specPreview);
                    setSpec(record.specPreview);
                    specRef.current?.focus();
                  }}
                  className="w-full text-left bg-surface-card border border-surface-border rounded-xl px-4 py-3 hover:border-slate-600 transition-colors group"
                >
                  <div className="flex items-center justify-between gap-4">
                    <p className="text-xs text-slate-400 font-mono truncate flex-1 group-hover:text-slate-200 transition-colors">
                      {record.specPreview || "—"}
                    </p>
                    <div className="flex items-center gap-3 flex-shrink-0">
                      {record.globalScore != null && (
                        <span
                          className={`text-xs font-mono font-bold tabular-nums ${
                            record.globalScore >= 0.7
                              ? "text-confidence-green"
                              : record.globalScore >= 0.45
                              ? "text-confidence-yellow"
                              : "text-confidence-red"
                          }`}
                        >
                          {Math.round(record.globalScore * 100)}%
                        </span>
                      )}
                      <span className="flex gap-1.5 text-[10px] font-mono">
                        <span className="text-confidence-red">{record.confidenceDist.red}↑</span>
                        <span className="text-confidence-yellow">{record.confidenceDist.yellow}~</span>
                        <span className="text-confidence-green">{record.confidenceDist.green}✓</span>
                      </span>
                      <span className="text-[10px] text-slate-600 font-mono">
                        {new Date(record.timestamp).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}

export default function HomePage() {
  return (
    <Suspense>
      <HomePageContent />
    </Suspense>
  );
}
