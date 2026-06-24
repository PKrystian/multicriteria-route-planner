from __future__ import annotations

from collections.abc import Hashable

from route_planner.criteria.base import EdgeCriterion, EnrichmentContext, edge_coords


class ElevationCriterion(EdgeCriterion):
    name = "elevation"
    sense = "min"

    def compute(
        self,
        u: Hashable,
        v: Hashable,
        key: Hashable,
        data: dict,
        ctx: EnrichmentContext,
    ) -> float:
        if ctx.dem is None:
            return 0.0

        coords = edge_coords(u, v, data, ctx)
        if len(coords) < 2:
            return 0.0

        elevations = ctx.dem.sample(coords)
        climb = 0.0
        prev = None
        for elev in elevations:
            if elev is None:
                continue
            if prev is not None and elev > prev:
                climb += elev - prev
            prev = elev

        length = float(data["length"])
        if length <= 0:
            return 0.0
        return climb / length
