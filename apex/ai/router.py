"""
APEX AI Router - Multi-model AI orchestration
Route tasks to different AI providers by role and capability
"""
import asyncio
import time
import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("apex.ai")


class AIRole(str, Enum):
    BUILD = "build_ai"         # Code generation, architecture
    RUNTIME = "runtime_ai"    # Task planning, reasoning
    ROBOT = "robot_ai"        # Robot command generation
    VISION = "vision_ai"      # Computer vision analysis
    FALLBACK = "fallback"     # Catch-all


@dataclass
class AIProvider:
    name: str           # openai | anthropic | custom
    model: str
    api_key: str
    role: str
    endpoint: Optional[str] = None
    max_tokens: int = 2048
    temperature: float = 0.3
    timeout: float = 30.0
    # Stats
    total_calls: int = 0
    total_tokens: int = 0
    total_errors: int = 0
    avg_latency_ms: float = 0.0


@dataclass
class AIRequest:
    role: str
    prompt: str
    system_prompt: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    max_tokens: int = 1024
    stream: bool = False


@dataclass
class AIResponse:
    content: str
    provider: str
    model: str
    role: str
    latency_ms: float
    tokens_used: int = 0
    success: bool = True
    error: Optional[str] = None


class AIRouter:
    """
    APEX AI Router
    - Multiple provider support (OpenAI, Anthropic, custom)
    - Role-based routing (build, runtime, robot, vision)
    - Fallback chain
    - Latency and cost tracking
    - Configurable via YAML or env vars
    """

    def __init__(self):
        self._providers: Dict[str, AIProvider] = {}
        self._history: List[Dict] = []
        self._loaded = False

    async def load_providers(self):
        """Load providers from config/providers.yaml or environment variables."""
        try:
            import yaml
            config_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "config", "providers.yaml"
            )
            if os.path.exists(config_path):
                with open(config_path) as f:
                    cfg = yaml.safe_load(f)
                providers_cfg = cfg.get("providers", {})
                for role, pcfg in providers_cfg.items():
                    key = pcfg.get("api_key", "")
                    # Support env var substitution
                    if key.startswith("$"):
                        key = os.environ.get(key[1:], "")
                    self._providers[role] = AIProvider(
                        name=pcfg["name"],
                        model=pcfg["model"],
                        api_key=key,
                        role=role,
                        max_tokens=pcfg.get("max_tokens", 2048),
                        temperature=pcfg.get("temperature", 0.3),
                        timeout=pcfg.get("timeout", 30.0)
                    )
                    logger.info(f"[AI Router] Loaded provider '{role}' -> {pcfg['name']}/{pcfg['model']}")
        except Exception as e:
            logger.warning(f"[AI Router] Could not load providers.yaml: {e}")

        # Fallback: load from environment variables
        if not self._providers:
            self._load_from_env()

        self._loaded = True
        logger.info(f"[AI Router] {len(self._providers)} provider(s) loaded")

    def _load_from_env(self):
        """Load providers from environment variables as fallback."""
        openai_key = os.environ.get("OPENAI_API_KEY", "")
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")

        if openai_key:
            for role in ["build_ai", "robot_ai", "fallback"]:
                self._providers[role] = AIProvider(
                    name="openai",
                    model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
                    api_key=openai_key,
                    role=role
                )
            logger.info("[AI Router] Loaded OpenAI from env")

        if anthropic_key:
            self._providers["runtime_ai"] = AIProvider(
                name="anthropic",
                model=os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-5"),
                api_key=anthropic_key,
                role="runtime_ai"
            )
            logger.info("[AI Router] Loaded Anthropic from env")

    def add_provider(self, role: str, name: str, model: str, api_key: str,
                     endpoint: Optional[str] = None, **kwargs) -> None:
        """Dynamically add a provider at runtime."""
        self._providers[role] = AIProvider(
            name=name, model=model, api_key=api_key,
            role=role, endpoint=endpoint, **kwargs
        )
        logger.info(f"[AI Router] Added provider '{role}' -> {name}/{model}")

    def get_providers(self) -> Dict[str, dict]:
        return {
            role: {
                "name": p.name,
                "model": p.model,
                "role": p.role,
                "total_calls": p.total_calls,
                "total_errors": p.total_errors,
                "avg_latency_ms": round(p.avg_latency_ms, 2),
                "has_key": bool(p.api_key)
            }
            for role, p in self._providers.items()
        }

    async def call(self, req: AIRequest) -> AIResponse:
        """Route an AI request to the appropriate provider."""
        provider = self._providers.get(req.role)
        if not provider:
            provider = self._providers.get("fallback")
        if not provider:
            return AIResponse(
                content="", provider="none", model="none",
                role=req.role, latency_ms=0,
                success=False, error="No provider configured for role: " + req.role
            )

        t_start = time.time()
        try:
            if provider.name == "openai":
                result = await self._call_openai(provider, req)
            elif provider.name == "anthropic":
                result = await self._call_anthropic(provider, req)
            else:
                result = await self._call_custom(provider, req)

            latency = (time.time() - t_start) * 1000
            # Update stats
            provider.total_calls += 1
            provider.avg_latency_ms = (
                (provider.avg_latency_ms * (provider.total_calls - 1) + latency)
                / provider.total_calls
            )
            # Log to history
            self._history.append({
                "role": req.role,
                "provider": provider.name,
                "model": provider.model,
                "latency_ms": round(latency, 1),
                "ts": time.time()
            })
            if len(self._history) > 500:
                self._history = self._history[-500:]

            return AIResponse(
                content=result,
                provider=provider.name,
                model=provider.model,
                role=req.role,
                latency_ms=round(latency, 1)
            )

        except Exception as e:
            provider.total_errors += 1
            latency = (time.time() - t_start) * 1000
            logger.error(f"[AI Router] Error calling {provider.name}: {e}")
            return AIResponse(
                content="", provider=provider.name, model=provider.model,
                role=req.role, latency_ms=round(latency, 1),
                success=False, error=str(e)
            )

    async def _call_openai(self, provider: AIProvider, req: AIRequest) -> str:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=provider.api_key)
        messages = []
        if req.system_prompt:
            messages.append({"role": "system", "content": req.system_prompt})
        else:
            messages.append({"role": "system", "content":
                "You are APEX, an advanced AI assistant for robotic middleware. "
                "Be precise, technical, and concise."})
        messages.append({"role": "user", "content": req.prompt})

        resp = await client.chat.completions.create(
            model=provider.model,
            messages=messages,
            max_tokens=req.max_tokens,
            temperature=provider.temperature
        )
        return resp.choices[0].message.content or ""

    async def _call_anthropic(self, provider: AIProvider, req: AIRequest) -> str:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=provider.api_key)
        sys_prompt = req.system_prompt or (
            "You are APEX, an advanced AI assistant for robotic middleware. "
            "Be precise, technical, and concise."
        )
        resp = await client.messages.create(
            model=provider.model,
            max_tokens=req.max_tokens,
            system=sys_prompt,
            messages=[{"role": "user", "content": req.prompt}]
        )
        return resp.content[0].text if resp.content else ""

    async def _call_custom(self, provider: AIProvider, req: AIRequest) -> str:
        """Generic HTTP call for custom/local providers."""
        import httpx
        endpoint = provider.endpoint or "http://localhost:11434/api/generate"
        payload = {
            "model": provider.model,
            "prompt": req.prompt,
            "stream": False
        }
        async with httpx.AsyncClient(timeout=provider.timeout) as client:
            resp = await client.post(endpoint, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", data.get("content", str(data)))

    def history(self, limit: int = 50) -> List[Dict]:
        return self._history[-limit:]
