import base64
import re
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def asr_inference_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("ASR_BACKEND", "mock")
    from app.asr_inference.main import app

    with TestClient(app) as client:
        yield client


def _assert_metric_registered(body: str, name: str, metric_type: str) -> None:
    assert f"# HELP {name}" in body
    assert f"# TYPE {name} {metric_type}" in body


def test_asr_service_metrics_endpoint_exposes_gpu_and_inference_series(
    asr_inference_client: TestClient,
) -> None:
    with patch("app.observability.gpu_collector.refresh_gpu_gauges") as refresh:
        def _set_gpu() -> None:
            from app.observability.gpu_collector import GPU_MEMORY_USED_BYTES, GPU_UTILIZATION

            GPU_UTILIZATION.labels(gpu_index="0").set(55.0)
            GPU_MEMORY_USED_BYTES.labels(gpu_index="0").set(1_000_000.0)

        refresh.side_effect = _set_gpu
        response = asr_inference_client.get("/metrics")

    assert response.status_code == 200
    body = response.text
    _assert_metric_registered(body, "voragon_gpu_utilization", "gauge")
    _assert_metric_registered(body, "voragon_gpu_memory_used_bytes", "gauge")
    _assert_metric_registered(body, "voragon_asr_inference_duration_seconds", "histogram")
    _assert_metric_registered(body, "voragon_asr_inference_errors_total", "counter")
    _assert_metric_registered(body, "voragon_inference_queue_depth", "gauge")
    _assert_metric_registered(body, "voragon_model_load_duration_seconds", "gauge")
    assert re.search(r'voragon_gpu_utilization\{gpu_index="0"\} 55(\.0)?', body)


def test_inference_updates_asr_duration_histogram(asr_inference_client: TestClient) -> None:
    from app.asr.mock_asr import MIN_AUDIO_BYTES_FOR_TEXT

    audio_b64 = base64.b64encode(b"\x00" * MIN_AUDIO_BYTES_FOR_TEXT).decode("ascii")
    before = asr_inference_client.get("/metrics").text
    asr_inference_client.post(
        "/v1/inference/asr",
        json={
            "kind": "final",
            "segment_id": "seg-metrics",
            "language": "en",
            "audio_base64": audio_b64,
        },
    )
    after = asr_inference_client.get("/metrics").text
    assert "voragon_asr_inference_duration_seconds_count{kind=\"final\"}" in after
    assert after.count("voragon_asr_inference_duration_seconds_count") >= before.count(
        "voragon_asr_inference_duration_seconds_count"
    )


def test_metric_registration_module_imports() -> None:
    from app.observability import gpu_collector, metrics

    assert metrics.ASR_INFERENCE_ERRORS._name == "voragon_asr_inference_errors"
    assert gpu_collector.GPU_UTILIZATION._name == "voragon_gpu_utilization"
