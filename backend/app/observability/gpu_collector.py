"""Best-effort GPU stats for Prometheus (P7-007). Uses NVML when available."""

from __future__ import annotations

import logging

from prometheus_client import Gauge

logger = logging.getLogger(__name__)

GPU_UTILIZATION = Gauge(
    "voragon_gpu_utilization",
    "GPU utilization percentage (0-100) for the pod GPU",
    labelnames=("gpu_index",),
)
GPU_MEMORY_USED_BYTES = Gauge(
    "voragon_gpu_memory_used_bytes",
    "GPU memory used in bytes",
    labelnames=("gpu_index",),
)

_nvml_initialized = False


def refresh_gpu_gauges() -> None:
    """Update GPU gauges from NVML; no-op when NVML is unavailable (local CPU / tests)."""
    global _nvml_initialized
    try:
        import pynvml
    except ImportError:
        return

    try:
        if not _nvml_initialized:
            pynvml.nvmlInit()
            _nvml_initialized = True
        device_count = pynvml.nvmlDeviceGetCount()
        for index in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(index)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
            GPU_UTILIZATION.labels(gpu_index=str(index)).set(float(util.gpu))
            GPU_MEMORY_USED_BYTES.labels(gpu_index=str(index)).set(float(memory.used))
    except Exception as exc:
        logger.debug("GPU metrics unavailable: %s", exc)
