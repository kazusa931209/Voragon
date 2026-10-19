"""Contract checks for P8-008 ai-gateway EKS manifests."""

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_EKS = _REPO_ROOT / "k8s" / "eks"


def test_kustomization_includes_ai_gateway_resources() -> None:
    text = (_EKS / "kustomization.yaml").read_text(encoding="utf-8")
    assert "ai-gateway-deployment.yaml" in text
    assert "ai-gateway-service.yaml" in text
    assert "ai-gateway-configmap.yaml" in text
    assert "voragon/ai-gateway" in text


def test_ai_gateway_deployment_contract() -> None:
    text = (_EKS / "ai-gateway-deployment.yaml").read_text(encoding="utf-8")
    assert "name: ai-gateway" in text
    assert "app: ai-gateway" in text
    assert "containerPort: 8080" in text
    assert "AI_GATEWAY_REGISTRY_PATH" in text
    assert "/config/registry.yaml" in text
    assert "name: ai-gateway-config" in text


def test_ai_gateway_service_clusterip() -> None:
    text = (_EKS / "ai-gateway-service.yaml").read_text(encoding="utf-8")
    assert "type: ClusterIP" in text
    assert "name: ai-gateway" in text
    assert "port: 8080" in text
    assert "app: ai-gateway" in text


def test_ai_gateway_registry_configmap_points_at_asr_service() -> None:
    text = (_EKS / "ai-gateway-configmap.yaml").read_text(encoding="utf-8")
    assert "name: ai-gateway-config" in text
    assert "asr.default" in text
    assert "http://asr-service:8081" in text
