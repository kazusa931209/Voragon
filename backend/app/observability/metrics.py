from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

from app.websocket.connection_registry import connection_count
from app.websocket.session_registry import detached_count

WS_CONNECTIONS = Gauge(
    "voragon_ws_connections",
    "Active WebSocket connections",
)
SESSIONS_ACTIVE = Gauge(
    "voragon_sessions_active",
    "Active sessions (connected plus detached awaiting resume)",
)
AUDIO_FRAMES_RECEIVED = Counter(
    "voragon_audio_frames_received_total",
    "Audio frames received into the processing pipeline",
)
AUDIO_FRAMES_DROPPED = Counter(
    "voragon_audio_frames_dropped_total",
    "Audio frames dropped due to buffer overflow",
)
TRANSCRIPT_PARTIAL = Counter(
    "voragon_transcript_partial_total",
    "Partial transcripts emitted",
)
TRANSCRIPT_FINAL = Counter(
    "voragon_transcript_final_total",
    "Final transcripts emitted",
)
ASR_INFERENCE_DURATION = Histogram(
    "voragon_asr_inference_duration_seconds",
    "ASR inference latency",
    labelnames=("kind",),
)
ASR_INFERENCE_ERRORS = Counter(
    "voragon_asr_inference_errors_total",
    "ASR inference failures",
)
INFERENCE_QUEUE_DEPTH = Gauge(
    "voragon_inference_queue_depth",
    "Pending inference requests in the ASR service",
)
MODEL_LOAD_DURATION = Gauge(
    "voragon_model_load_duration_seconds",
    "Model loading time at startup",
)


async def refresh_gauges() -> None:
    connections = await connection_count()
    detached = await detached_count()
    WS_CONNECTIONS.set(connections)
    SESSIONS_ACTIVE.set(connections + detached)


def record_audio_frame(*, dropped: int = 0) -> None:
    AUDIO_FRAMES_RECEIVED.inc()
    if dropped > 0:
        AUDIO_FRAMES_DROPPED.inc(dropped)


def record_transcript_partial() -> None:
    TRANSCRIPT_PARTIAL.inc()


def record_transcript_final() -> None:
    TRANSCRIPT_FINAL.inc()


def observe_asr_inference_duration(seconds: float, *, kind: str) -> None:
    ASR_INFERENCE_DURATION.labels(kind=kind).observe(seconds)


def record_asr_inference_error() -> None:
    ASR_INFERENCE_ERRORS.inc()


def set_inference_queue_depth(depth: int) -> None:
    INFERENCE_QUEUE_DEPTH.set(depth)


def observe_model_load_duration(seconds: float) -> None:
    MODEL_LOAD_DURATION.set(seconds)


async def asr_service_metrics_body() -> bytes:
    from app.observability.gpu_collector import refresh_gpu_gauges

    refresh_gpu_gauges()
    return generate_latest()


async def metrics_body() -> bytes:
    await refresh_gauges()
    return generate_latest()


def metrics_content_type() -> str:
    return CONTENT_TYPE_LATEST
