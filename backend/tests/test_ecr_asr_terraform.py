from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_ECR_MAIN = _REPO / "infra" / "ecr" / "main.tf"


def test_asr_inference_ecr_repository() -> None:
    text = _ECR_MAIN.read_text(encoding="utf-8")
    assert "aws_ecr_repository" in text
    assert "asr_inference" in text
    assert "voragon/asr-inference" in text or "asr_repository_name" in text
