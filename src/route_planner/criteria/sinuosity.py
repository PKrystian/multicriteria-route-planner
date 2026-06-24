from __future__ import annotations

from collections.abc import Hashable

from route_planner.criteria.base import (
    EdgeCriterion,
    EnrichmentContext,
    edge_coords,
    haversine_m,
)


class SinuosityCriterion(EdgeCriterion):
    name = "sinuosity"

    def __init__(self, sense: str = "min") -> None:
        self.sense = sense

    def compute(
        self,
        u: Hashable,
        v: Hashable,
        key: Hashable,
        data: dict,
        ctx: EnrichmentContext,
    ) -> float:
        coords = edge_coords(u, v, data, ctx)
        if len(coords) < 2:
            return 1.0
        (lon1, lat1), (lon2, lat2) = coords[0], coords[-1]
        straight = haversine_m(lon1, lat1, lon2, lat2)
        length = float(data["length"])
        if straight < 1.0:
            return 1.0
        return max(1.0, length / straight)
