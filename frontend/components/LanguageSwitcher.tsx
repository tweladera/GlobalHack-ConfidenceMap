"use client";

import { useI18n, type Lang } from "@/lib/i18n";

const LANGS: { code: Lang; label: string }[] = [
  { code: "en", label: "EN" },
  { code: "es", label: "ES" },
  { code: "pt", label: "PT" },
];

export default function LanguageSwitcher() {
  const { lang, setLang } = useI18n();

  return (
    <div
      className="flex items-center rounded-lg border border-surface-border overflow-hidden text-xs font-mono"
      role="group"
      aria-label="Language selector"
    >
      {LANGS.map(({ code, label }) => (
        <button
          key={code}
          onClick={() => setLang(code)}
          className={`px-2.5 py-1 transition-colors border-l first:border-l-0 border-surface-border ${
            lang === code ? "bg-accent text-white" : "text-slate-400 hover:text-slate-200"
          }`}
          aria-pressed={lang === code}
          aria-label={`Switch language to ${label}`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
