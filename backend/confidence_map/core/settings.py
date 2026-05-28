"""Application settings loaded from environment variables.

Priority order (highest → lowest):
  1. Environment variables  (export ANTHROPIC_API_KEY=sk-ant-...)
  2. .env file              (ANTHROPIC_API_KEY=sk-ant-...)
  3. Default values

Quick reference:
  DEMO_MODE=true   → runs without API key (mock data, free)
  DEMO_MODE=false  → calls Claude API (ANTHROPIC_API_KEY required)
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Demo mode ────────────────────────────────────────────────────────────
    # true  = pre-generated mock results, no API key needed (safe for dev/demo)
    # false = real Claude API calls (ANTHROPIC_API_KEY required)
    demo_mode: bool = False

    # ── Extended thinking ─────────────────────────────────────────────────────
    # When true, each agent call uses Claude's extended thinking feature, which
    # shows the model's chain-of-thought before producing findings.
    # This increases latency and cost (budget_tokens billed as output tokens).
    # Requires demo_mode=false and a model that supports extended thinking.
    enable_thinking: bool = False
    thinking_budget_tokens: int = 5000  # tokens allocated for reasoning per agent

    # ── Anthropic ─────────────────────────────────────────────────────────────
    # Required only when demo_mode=false.
    # Get your key at: https://console.anthropic.com
    anthropic_api_key: str = ""

    # claude-haiku-4-5-20251001  → faster and cheaper (good for development)
    # claude-sonnet-4-6          → higher quality (recommended for demo)
    model: str = "claude-sonnet-4-6"

    # ── Server ────────────────────────────────────────────────────────────────
    frontend_url: str = "http://localhost:3000"
    stream_timeout_seconds: float = 120.0

    @model_validator(mode="after")
    def require_api_key_in_live_mode(self) -> Settings:
        if not self.demo_mode and not self.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required when DEMO_MODE=false.\n"
                "  Option A: Set ANTHROPIC_API_KEY=sk-ant-... in backend/.env\n"
                "  Option B: Set DEMO_MODE=true to run without an API key"
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance (singleton per process)."""
    return Settings()
