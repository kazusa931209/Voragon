from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.ai_gateway.registry import ModelRegistry, ModelRegistryEntry

logger = logging.getLogger(__name__)


@dataclass
class ModelHealthState:
    healthy: bool = False
    ever_failed: bool = False
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    message: str | None = None
    checked: bool = False


@dataclass
class ModelHealthStore:
    failure_threshold: int = 3
    recovery_threshold: int = 2
    _states: dict[str, ModelHealthState] = field(default_factory=dict)

    def snapshot(self, model_id: str) -> dict[str, object]:
        state = self._states.get(model_id)
        if state is None or not state.checked:
            return {
                "status": "unchecked",
                "ready": None,
                "message": "No health probe yet",
            }
        if state.healthy:
            return {
                "status": "healthy",
                "ready": True,
                "message": state.message,
            }
        return {
            "status": "unhealthy",
            "ready": False,
            "message": state.message or "Model backend unhealthy",
        }

    def is_routable(self, model_id: str, *, checks_enabled: bool) -> bool:
        if not checks_enabled:
            return True
        state = self._states.get(model_id)
        if state is None or not state.checked:
            return False
        return state.healthy

    def any_routable(self, model_ids: list[str], *, checks_enabled: bool) -> bool:
        if not checks_enabled:
            return True
        return any(self.is_routable(model_id, checks_enabled=True) for model_id in model_ids)

    def record_probe(self, model_id: str, *, success: bool, message: str | None) -> None:
        state = self._states.setdefault(model_id, ModelHealthState())
        state.checked = True
        state.message = message
        if success:
            state.consecutive_failures = 0
            state.consecutive_successes += 1
            if state.consecutive_successes >= self.recovery_threshold or (
                not state.ever_failed and state.consecutive_successes >= 1
            ):
                state.healthy = True
        else:
            state.consecutive_successes = 0
            state.consecutive_failures += 1
            state.ever_failed = True
            if state.consecutive_failures >= self.failure_threshold:
                state.healthy = False
            elif state.consecutive_failures == 1 and not state.healthy:
                state.healthy = False


async def probe_asr_backend(
    http_client: httpx.AsyncClient,
    entry: ModelRegistryEntry,
    *,
    timeout_s: float,
) -> tuple[bool, str | None]:
    url = f"{entry.endpoint.rstrip('/')}/health"
    try:
        response = await http_client.get(url, timeout=timeout_s)
    except httpx.HTTPError as exc:
        return False, f"Backend unreachable: {exc}"

    if response.status_code == 503:
        return False, "Backend reported degraded"

    try:
        response.raise_for_status()
        body: dict[str, Any] = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        return False, f"Invalid health response: {exc}"

    asr = body.get("asr") if isinstance(body.get("asr"), dict) else {}
    ready = bool(asr.get("ready"))
    if ready:
        return True, None
    return False, "ASR model not ready"


class ModelHealthChecker:
    def __init__(
        self,
        registry: ModelRegistry,
        http_client: httpx.AsyncClient,
        store: ModelHealthStore,
        *,
        check_timeout_s: float,
        check_interval_s: float,
        enabled: bool,
    ) -> None:
        self._registry = registry
        self._http_client = http_client
        self._store = store
        self._check_timeout_s = check_timeout_s
        self._check_interval_s = check_interval_s
        self._enabled = enabled
        self._task: asyncio.Task[None] | None = None

    async def check_all(self) -> None:
        if not self._enabled:
            return
        for model_id, entry in self._registry.models.items():
            if entry.type != "asr":
                continue
            success, message = await probe_asr_backend(
                self._http_client,
                entry,
                timeout_s=self._check_timeout_s,
            )
            self._store.record_probe(model_id, success=success, message=message)
            logger.debug(
                "Health probe model=%s success=%s message=%s",
                model_id,
                success,
                message,
            )

    async def run_loop(self) -> None:
        while True:
            await asyncio.sleep(self._check_interval_s)
            await self.check_all()

    def start_background(self) -> None:
        if not self._enabled:
            return
        self._task = asyncio.create_task(self.run_loop(), name="ai-gateway-health")

    async def stop_background(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None
