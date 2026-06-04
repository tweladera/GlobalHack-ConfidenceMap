export interface AnalysisConfig {
  defaultView: "map" | "table" | "text" | "heat";
  autoHideRedundant: boolean;
  enabledAgents: string[]; // empty = all agents enabled
}

const CONFIG_KEY = "cm_config";

export const DEFAULT_CONFIG: AnalysisConfig = {
  defaultView: "map",
  autoHideRedundant: false,
  enabledAgents: [],
};

export function getConfig(): AnalysisConfig {
  if (typeof window === "undefined") return DEFAULT_CONFIG;
  try {
    const raw = localStorage.getItem(CONFIG_KEY);
    if (!raw) return DEFAULT_CONFIG;
    return { ...DEFAULT_CONFIG, ...JSON.parse(raw) };
  } catch {
    return DEFAULT_CONFIG;
  }
}

export function saveConfig(config: AnalysisConfig): void {
  localStorage.setItem(CONFIG_KEY, JSON.stringify(config));
}
