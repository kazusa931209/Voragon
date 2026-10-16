from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator

DEFAULT_REGISTRY_PATH = Path(__file__).resolve().parent / "default_registry.yaml"


class ModelRegistryEntry(BaseModel):
    type: Literal["asr", "llm", "embedding", "vision"]
    endpoint: str = Field(min_length=1)
    capabilities: list[str] = Field(min_length=1)
    version: str = Field(min_length=1)
    languages: list[str] = Field(default_factory=list)
    health_check_interval_s: int = Field(default=30, ge=1)


class ModelRegistry(BaseModel):
    models: dict[str, ModelRegistryEntry]

    @field_validator("models")
    @classmethod
    def validate_unique_capabilities(
        cls, models: dict[str, ModelRegistryEntry]
    ) -> dict[str, ModelRegistryEntry]:
        seen: dict[str, str] = {}
        for model_id, entry in models.items():
            for capability in entry.capabilities:
                if capability in seen:
                    raise ValueError(
                        f"Capability {capability!r} mapped to both "
                        f"{seen[capability]!r} and {model_id!r}"
                    )
                seen[capability] = model_id
        return models

    def resolve_capability(self, capability: str) -> tuple[str, ModelRegistryEntry]:
        for model_id, entry in self.models.items():
            if capability in entry.capabilities:
                return model_id, entry
        raise KeyError(f"Unknown capability: {capability}")

    def capability_map(self) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for model_id, entry in self.models.items():
            for capability in entry.capabilities:
                mapping[capability] = model_id
        return mapping


def load_model_registry(path: Path | None = None) -> ModelRegistry:
    registry_path = path or DEFAULT_REGISTRY_PATH
    raw = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid registry file (expected mapping): {registry_path}")
    return ModelRegistry.model_validate(raw)
