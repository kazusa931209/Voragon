"""Contract checks for P7-001 GPU node pool in infra/eks Terraform."""

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_EKS_MAIN = _REPO_ROOT / "infra" / "eks" / "main.tf"
_EKS_VARS = _REPO_ROOT / "infra" / "eks" / "variables.tf"
_NVIDIA_PLUGIN = _REPO_ROOT / "infra" / "eks" / "nvidia_device_plugin.tf"


def test_gpu_node_group_in_main_tf() -> None:
    text = _EKS_MAIN.read_text(encoding="utf-8")
    assert "enable_gpu_node_group" in text
    assert 'node-type = "gpu"' in text
    assert "nvidia.com/gpu" in text
    assert 'node-type = "cpu"' in text


def test_gpu_variables_defined() -> None:
    text = _EKS_VARS.read_text(encoding="utf-8")
    assert "variable \"enable_gpu_node_group\"" in text
    assert "variable \"gpu_node_instance_types\"" in text


def test_nvidia_device_plugin_helm_release() -> None:
    text = _NVIDIA_PLUGIN.read_text(encoding="utf-8")
    assert "helm_release" in text
    assert "nvidia.github.io/k8s-device-plugin" in text
    assert "enable_gpu_node_group" in text
