"""Contract checks for P7-004/P7-005 asr-service EKS manifests."""

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_EKS = _REPO_ROOT / "k8s" / "eks"


def test_kustomization_includes_asr_resources() -> None:
    text = (_EKS / "kustomization.yaml").read_text(encoding="utf-8")
    assert "asr-deployment.yaml" in text
    assert "asr-service.yaml" in text
    assert "asr-configmap.yaml" in text
    assert "asr-pvc.yaml" in text
    assert "voragon/asr-inference" in text


def test_asr_deployment_gpu_scheduling() -> None:
    text = (_EKS / "asr-deployment.yaml").read_text(encoding="utf-8")
    assert 'node-type: gpu' in text
    assert "nvidia.com/gpu" in text
    assert 'value: "true"' in text
    assert "containerPort: 8081" in text
    assert 'nvidia.com/gpu: "1"' in text
    assert "app: asr-service" in text
    assert "name: asr-service" in text


def test_asr_service_clusterip() -> None:
    text = (_EKS / "asr-service.yaml").read_text(encoding="utf-8")
    assert "type: ClusterIP" in text
    assert "name: asr-service" in text
    assert "port: 8081" in text
    assert "app: asr-service" in text


def test_asr_model_cache_pvc() -> None:
    text = (_EKS / "asr-pvc.yaml").read_text(encoding="utf-8")
    assert "name: voragon-asr-model-cache" in text
    assert "storageClassName: gp2" in text
    assert "storage: 10Gi" in text


def test_asr_deployment_mounts_model_cache() -> None:
    deploy = (_EKS / "asr-deployment.yaml").read_text(encoding="utf-8")
    config = (_EKS / "asr-configmap.yaml").read_text(encoding="utf-8")
    assert "claimName: voragon-asr-model-cache" in deploy
    assert "mountPath: /var/lib/voragon/model-cache" in deploy
    assert "HF_HOME: \"/var/lib/voragon/model-cache/huggingface\"" in config
    assert "TORCH_HOME: \"/var/lib/voragon/model-cache/torch\"" in config
