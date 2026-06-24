from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from route_planner.criteria.base import CriteriaConfig

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"


@dataclass(frozen=True)
class AreaConfig:
    name: str
    description: str
    lat: float
    lon: float
    dist_m: int
    network_type: str

    @property
    def center(self) -> tuple[float, float]:
        return (self.lat, self.lon)

    def bbox(self, margin_m: float = 500.0) -> tuple[float, float, float, float]:
        radius = self.dist_m + margin_m
        dlat = radius / 111_320.0
        dlon = radius / (111_320.0 * math.cos(math.radians(self.lat)))
        return (self.lon - dlon, self.lat - dlat, self.lon + dlon, self.lat + dlat)


def load_area_config(path: Path | str | None = None) -> AreaConfig:
    path = Path(path) if path is not None else CONFIG_DIR / "area.yaml"
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    center = data["center"]
    return AreaConfig(
        name=data["name"],
        description=data.get("description", ""),
        lat=float(center["lat"]),
        lon=float(center["lon"]),
        dist_m=int(data["dist_m"]),
        network_type=data["network_type"],
    )


def load_criteria_config(
    speeds_path: Path | str | None = None,
    criteria_path: Path | str | None = None,
) -> CriteriaConfig:
    from route_planner.criteria.base import CriteriaConfig

    speeds_path = Path(speeds_path) if speeds_path else CONFIG_DIR / "road_speeds.yaml"
    criteria_path = Path(criteria_path) if criteria_path else CONFIG_DIR / "criteria.yaml"

    with open(speeds_path, encoding="utf-8") as fh:
        speeds = yaml.safe_load(fh)
    with open(criteria_path, encoding="utf-8") as fh:
        crit = yaml.safe_load(fh)

    return CriteriaConfig(
        road_speeds={k: float(v) for k, v in speeds.get("speeds", {}).items()},
        default_speed=float(speeds.get("default", 40)),
        congestion_levels={k: float(v) for k, v in crit["congestion"]["levels"].items()},
        default_congestion=float(crit["congestion"]["default"]),
        road_penalties={k: float(v) for k, v in crit["road_type"]["penalties"].items()},
        default_road_penalty=float(crit["road_type"]["default"]),
        sinuosity_sense=str(crit["sinuosity"]["sense"]),
        scenic=crit["scenic"],
    )


def load_pareto_axes(path: Path | str | None = None) -> list[str]:
    path = Path(path) if path else CONFIG_DIR / "pareto.yaml"
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return [str(a) for a in data["axes"]]


def graph_cache_dir() -> Path:
    path = Path(os.environ.get("GRAPH_CACHE_DIR", PROJECT_ROOT / "data" / "cache" / "graphs"))
    path.mkdir(parents=True, exist_ok=True)
    return path
