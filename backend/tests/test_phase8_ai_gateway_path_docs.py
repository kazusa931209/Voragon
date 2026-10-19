"""Doc contract checks for P8-010 Phase 8 AI Gateway contributor path."""

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PHASE8_PATH = _REPO_ROOT / "docs" / "operations" / "phase8-ai-gateway-path.md"
_AWS_DEPLOY = _REPO_ROOT / "docs" / "operations" / "aws-deployment.md"
_PHASE8_EXIT = _REPO_ROOT / "docs" / "roadmap" / "dev-step-phase8-exit.md"
_DOCS_README = _REPO_ROOT / "docs" / "README.md"


def test_phase8_ai_gateway_path_doc_exists_and_links_dev_steps() -> None:
    text = _PHASE8_PATH.read_text(encoding="utf-8")
    assert "P8-006" in text and "P8-008" in text
    assert "ai_gateway_repository_url" in text
    assert "ASR_REMOTE_VIA_AI_GATEWAY" in text or "ai-gateway:8080" in text


def test_aws_deployment_links_phase8_ai_gateway_path() -> None:
    text = _AWS_DEPLOY.read_text(encoding="utf-8")
    assert "phase8-ai-gateway-path.md" in text
    assert "P8-008" in text
    assert "Implemented" in text


def test_phase8_exit_and_docs_readme_cross_link() -> None:
    exit_text = _PHASE8_EXIT.read_text(encoding="utf-8")
    readme = _DOCS_README.read_text(encoding="utf-8")
    assert "phase8-ai-gateway-path.md" in exit_text
    assert "phase8-ai-gateway-path.md" in readme
    assert "dev-step-phase8-exit.md" in readme
