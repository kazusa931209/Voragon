"""Doc contract checks for P7-008 Phase 7 GPU contributor path."""

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PHASE7_PATH = _REPO_ROOT / "docs" / "operations" / "phase7-gpu-path.md"
_AWS_DEPLOY = _REPO_ROOT / "docs" / "operations" / "aws-deployment.md"
_PHASE7_EXIT = _REPO_ROOT / "docs" / "roadmap" / "dev-step-phase7-exit.md"
_DOCS_README = _REPO_ROOT / "docs" / "README.md"


def test_phase7_gpu_path_doc_exists_and_links_dev_steps() -> None:
    text = _PHASE7_PATH.read_text(encoding="utf-8")
    assert "P7-001" in text and "P7-007" in text
    assert "kustomize edit set image" in text
    assert "ASR_BACKEND=remote" in text
    assert "asr-service:8081/metrics" in text or "/metrics" in text


def test_aws_deployment_links_phase7_gpu_path() -> None:
    text = _AWS_DEPLOY.read_text(encoding="utf-8")
    assert "phase7-gpu-path.md" in text
    assert "P7-007" in text
    assert "Implemented" in text


def test_phase7_exit_and_docs_readme_cross_link() -> None:
    exit_text = _PHASE7_EXIT.read_text(encoding="utf-8")
    readme = _DOCS_README.read_text(encoding="utf-8")
    assert "phase7-gpu-path.md" in exit_text
    assert "phase7-gpu-path.md" in readme
    assert "dev-step-phase7-exit.md" in readme
