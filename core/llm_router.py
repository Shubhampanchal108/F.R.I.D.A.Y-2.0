"""
=============================================================================
F.R.I.D.A.Y 2.0 // MULTI-TIER NEURAL CORE & QUOTA FAILOVER ROUTER
=============================================================================
4-Tier Resilient Architecture:
  Tier 1: Groq Cloud LPUs (Ultra-Fast LPUs + Multi-Key Rotation)
  Tier 2: Google Gemini Official (All Models + Multi-Key Rotation)
  Tier 3: Hugging Face Serverless Router (30+ Deep Reasoning/Chat/Code Models)
  Tier 4: OpenRouter Free Pool (26+ Resilient Free Models)

Full support for multiple API keys per provider, per-model and per-key rate-limit
cooldown tracking, and zero downtime.
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

from config.config_driver import load_data, get_neural_keys

logger = logging.getLogger("friday_llm_router")
logger.setLevel(logging.INFO)

# =============================================================================
# 1. GOOGLE GEMINI OFFICIAL (TIER 1 - PRIORITY 1)
# =============================================================================
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
GEMINI_MODELS: List[str] = [
    "gemini-3.8-flash",
    "gemini-3.1-pro-preview",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]

# =============================================================================
# 2. HUGGING FACE SERVERLESS INFERENCE ROUTER (TIER 2 - PRIORITY 2)
# =============================================================================
HUGGINGFACE_API_URL = "https://router.huggingface.co/hf-inference/v1"
HUGGINGFACE_MODELS: List[str] = [
    # Deep Reasoning & Distill Champions
    "deepseek-ai/DeepSeek-R1",
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
    "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
    "deepseek-ai/DeepSeek-V3",
    "Qwen/QwQ-32B-Preview",
    # Meta Llama Family
    "meta-llama/Llama-3.3-70B-Instruct",
    "meta-llama/Meta-Llama-3.1-70B-Instruct",
    "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "meta-llama/Llama-3.2-3B-Instruct",
    "meta-llama/Llama-3.2-1B-Instruct",
    # Qwen 2.5 General & Coding Family
    "Qwen/Qwen2.5-72B-Instruct",
    "Qwen/Qwen2.5-Coder-32B-Instruct",
    "Qwen/Qwen2.5-32B-Instruct",
    "Qwen/Qwen2.5-14B-Instruct",
    "Qwen/Qwen2.5-Coder-7B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct",
    # Mistral & Mixtral MoE
    "mistralai/Mistral-Small-24B-Instruct-2501",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "mistralai/Mixtral-8x22B-Instruct-v0.1",
    # Google Gemma & Microsoft Phi
    "google/gemma-2-27b-it",
    "google/gemma-2-9b-it",
    "google/gemma-2-2b-it",
    "microsoft/Phi-4",
    "microsoft/Phi-3.5-mini-instruct",
    # Frontier Open-weights
    "NousResearch/Hermes-3-Llama-3.1-8B",
    "CohereForAI/c4ai-command-r-plus-08-2024",
    "openchat/openchat-3.5-0106",
]

# =============================================================================
# 3. GROQ CLOUD LPUs (TIER 3 - PRIORITY 3)
# =============================================================================
GROQ_API_URL = "https://api.groq.com/openai/v1"
GROQ_MODELS: List[str] = [
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "deepseek-r1-distill-llama-70b",
    "qwen-2.5-32b",
    "gemma2-9b-it",
    "mixtral-8x7b-32768",
]

# =============================================================================
# 4. OPENROUTER RESILIENT FREE POOL (TIER 4 - PRIORITY 4)
# =============================================================================
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
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

RATE_LIMIT_COOLDOWN = 60  # seconds
_rate_limited_models: Dict[str, float] = {}
_rate_limited_keys: Dict[str, float] = {}


def _is_rate_limited(provider: str, identifier: str) -> bool:
    key = f"{provider}:{identifier}"
    ts = _rate_limited_models.get(key) or _rate_limited_keys.get(key)
    if ts is None:
        return False
    if time.time() - ts > RATE_LIMIT_COOLDOWN:
        _rate_limited_models.pop(key, None)
        _rate_limited_keys.pop(key, None)
        return False
    return True


def _mark_rate_limited(provider: str, identifier: str, is_key: bool = False):
    key = f"{provider}:{identifier}"
    if is_key:
        _rate_limited_keys[key] = time.time()
        masked = identifier[:6] + "..." if len(identifier) > 6 else identifier
        print(f"[LLM Router] ⏱️ Key [{provider}][{masked}] rate-limited — cooling down for {RATE_LIMIT_COOLDOWN}s")
    else:
        _rate_limited_models[key] = time.time()
        print(f"[LLM Router] ⏱️ Model [{provider}][{identifier}] rate-limited — cooling down for {RATE_LIMIT_COOLDOWN}s")


# =============================================================================
# TIER RUNNERS
# =============================================================================

def _call_openai_compatible(
    provider_name: str,
    base_url: str,
    api_key: str,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.3,
    max_tokens: int = 4096,
    timeout: float = 30.0,
    response_format: Optional[Dict] = None,
) -> Optional[str]:
    """Universal caller for OpenAI-compatible providers (Gemini, HuggingFace, Groq)."""
    from openai import OpenAI

    client = OpenAI(base_url=base_url, api_key=api_key)
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
    if resp and resp.choices and resp.choices[0].message:
        content = resp.choices[0].message.content or ""
        return content.strip()
    return None


def _call_openrouter_direct(
    api_key: str,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.3,
    max_tokens: int = 4096,
    timeout: float = 30.0,
    response_format: Optional[Dict] = None,
) -> Optional[str]:
    """Direct HTTP caller for OpenRouter models."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/shubham-studio/friday",
        "X-Title": "F.R.I.D.A.Y 2.0",
    }
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        payload["response_format"] = response_format

    resp = requests.post(
        OPENROUTER_API_URL,
        headers=headers,
        json=payload,
        timeout=timeout,
    )
    if resp.status_code == 200:
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

    if resp.status_code in [429, 402, 503]:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:120]}")

    return None


