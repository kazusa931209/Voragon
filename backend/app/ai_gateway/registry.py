from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

DEFAULT_REGISTRY_PATH = Path(__file__).resolve().parent / "default_registry.yaml"


class ModelRegistryEntry(BaseModel):
    type: Literal["asr", "llm", "embedding", "vision"]
    endpoint: str = Field(min_length=1)
    capabilities: list[str] = Field(default_factory=list)
    version: str = Field(min_length=1)
    languages: list[str] = Field(default_factory=list)
    health_check_interval_s: int = Field(default=30, ge=1)


class CapabilityRouting(BaseModel):
    primary: str = Field(min_length=1)
    fallback: list[str] = Field(default_factory=list)


class ModelRegistry(BaseModel):
    models: dict[str, ModelRegistryEntry]
    routing: dict[str, CapabilityRouting] = Field(default_factory=dict)

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

    @model_validator(mode="after")
    def validate_routing(self) -> ModelRegistry:
        cap_map = self.capability_map()
        for capability, route in self.routing.items():
            if capability not in cap_map:
                raise ValueError(
                    f"Routing for unknown capability {capability!r} (not on any model)"
                )
            if cap_map[capability] != route.primary:
                raise ValueError(
                    f"Routing primary {route.primary!r} does not match capability "
                    f"{capability!r} owner {cap_map[capability]!r}"
                )
            if route.primary not in self.models:
                raise ValueError(f"Routing primary model not found: {route.primary!r}")
            for fallback_id in route.fallback:
                if fallback_id not in self.models:
                    raise ValueError(f"Routing fallback model not found: {fallback_id!r}")
                if fallback_id == route.primary:
                    raise ValueError(
                        f"Fallback for {capability!r} duplicates primary {route.primary!r}"
                    )
        return self

    @model_validator(mode="after")
    def fill_default_routing(self) -> ModelRegistry:
        if self.routing:
            return self
        self.routing = {
            capability: CapabilityRouting(primary=model_id)
            for capability, model_id in self.capability_map().items()
        }
        return self

    def resolve_capability(self, capability: str) -> tuple[str, ModelRegistryEntry]:
        for model_id, entry in self.models.items():
            if capability in entry.capabilities:
                return model_id, entry
        raise KeyError(f"Unknown capability: {capability}")

    def routing_chain(self, capability: str) -> list[tuple[str, ModelRegistryEntry]]:
        if capability not in self.routing:
            raise KeyError(f"Unknown capability: {capability}")
        route = self.routing[capability]
        chain_ids = [route.primary, *route.fallback]
        return [(model_id, self.models[model_id]) for model_id in chain_ids]

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
