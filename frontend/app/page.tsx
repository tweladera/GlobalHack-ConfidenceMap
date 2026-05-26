"use client";

import { useState, useRef, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { DEMO_SPEC, DEMO_ARCHITECTURE, DEMO_SPEC_AUTH, DEMO_ARCH_AUTH } from "@/lib/demo-spec";

function HomePageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [spec, setSpec] = useState("");
  const [architecture, setArchitecture] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const specRef = useRef<HTMLTextAreaElement>(null);

  // Auto-load preset from URL on mount: ?spec=pagos | ?spec=auth
  useEffect(() => {
    const preset = searchParams.get("spec");
    if (preset === "pagos") { setSpec(DEMO_SPEC); setArchitecture(DEMO_ARCHITECTURE); }
    else if (preset === "auth") { setSpec(DEMO_SPEC_AUTH); setArchitecture(DEMO_ARCH_AUTH); }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const loadPreset = (preset: "pagos" | "auth") => {
    if (preset === "pagos") {
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
      setError("Please enter a specification to analyze.");
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

      const { analysis_id } = await res.json();
      sessionStorage.setItem("analysis_id", analysis_id);
      sessionStorage.setItem("analysis_spec", spec);
      router.push("/analysis");
    } catch (e) {
      setError("Could not connect to the analysis service. Is the backend running?");
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
          AI Architecture &amp;{" "}
          <span className="text-accent">Delivery Intelligence</span>
        </h1>
        <p className="text-slate-400 text-lg max-w-2xl mx-auto">
          Paste your PRD or specification. Six specialized agents will analyze it
          simultaneously — surfacing ambiguity, risks, and blind spots with explicit confidence levels.
        </p>
      </header>

      {/* Input area */}
      <section
        className="w-full max-w-3xl bg-surface-card border border-surface-border rounded-2xl p-6 animate-slide-up"
        aria-label="Specification input"
      >
        {/* Confidence legend */}
        <div
          className="flex gap-4 mb-6 text-sm"
          role="note"
          aria-label="Confidence level legend"
        >
          {[
            { level: "green", label: "Explicitly defined" },
            { level: "yellow", label: "Reasonably inferred" },
            { level: "red", label: "High uncertainty" },
          ].map(({ level, label }) => (
            <div key={level} className="flex items-center gap-1.5">
              <span
                className={`w-2.5 h-2.5 rounded-full bg-confidence-${level}`}
                aria-hidden="true"
              />
              <span className="text-slate-400">{label}</span>
            </div>
          ))}
        </div>

        {/* Spec input */}
        <div className="mb-4">
          <label
            htmlFor="spec-input"
            className="block text-sm font-medium text-slate-300 mb-2"
          >
            Specification / PRD / User Stories{" "}
            <span className="text-confidence-red" aria-label="required">*</span>
          </label>
          <textarea
            id="spec-input"
            ref={specRef}
            value={spec}
            onChange={(e) => setSpec(e.target.value)}
            rows={14}
            placeholder="Paste your PRD, user stories, BRD, or any engineering specification here..."
            className="w-full bg-surface border border-surface-border rounded-xl px-4 py-3 text-slate-200 placeholder-slate-600 font-mono text-sm resize-none focus:border-accent focus:outline-none transition-colors"
            aria-required="true"
            aria-describedby={error ? "spec-error" : undefined}
          />
        </div>

        {/* Architecture input */}
        <div className="mb-6">
          <label
            htmlFor="arch-input"
            className="block text-sm font-medium text-slate-300 mb-2"
          >
            Architecture / ADR{" "}
            <span className="text-slate-500 font-normal">(optional)</span>
          </label>
          <textarea
            id="arch-input"
            value={architecture}
            onChange={(e) => setArchitecture(e.target.value)}
            rows={5}
            placeholder="Paste architecture description, diagrams as text, or ADRs..."
            className="w-full bg-surface border border-surface-border rounded-xl px-4 py-3 text-slate-200 placeholder-slate-600 font-mono text-sm resize-none focus:border-accent focus:outline-none transition-colors"
          />
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
                Starting analysis...
              </>
            ) : (
              <>
                <span aria-hidden="true">&#9654;</span>
                Run Analysis
              </>
            )}
          </button>

          {/* Preset selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 flex-shrink-0">Try a preset:</span>
            <div className="flex gap-2 flex-1">
              <button
                onClick={() => loadPreset("pagos")}
                className="flex-1 py-2 px-3 text-xs text-slate-400 hover:text-slate-200 border border-surface-border hover:border-accent/50 rounded-lg transition-colors text-left group"
                aria-label="Load NovaBank international payments demo specification"
              >
                <span className="text-accent font-mono mr-1.5 group-hover:text-accent">▸</span>
                NovaBank · Pagos
                <span className="ml-1.5 text-[9px] px-1.5 py-0.5 rounded bg-confidence-green-dim text-confidence-green font-mono uppercase">demo</span>
              </button>
              <button
                onClick={() => loadPreset("auth")}
                className="flex-1 py-2 px-3 text-xs text-slate-400 hover:text-slate-200 border border-surface-border hover:border-accent/50 rounded-lg transition-colors text-left group"
                aria-label="Load NovaBank MFA authentication demo specification"
              >
                <span className="text-accent font-mono mr-1.5 group-hover:text-accent">▸</span>
                NovaBank · Auth MFA
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Agents preview */}
      <section
        className="mt-10 w-full max-w-3xl"
        aria-label="Available analysis agents"
      >
        <p className="text-center text-slate-500 text-sm mb-4">
          Six specialized agents analyze your spec simultaneously
        </p>
        <ul
          className="grid grid-cols-2 md:grid-cols-3 gap-3"
          role="list"
          aria-label="Analysis agents"
        >
          {[
            { name: "Spec Analyst", desc: "Ambiguity & gaps", color: "indigo" },
            { name: "Architecture Validator", desc: "Drift & coupling", color: "violet" },
            { name: "Risk Intelligence", desc: "Security & delivery", color: "rose" },
            { name: "Business Impact", desc: "Cost & velocity", color: "amber" },
            { name: "Accessibility Advocate", desc: "WCAG & inclusion", color: "emerald" },
            { name: "Delivery Historian", desc: "Patterns & pitfalls", color: "sky" },
          ].map((agent) => (
            <li
              key={agent.name}
              className="bg-surface-card border border-surface-border rounded-xl p-4"
            >
              <div className="font-medium text-sm text-slate-200">{agent.name}</div>
              <div className="text-xs text-slate-500 mt-0.5">{agent.desc}</div>
            </li>
          ))}
        </ul>
      </section>
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
