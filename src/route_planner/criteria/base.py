from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Hashable
from dataclasses import dataclass, field
from typing import Any

from route_planner.geo import haversine_m as haversine_m


@dataclass(frozen=True)
class CriteriaConfig:
    road_speeds: dict[str, float]
    default_speed: float
    congestion_levels: dict[str, float]
    default_congestion: float
    road_penalties: dict[str, float]
    default_road_penalty: float
    sinuosity_sense: str
    scenic: dict[str, Any]


@dataclass
class EnrichmentContext:
    config: CriteriaConfig
    node_xy: dict[Hashable, tuple[float, float]] = field(default_factory=dict)
    dem: Any = None
    scenic_index: Any = None


class EdgeCriterion(ABC):
    name: str = "base"
    sense: str = "min"

    @abstractmethod
    def compute(
        self,
        u: Hashable,
        v: Hashable,
        key: Hashable,
        data: dict,
        ctx: EnrichmentContext,
    ) -> float:
        raise NotImplementedError


def primary_highway(data: dict) -> str:
    highway = data.get("highway", "unclassified")
    if isinstance(highway, list):
        highway = highway[0] if highway else "unclassified"
    return str(highway)


def edge_coords(
    u: Hashable,
    v: Hashable,
    data: dict,
    ctx: EnrichmentContext,
) -> list[tuple[float, float]]:
    geom = data.get("geometry")
    if geom is not None:
        coords = [(float(x), float(y)) for x, y in geom.coords]
    else:
        coords = [ctx.node_xy[u], ctx.node_xy[v]]

    start = ctx.node_xy.get(u)
    if start is not None and coords and coords[0] != start:
        if coords[-1] == start:
            coords = list(reversed(coords))
    return coords
