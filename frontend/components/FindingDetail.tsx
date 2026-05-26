"use client";

import type { Finding } from "@/types";
import { CONFIDENCE_COLORS, CONFIDENCE_LABELS } from "@/types";

interface FindingDetailProps {
  finding: Finding;
  onClose: () => void;
}

export default function FindingDetail({ finding, onClose }: FindingDetailProps) {
  const colors = CONFIDENCE_COLORS[finding.confidence];
  const score = Math.round(finding.confidence_score * 100);

  return (
    <section
      className="bg-surface-card border border-surface-border rounded-xl overflow-hidden animate-slide-up"
      aria-label={`Finding details: ${finding.title}`}
      role="dialog"
      aria-modal="false"
    >
      {/* Header */}
      <div className={`px-4 py-3 border-b ${colors.border} ${colors.bg}`}>
        <div className="flex items-start justify-between gap-2">
          <div>
            <span
              className={`inline-block text-[10px] font-mono uppercase px-2 py-0.5 rounded mb-1 ${colors.badge}`}
              aria-label={`Confidence level: ${CONFIDENCE_LABELS[finding.confidence]}`}
            >
              {CONFIDENCE_LABELS[finding.confidence]}
            </span>
            <h3 className="text-sm font-semibold text-slate-100 leading-snug">
              {finding.title}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-500 hover:text-slate-200 text-lg leading-none flex-shrink-0 mt-1"
            aria-label="Close finding details"
          >
            ×
          </button>
        </div>

        <div className="mt-2 flex items-center gap-3">
          <div
            className="flex-1 h-1.5 bg-surface-border rounded-full overflow-hidden"
            role="progressbar"
            aria-valuenow={score}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`Confidence score: ${score}%`}
          >
            <div
              className={`h-full rounded-full bg-confidence-${finding.confidence}`}
              style={{ width: `${score}%` }}
            />
          </div>
          <span className={`text-xs font-mono ${colors.text}`}>{score}%</span>
        </div>
      </div>

      {/* Body */}
      <div className="px-4 py-3 space-y-3 text-sm max-h-80 overflow-y-auto">
        {/* Description */}
        <div>
          <p className="text-slate-300 leading-relaxed">{finding.description}</p>
        </div>

        {/* Evidence */}
        {finding.evidence && (
          <div>
            <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
              Evidence
            </h4>
            <blockquote className="border-l-2 border-surface-border pl-3 text-slate-400 italic text-xs leading-relaxed">
              {finding.evidence}
            </blockquote>
          </div>
        )}

        {/* Assumptions */}
        {finding.assumptions.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
              Assumptions
            </h4>
            <ul className="space-y-1" aria-label="Assumptions made">
              {finding.assumptions.map((a, i) => (
                <li key={i} className="text-xs text-slate-400 flex items-start gap-2">
                  <span className="text-confidence-yellow mt-0.5" aria-hidden="true">~</span>
                  {a}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Needs validation */}
        {finding.needs_validation.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
              Needs validation
            </h4>
            <ul className="space-y-1" aria-label="Items needing validation">
              {finding.needs_validation.map((v, i) => (
                <li key={i} className="text-xs text-slate-400 flex items-start gap-2">
                  <span className="text-confidence-red mt-0.5" aria-hidden="true">?</span>
                  {v}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Recommended action */}
        {finding.recommended_action && (
          <div>
            <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
              Qué hacer
            </h4>
            <p className="text-xs text-slate-200 leading-relaxed bg-accent-dim border border-accent/30 rounded-lg px-3 py-2">
              {finding.recommended_action}
            </p>
          </div>
        )}

        {/* Agent + category */}
        <div className="flex gap-2 pt-1 border-t border-surface-border">
          <span className="text-[10px] px-2 py-0.5 rounded bg-accent-dim text-accent font-mono">
            {finding.agent_name}
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded bg-surface-border text-slate-400 font-mono">
            {finding.category}
          </span>
        </div>
      </div>
    </section>
  );
}
