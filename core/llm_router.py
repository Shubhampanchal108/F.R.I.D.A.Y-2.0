"""
=============================================================================
F.R.I.D.A.Y 2.0 // MULTI-MODEL QUOTA FAILOVER & COGNITIVE ROUTER
=============================================================================
Prioritizes the user's primary configured LLM / Provider (OpenAI, Groq, etc.).
On quota exhaustion (HTTP 429, RateLimit, InsufficientQuota) or provider failure,
seamlessly fails over to OpenRouter across a 25+ model resilient free pool
with automated cooldown tracking and zero interruption.
=============================================================================
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import requests

# Ensure parent directory imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.config_driver import Check_Keys, load_data

logger = logging.getLogger("friday_llm_router")
logger.setLevel(logging.INFO)

# =============================================================================
# OPENROUTER RESILIENT MODEL POOL (All J.A.R.V.I.S models + top high-tier models)
# =============================================================================
OPENROUTER_MODELS: List[str] = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-coder:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "minimax/minimax-m2.5:free",
    "google/gemma-3-27b-it:free",
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "arcee-ai/trinity-large-preview:free",
    "z-ai/glm-4.5-air:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
    "google/gemma-3-12b-it:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "deepseek/deepseek-r1:free",
    "mistralai/mistral-small-24b-instruct-2501:free",
    "meta-llama/llama-3.1-70b-instruct:free",
    "google/gemma-3-4b-it:free",
    "google/gemma-3n-e4b-it:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "google/gemma-3n-e2b-it:free",
    "liquid/lfm-2.5-1.2b-instruct:free",
    "liquid/lfm-2.5-1.2b-thinking:free",
    "openrouter/auto",
]

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
RATE_LIMIT_COOLDOWN = 60  # seconds before retrying a rate-limited model
_rate_limited_models: Dict[str, float] = {}


def _get_openrouter_api_key() -> str:
    """Retrieves OpenRouter API Key from Friday config or JARVIS fallback."""
    try:
        data = load_data()
        key = data.get("KEYS", {}).get("OPENROUTER_API_KEY", "").strip()
        if key:
            return key
    except Exception:
        pass

    # Fallback to J.A.R.V.I.S api_keys.json if present
    jarvis_cfg = Path(__file__).resolve().parent.parent / "J.A.R.V.I.S" / "config" / "api_keys.json"
    if jarvis_cfg.exists():
        try:
            with open(jarvis_cfg, "r", encoding="utf-8") as f:
                j_data = json.load(f)
                j_key = j_data.get("openrouter_api_key", "").strip()
                if j_key:
                    return j_key
        except Exception:
            pass

    return ""


def _is_rate_limited(model: str) -> bool:
    ts = _rate_limited_models.get(model)
    if ts is None:
        return False
    if time.time() - ts > RATE_LIMIT_COOLDOWN:
        del _rate_limited_models[model]
        return False
    return True


def _mark_rate_limited(model: str):
    _rate_limited_models[model] = time.time()
    print(f"[LLM Router] ⏱️ Model '{model}' rate-limited — cooling down for {RATE_LIMIT_COOLDOWN}s")


def _call_openrouter(
    messages: List[Dict[str, str]],
    temperature: float = 0.3,
    max_tokens: int = 4096,
    timeout: float = 30.0,
    response_format: Optional[Dict] = None,
) -> Optional[str]:
    """Iterates through OpenRouter free model pool until one succeeds."""
    api_key = _get_openrouter_api_key()
    if not api_key:
        print("[LLM Router] ⚠️ No OpenRouter API key found in configuration. Cannot failover.")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/shubham-studio/friday",
        "X-Title": "F.R.I.D.A.Y 2.0",
    }

    payload_base = {
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        payload_base["response_format"] = response_format

    for model in OPENROUTER_MODELS:
        if _is_rate_limited(model):
            continue

        payload = dict(payload_base)
        payload["model"] = model

        try:
            print(f"[LLM Router] 🌐 Failover attempt via OpenRouter model: {model}")
            resp = requests.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload,
                timeout=timeout,
            )

            if resp.status_code == 429:
                _mark_rate_limited(model)
                continue

            if resp.status_code == 200:
                data = resp.json()
                content = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
                if content:
                    print(f"[LLM Router] ✅ Success via OpenRouter ({model})")
                    return content.strip()

            print(f"[LLM Router] ⚠️ OpenRouter {model} returned HTTP {resp.status_code}: {resp.text[:120]}")

        except Exception as e:
            print(f"[LLM Router] ⚠️ OpenRouter {model} connection notice: {e}")
            continue

    return None


class LLMRouter:
    """
    Centralized cognitive LLM client with quota failover.
    Attempts primary configured LLM first; on rate limits / quota failure,
    seamlessly shifts to OpenRouter free models.
    """

    @staticmethod
    def get_primary_config() -> tuple:
        try:
            data = load_data()
            llm_key = data.get("KEYS", {}).get("LLM_KEY", "")
            base_url = data.get("LLM", {}).get("LLM_SERVICE_PROVIDER_URL", "")
            model = data.get("LLM", {}).get("MODEL", "") or "llama-3.3-70b-versatile"
            return llm_key, base_url, model
        except Exception:
            return "", "", "llama-3.3-70b-versatile"

    @classmethod
    def chat_complete(
        cls,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
        timeout: float = 30.0,
        response_format: Optional[Dict] = None,
    ) -> str:
        """
        Executes chat completion with automatic failover.
        Returns the generated content string.
        """
        llm_key, base_url, model = cls.get_primary_config()

        # 1. Attempt Primary User-Configured Provider
        if llm_key:
            try:
                from openai import OpenAI
                client = OpenAI(
                    base_url=base_url if base_url else None,
                    api_key=llm_key,
                )

                call_kwargs: Dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "timeout": timeout,
                }
                if response_format:
                    call_kwargs["response_format"] = response_format

                resp = client.chat.completions.create(**call_kwargs)
                content = resp.choices[0].message.content or ""
                return content.strip()

            except Exception as e:
                err_str = str(e).lower()
                is_quota_issue = any(k in err_str for k in [
                    "429", "quota", "rate limit", "ratelimit", "insufficient_quota",
                    "exceeded your current quota", "tokens per minute", "requests per minute",
                    "resource_exhausted", "503", "connection error", "timeout"
                ])
                if is_quota_issue:
                    print(f"\n[LLM Router] ⚠️ Primary LLM Notice ({model}): {e}")
                    print("[LLM Router] 🚀 Primary model quota reached or rate limited! Seamlessly switching to OpenRouter resilient pool...")
                else:
                    print(f"[LLM Router] ⚠️ Primary LLM error: {e}. Attempting OpenRouter failover...")

        # 2. Seamless OpenRouter Failover Pool
        or_result = _call_openrouter(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            response_format=response_format,
        )

        if or_result:
            return or_result

        raise RuntimeError("All LLM providers (Primary and OpenRouter fallback pool) are currently unavailable.")


# Global convenience function
chat_complete = LLMRouter.chat_complete
