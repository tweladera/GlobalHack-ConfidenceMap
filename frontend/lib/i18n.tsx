"use client";

import { createContext, useContext, useState, type ReactNode } from "react";
import en from "@/messages/en.json";
import es from "@/messages/es.json";
import ptBr from "@/messages/pt-br.json";

export type Lang = "en" | "es" | "pt";

type Messages = typeof en;
export type MessageKey = keyof Messages;

const MESSAGES: Record<Lang, Messages> = { en, es, pt: ptBr };

interface I18nContextType {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: MessageKey, vars?: Record<string, string | number>) => string;
}

const I18nContext = createContext<I18nContextType | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>("en");

  const t = (key: MessageKey, vars?: Record<string, string | number>): string => {
    let str = MESSAGES[lang][key] as string;
    if (vars) {
      for (const [k, v] of Object.entries(vars)) {
        str = str.replace(`{${k}}`, String(v));
      }
    }
    return str;
  };

  return <I18nContext.Provider value={{ lang, setLang, t }}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextType {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}
