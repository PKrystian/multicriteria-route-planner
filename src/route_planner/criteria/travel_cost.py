from __future__ import annotations

from collections.abc import Hashable

from route_planner.criteria.base import EdgeCriterion, EnrichmentContext, primary_highway


class TravelCostCriterion(EdgeCriterion):
    name = "travel"
    sense = "min"

    def compute(
        self,
        u: Hashable,
        v: Hashable,
        key: Hashable,
        data: dict,
        ctx: EnrichmentContext,
    ) -> float:
        highway = primary_highway(data)
        speed_kmh = ctx.config.road_speeds.get(highway, ctx.config.default_speed)
        speed_mps = max(speed_kmh, 1.0) / 3.6
        return 1.0 / speed_mps
