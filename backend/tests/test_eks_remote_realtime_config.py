"""EKS realtime ConfigMap contract for remote ASR (P7-006) via AI Gateway (P8-006)."""

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CONFIGMAP = _REPO_ROOT / "k8s" / "eks" / "configmap.yaml"


def test_realtime_config_uses_remote_asr_on_eks() -> None:
    text = _CONFIGMAP.read_text(encoding="utf-8")
    assert "ASR_BACKEND: remote" in text or 'ASR_BACKEND: "remote"' in text
    assert "ASR_REMOTE_BASE_URL" in text
    assert "ai-gateway:8080" in text
    assert "ASR_REMOTE_VIA_AI_GATEWAY" in text
    assert "ASR_CAPABILITY" in text
    assert "asr.default" in text
