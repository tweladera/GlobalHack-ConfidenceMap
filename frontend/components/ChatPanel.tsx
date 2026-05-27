"use client";

import { useEffect, useRef, useState } from "react";
import type { AgentState, Finding } from "@/types";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ChatPayload {
  text?: string;
  type?: string;
  message?: string;
}

interface Props {
  findings: Finding[];
  agents: AgentState[];
  globalScore: number | null;
  onClose: () => void;
}

const SUGGESTIONS = [
  "What are the most critical risks to address first?",
  "How should we prioritize these findings?",
  "What should be resolved before implementation starts?",
];

export default function ChatPanel({ findings, agents, globalScore, onClose }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    const question = input.trim();
    if (!question || isStreaming) return;

    const history: Message[] = [...messages];
    setMessages([...history, { role: "user", content: question }]);
    setInput("");
    setIsStreaming(true);
    // Placeholder assistant message
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    try {
      const res = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          findings: findings.map((f) => ({
            title: f.title,
            description: f.description,
            confidence: f.confidence,
            confidence_score: f.confidence_score,
            category: f.category,
            agent_name: f.agent_name,
            recommended_action: f.recommended_action,
          })),
          agents: agents.map((a) => ({ agent_name: a.agent_name, summary: a.summary })),
          global_score: globalScore,
          history: history.map((m) => ({ role: m.role, content: m.content })),
        }),
      });

      if (!res.ok || !res.body) throw new Error("Failed to connect");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const payload = JSON.parse(line.slice(6)) as ChatPayload;
          if (payload.type === "complete") break;
          if (payload.type === "error") {
            setMessages((prev) => {
              const updated = [...prev];
              updated[updated.length - 1] = {
                role: "assistant",
                content: `Error: ${payload.message ?? "Unknown error"}`,
              };
              return updated;
            });
            break;
          }
          if (payload.text) {
            setMessages((prev) => {
              const updated = [...prev];
              updated[updated.length - 1] = {
                role: "assistant",
                content: updated[updated.length - 1].content + payload.text,
              };
              return updated;
            });
          }
        }
      }
    } catch {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: "Connection error. Please check that the backend is running.",
        };
        return updated;
      });
    } finally {
      setIsStreaming(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void send();
    }
  };

  return (
    <div
      className="flex flex-col h-full animate-fade-in"
      role="complementary"
      aria-label="Chat with AI about this analysis"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-surface-border flex-shrink-0">
        <div>
          <h2 className="text-sm font-semibold text-slate-200">Ask AI</h2>
          <p className="text-xs text-slate-500 font-mono">{findings.length} findings in context</p>
        </div>
        <button
          onClick={onClose}
          className="text-slate-500 hover:text-slate-200 transition-colors"
          aria-label="Close chat panel"
        >
          ✕
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-8 space-y-3">
            <div className="text-3xl text-slate-600" aria-hidden="true">◎</div>
            <p className="text-sm text-slate-500">Ask anything about the analysis findings.</p>
            <div className="space-y-2 mt-4">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => {
                    setInput(s);
                    inputRef.current?.focus();
                  }}
                  className="block w-full text-left text-xs px-3 py-2 rounded-lg border border-surface-border text-slate-400 hover:text-slate-200 hover:border-slate-600 transition-colors font-mono"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[85%] rounded-xl px-3 py-2 text-xs leading-relaxed ${
                m.role === "user"
                  ? "bg-accent text-white"
                  : "bg-surface border border-surface-border text-slate-300"
              }`}
            >
              {m.role === "assistant" && m.content === "" && isStreaming ? (
                <span className="flex gap-1 items-center py-0.5">
                  <span
                    className="w-1.5 h-1.5 rounded-full bg-slate-500 animate-bounce"
                    style={{ animationDelay: "0ms" }}
                  />
                  <span
                    className="w-1.5 h-1.5 rounded-full bg-slate-500 animate-bounce"
                    style={{ animationDelay: "150ms" }}
                  />
                  <span
                    className="w-1.5 h-1.5 rounded-full bg-slate-500 animate-bounce"
                    style={{ animationDelay: "300ms" }}
                  />
                </span>
              ) : (
                <span className="whitespace-pre-wrap">{m.content}</span>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-3 border-t border-surface-border flex-shrink-0">
        <div className="flex gap-2 items-end">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about the findings… (Enter to send)"
            rows={2}
            className="flex-1 bg-surface border border-surface-border rounded-xl px-3 py-2 text-xs text-slate-200 placeholder-slate-600 font-mono resize-none focus:border-accent focus:outline-none transition-colors"
            aria-label="Chat message input"
            disabled={isStreaming}
          />
          <button
            onClick={() => void send()}
            disabled={!input.trim() || isStreaming}
            className="px-3 py-2 rounded-xl bg-accent text-white text-xs font-mono disabled:opacity-40 disabled:cursor-not-allowed hover:bg-indigo-500 transition-colors flex-shrink-0"
            aria-label="Send message"
          >
            {isStreaming ? "…" : "Send"}
          </button>
        </div>
        <p className="text-[9px] text-slate-600 font-mono mt-1.5">Shift+Enter for new line</p>
      </div>
    </div>
  );
}
