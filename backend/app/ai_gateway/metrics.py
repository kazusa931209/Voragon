from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

from app.ai_gateway.health import ModelHealthStore
from app.ai_gateway.registry import ModelRegistry

GATEWAY_INFERENCE_REQUESTS = Counter(
    "voragon_gateway_inference_requests_total",
    "AI Gateway inference requests completed successfully",
    labelnames=("capability", "model", "kind"),
)
GATEWAY_INFERENCE_ERRORS = Counter(
    "voragon_gateway_inference_errors_total",
    "AI Gateway inference request failures",
    labelnames=("capability",),
)
GATEWAY_INFERENCE_DURATION = Histogram(
    "voragon_gateway_inference_duration_seconds",
    "AI Gateway inference latency including upstream ASR",
    labelnames=("capability", "model", "kind"),
)
GATEWAY_FALLBACK_ROUTES = Counter(
    "voragon_gateway_fallback_routes_total",
    "Successful inferences served by a non-primary model in the routing chain",
    labelnames=("capability", "model"),
)
GATEWAY_MODELS_ROUTABLE = Gauge(
    "voragon_gateway_models_routable",
    "Registered models currently routable (health checks considered)",
)


def record_inference_success(
    *,
    capability: str,
    model: str,
    kind: str,
    duration_s: float,
    used_fallback: bool,
) -> None:
    GATEWAY_INFERENCE_REQUESTS.labels(
        capability=capability, model=model, kind=kind
    ).inc()
    GATEWAY_INFERENCE_DURATION.labels(
        capability=capability, model=model, kind=kind
    ).observe(duration_s)
    if used_fallback:
        GATEWAY_FALLBACK_ROUTES.labels(capability=capability, model=model).inc()


def record_inference_error(capability: str) -> None:
    GATEWAY_INFERENCE_ERRORS.labels(capability=capability).inc()


def refresh_gateway_gauges(
    registry: ModelRegistry,
    health_store: ModelHealthStore,
    *,
    health_checks_enabled: bool,
) -> None:
    routable = sum(
        1
        for model_id in registry.models
        if health_store.is_routable(model_id, checks_enabled=health_checks_enabled)
    )
    GATEWAY_MODELS_ROUTABLE.set(routable)


async def gateway_metrics_body(
    registry: ModelRegistry,
    health_store: ModelHealthStore,
    *,
    health_checks_enabled: bool,
) -> bytes:
    refresh_gateway_gauges(
        registry, health_store, health_checks_enabled=health_checks_enabled
    )
    return generate_latest()


def metrics_content_type() -> str:
    return CONTENT_TYPE_LATEST