class LLMRouter:
    """
    Centralized 4-Tier Cognitive Router with Cascade Failover & Multi-Key Rotation.
    Priority 1: Groq Cloud LPUs
    Priority 2: Google Gemini Official
    Priority 3: Hugging Face Serverless
    Priority 4: OpenRouter Free Pool
    """

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
        Executes chat completion with automatic cascade failover across providers,
        multiple keys, and model pools.
        """
        neural_keys = get_neural_keys()

        # =====================================================================
        # TIER 1: GROQ CLOUD LPUs (PRIORITY 1)
        # =====================================================================
        groq_keys = neural_keys.get("GROQ", [])
        if groq_keys:
            for key_idx, groq_key in enumerate(groq_keys):
                if _is_rate_limited("GROQ_KEY", groq_key):
                    continue

                for model in GROQ_MODELS:
                    if _is_rate_limited("GROQ", model):
                        continue

                    try:
                        print(f"[LLM Router] ⚡ [Tier 1 Groq] Trying model: {model} (Key #{key_idx + 1})")
                        content = _call_openai_compatible(
                            provider_name="GROQ",
                            base_url=GROQ_API_URL,
                            api_key=groq_key,
                            model=model,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            timeout=timeout,
                            response_format=response_format,
                        )
                        if content:
                            print(f"[LLM Router] ✅ Success via Groq ({model})")
                            return content

                    except Exception as e:
                        err_str = str(e).lower()
                        if any(k in err_str for k in ["429", "rate limit", "quota", "tpm", "rpm"]):
                            _mark_rate_limited("GROQ", model)
                            continue
                        else:
                            continue

        # =====================================================================
        # TIER 2: GOOGLE GEMINI OFFICIAL (PRIORITY 2)
        # =====================================================================
        gemini_keys = neural_keys.get("GEMINI", [])
        if gemini_keys:
            for key_idx, gem_key in enumerate(gemini_keys):
                if _is_rate_limited("GEMINI_KEY", gem_key):
                    continue

                for model in GEMINI_MODELS:
                    if _is_rate_limited("GEMINI", model):
                        continue

                    try:
                        print(f"[LLM Router] 🔷 [Tier 2 Gemini] Trying model: {model} (Key #{key_idx + 1})")
                        content = _call_openai_compatible(
                            provider_name="GEMINI",
                            base_url=GEMINI_API_URL,
                            api_key=gem_key,
                            model=model,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            timeout=timeout,
                            response_format=response_format,
                        )
                        if content:
                            print(f"[LLM Router] ✅ Success via Google Gemini ({model})")
                            return content

                    except Exception as e:
                        err_str = str(e).lower()
                        if any(k in err_str for k in ["429", "resource_exhausted", "quota", "rate limit"]):
                            _mark_rate_limited("GEMINI", model)
                            # If quota for entire key exhausted, mark key
                            if "quota" in err_str or "exceeded" in err_str:
                                _mark_rate_limited("GEMINI_KEY", gem_key, is_key=True)
                                break
                            continue
                        elif any(k in err_str for k in ["503", "timeout", "unavailable", "server error"]):
                            _mark_rate_limited("GEMINI", model)
                            continue
                        else:
                            print(f"[LLM Router] ⚠️ Gemini {model} note: {e}")
                            continue

        # =====================================================================
        # TIER 3: HUGGING FACE SERVERLESS ROUTER (PRIORITY 3)
        # =====================================================================
        hf_keys = neural_keys.get("HUGGINGFACE", [])
        if hf_keys:
            for key_idx, hf_key in enumerate(hf_keys):
                if _is_rate_limited("HF_KEY", hf_key):
                    continue

                for model in HUGGINGFACE_MODELS:
                    if _is_rate_limited("HUGGINGFACE", model):
                        continue

                    try:
                        print(f"[LLM Router] 🤗 [Tier 3 HuggingFace] Trying model: {model} (Key #{key_idx + 1})")
                        content = _call_openai_compatible(
                            provider_name="HUGGINGFACE",
                            base_url=HUGGINGFACE_API_URL,
                            api_key=hf_key,
                            model=model,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            timeout=timeout,
                            response_format=response_format,
                        )
                        if content:
                            print(f"[LLM Router] ✅ Success via Hugging Face ({model})")
                            return content

                    except Exception as e:
                        err_str = str(e).lower()
                        if any(k in err_str for k in ["429", "rate limit", "quota"]):
                            _mark_rate_limited("HUGGINGFACE", model)
                            continue
                        elif any(k in err_str for k in ["503", "loading", "estimated_time", "timeout"]):
                            _mark_rate_limited("HUGGINGFACE", model)
                            continue
                        else:
                            continue

        # =====================================================================
        # TIER 4: OPENROUTER RESILIENT FREE POOL (PRIORITY 4)
        # =====================================================================
        or_keys = neural_keys.get("OPENROUTER", [])
        # Also check fallback J.A.R.V.I.S or config single key if list empty
        if not or_keys:
            cfg_or = load_data().get("KEYS", {}).get("OPENROUTER_API_KEY", "").strip()
            if cfg_or:
                or_keys = [cfg_or]

        if or_keys:
            for key_idx, or_key in enumerate(or_keys):
                if _is_rate_limited("OR_KEY", or_key):
                    continue

                for model in OPENROUTER_MODELS:
                    if _is_rate_limited("OPENROUTER", model):
                        continue

                    try:
                        print(f"[LLM Router] 🌐 [Tier 4 OpenRouter] Trying model: {model} (Key #{key_idx + 1})")
                        content = _call_openrouter_direct(
                            api_key=or_key,
                            model=model,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            timeout=timeout,
                            response_format=response_format,
                        )
                        if content:
                            print(f"[LLM Router] ✅ Success via OpenRouter ({model})")
                            return content

                    except Exception as e:
                        err_str = str(e).lower()
                        if any(k in err_str for k in ["429", "rate limit", "credits", "quota", "503"]):
                            _mark_rate_limited("OPENROUTER", model)
                            continue
                        else:
                            continue

        # =====================================================================
        # TIER 5: LEGACY SINGLE LLM_KEY FALLBACK (IF CONFIGURED)
        # =====================================================================
        data = load_data()
        legacy_key = data.get("KEYS", {}).get("LLM_KEY", "").strip()
        legacy_url = data.get("LLM", {}).get("LLM_SERVICE_PROVIDER_URL", "").strip()
        legacy_model = data.get("LLM", {}).get("MODEL", "").strip() or "llama-3.3-70b-versatile"

        if legacy_key:
            try:
                print(f"[LLM Router] 🔄 Attempting legacy configured provider: {legacy_model}")
                content = _call_openai_compatible(
                    provider_name="LEGACY",
                    base_url=legacy_url if legacy_url else None,
                    api_key=legacy_key,
                    model=legacy_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout,
                    response_format=response_format,
                )
                if content:
                    return content
            except Exception as e:
                print(f"[LLM Router] ⚠️ Legacy LLM error: {e}")

        raise RuntimeError(
            "All Neural Core Providers (Gemini, HuggingFace, Groq, OpenRouter) "
            "are currently rate-limited, exhausted, or have no valid keys configured."
        )


# Global convenience function
chat_complete = LLMRouter.chat_complete
