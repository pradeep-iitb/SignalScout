import json
import asyncio
import logging
import httpx
from typing import Any, Dict, List, Optional
from backend.config.settings import settings

logger = logging.getLogger("signalscout.llm")

# Live Gemini models prioritized by availability and speed
GEMINI_MODELS_CASCADE = [
    "gemini-flash-lite-latest",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.8-flash"
]

# Live Grok / xAI models
XAI_MODELS_CASCADE = [
    "grok-3-mini",
    "grok-2-latest",
    "grok-beta"
]


class LLMService:
    def _provider(self) -> str:
        provider = settings.LLM_PROVIDER.strip().lower()
        if provider not in {"gemini", "grok"}:
            raise RuntimeError(f"LLM_PROVIDER must be 'gemini' or 'grok' (got: {provider})")
        return provider

    async def generate_json(self, prompt: str) -> Dict[str, Any]:
        """
        Executes live LLM request.
        If a model returns HTTP 503 (high demand) or 429, it dynamically switches
        to the next live model in the cascade (e.g. flash-lite-latest -> 3.5-flash-lite -> 3.5-flash).
        Does NOT use mock fallbacks!
        """
        provider = self._provider()
        
        if provider == "gemini":
            return await self._generate_gemini_cascade(prompt)
        elif provider == "grok":
            return await self._generate_grok_cascade(prompt)
        
        raise RuntimeError(f"Unsupported LLM provider: {provider}")

    async def _generate_gemini_cascade(self, prompt: str) -> Dict[str, Any]:
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not configured. Add it to .env.")

        # Build candidate list starting with configured model if present
        primary_model = settings.LLM_MODEL or "gemini-flash-lite-latest"
        models_to_try = [primary_model] + [m for m in GEMINI_MODELS_CASCADE if m != primary_model]
        
        last_error = None
        timeout = httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0)

        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            body = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"},
            }
            print(f"[LLM REQUEST] Live Gemini call with model: {model}", flush=True)

            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        url,
                        params={"key": settings.GEMINI_API_KEY},
                        json=body
                    )

                if response.status_code == 200:
                    data = response.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = json.loads(text)
                    print(f"[LLM SUCCESS] Model {model} returned valid live JSON", flush=True)
                    return parsed

                elif response.status_code in {503, 429}:
                    print(f"[MODEL SWITCH] {model} is experiencing high demand (HTTP {response.status_code}). Switching to next live model...", flush=True)
                    last_error = f"{model} returned HTTP {response.status_code}: {response.text[:150]}"
                    continue

                else:
                    print(f"[MODEL ERROR] {model} returned HTTP {response.status_code}. Trying next model...", flush=True)
                    last_error = f"{model} returned HTTP {response.status_code}: {response.text[:150]}"
                    continue

            except Exception as e:
                print(f"[MODEL EXCEPTION] {model} failed: {e}. Trying next model...", flush=True)
                last_error = str(e)
                continue

        raise RuntimeError(f"All live Gemini models failed. Last error: {last_error}")

    async def _generate_grok_cascade(self, prompt: str) -> Dict[str, Any]:
        api_key = settings.XAI_API_KEY or settings.GROK_API_KEY
        if not api_key:
            raise RuntimeError("GROK_API_KEY is not configured in .env.")

        base_url = (settings.XAI_BASE_URL or "https://api.x.ai/v1").rstrip("/")
        url = f"{base_url}/chat/completions"
        primary_model = settings.XAI_MODEL or "grok-3-mini"
        models_to_try = [primary_model] + [m for m in XAI_MODELS_CASCADE if m != primary_model]

        last_error = None
        timeout = httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0)

        for model in models_to_try:
            body = {
                "model": model,
                "temperature": 0.1,
                "messages": [
                    {"role": "system", "content": "Return valid JSON only. No prose or markdown fences."},
                    {"role": "user", "content": prompt},
                ],
                "response_format": {"type": "json_object"},
            }
            print(f"[LLM REQUEST] Live Grok call with model: {model}", flush=True)

            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        url,
                        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                        json=body
                    )

                if response.status_code == 200:
                    data = response.json()
                    text = data["choices"][0]["message"]["content"]
                    parsed = json.loads(text)
                    print(f"[LLM SUCCESS] Grok {model} returned valid live JSON", flush=True)
                    return parsed

                elif response.status_code in {503, 429}:
                    print(f"[MODEL SWITCH] Grok {model} returned HTTP {response.status_code}. Switching...", flush=True)
                    last_error = f"Grok {model} returned HTTP {response.status_code}"
                    continue

                else:
                    last_error = f"Grok {model} returned HTTP {response.status_code}: {response.text[:150]}"
                    continue

            except Exception as e:
                last_error = str(e)
                continue

        raise RuntimeError(f"All live Grok models failed. Last error: {last_error}")


llm_service = LLMService()
