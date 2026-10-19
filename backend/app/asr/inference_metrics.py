"""Inference queue depth tracking for asr-service metrics (P7-007)."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from app.observability.metrics import set_inference_queue_depth

_active_inferences = 0
_lock = asyncio.Lock()


@asynccontextmanager
async def track_inference_queue():
    global _active_inferences
    async with _lock:
        _active_inferences += 1
        set_inference_queue_depth(_active_inferences)
    try:
        yield
    finally:
        async with _lock:
            _active_inferences -= 1
            set_inference_queue_depth(_active_inferences)
