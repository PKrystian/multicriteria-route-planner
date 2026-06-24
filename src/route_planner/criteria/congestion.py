from __future__ import annotations

from collections.abc import Hashable

from route_planner.criteria.base import EdgeCriterion, EnrichmentContext, primary_highway


class CongestionCriterion(EdgeCriterion):
    name = "congestion"
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
        return ctx.config.congestion_levels.get(highway, ctx.config.default_congestion)
