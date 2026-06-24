from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import yaml

from route_planner.config import CONFIG_DIR

DEFAULT_STRENGTH = 15.0


@dataclass(frozen=True)
class Weights:
    values: dict[str, float]
    strength: float = DEFAULT_STRENGTH

    def __post_init__(self) -> None:
        for name, w in self.values.items():
            if w < 0:
                raise ValueError(f"Weight for {name!r} must be >= 0, got {w}")
        if self.strength < 0:
            raise ValueError(f"strength must be >= 0, got {self.strength}")

    def normalized(self) -> dict[str, float]:
        total = sum(self.values.values())
        if total <= 0:
            return {name: 0.0 for name in self.values}
        return {name: w / total for name, w in self.values.items()}

    @classmethod
    def from_mapping(
        cls, mapping: Mapping[str, float], strength: float = DEFAULT_STRENGTH
    ) -> Weights:
        return cls({str(k): float(v) for k, v in mapping.items()}, strength=strength)


def load_weights(path: Path | str | None = None) -> Weights:
    path = Path(path) if path else CONFIG_DIR / "default_weights.yaml"
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    strength = float(data.get("strength", DEFAULT_STRENGTH))
    return Weights.from_mapping(data["weights"], strength=strength)
