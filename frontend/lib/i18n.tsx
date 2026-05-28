"use client";

import { createContext, useContext, type ReactNode } from "react";
import en from "@/messages/en.json";

type Messages = typeof en;
export type MessageKey = keyof Messages;

interface I18nContextType {
  t: (key: MessageKey, vars?: Record<string, string | number>) => string;
}

const I18nContext = createContext<I18nContextType | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const t = (key: MessageKey, vars?: Record<string, string | number>): string => {
    let str = en[key] as string;
    if (vars) {
      for (const [k, v] of Object.entries(vars)) {
        str = str.replace(`{${k}}`, String(v));
      }
    }
    return str;
  };

  return <I18nContext.Provider value={{ t }}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextType {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}
