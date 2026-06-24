from __future__ import annotations

import math
from collections.abc import Hashable

from route_planner.criteria.base import EdgeCriterion, EnrichmentContext, edge_coords


class ScenicIndex:
    def __init__(self, projected_geoms, transformer, scale_m: float) -> None:
        from shapely import STRtree

        self._geoms = list(projected_geoms)
        self._tree = STRtree(self._geoms) if self._geoms else None
        self._transformer = transformer
        self._scale_m = scale_m

    def score(self, lon: float, lat: float) -> float:
        if self._tree is None:
            return 0.0
        from shapely.geometry import Point

        x, y = self._transformer.transform(lon, lat)
        point = Point(x, y)
        nearest_idx = self._tree.nearest(point)
        distance = point.distance(self._geoms[nearest_idx])
        return math.exp(-distance / self._scale_m)


def build_scenic_index(
    bbox: tuple[float, float, float, float],
    scenic_config: dict,
) -> ScenicIndex | None:
    try:
        import osmnx as ox
        from pyproj import Transformer

        tags = scenic_config["tags"]
        features = ox.features_from_bbox(bbox, tags=tags)
        if features.empty:
            return None

        metric_crs = features.estimate_utm_crs()
        projected = features.to_crs(metric_crs)
        transformer = Transformer.from_crs("EPSG:4326", metric_crs, always_xy=True)

        geoms = [g for g in projected.geometry if g is not None and not g.is_empty]
        if not geoms:
            return None
        return ScenicIndex(geoms, transformer, float(scenic_config.get("scale_m", 250)))
    except Exception as exc:
        print(f"  [scenic] could not build index ({exc}); scenic score = 0")
        return None


class ScenicCriterion(EdgeCriterion):
    name = "scenic"
    sense = "max"

    def compute(
        self,
        u: Hashable,
        v: Hashable,
        key: Hashable,
        data: dict,
        ctx: EnrichmentContext,
    ) -> float:
        if ctx.scenic_index is None:
            return 0.0
        coords = edge_coords(u, v, data, ctx)
        if not coords:
            return 0.0
        lon, lat = coords[len(coords) // 2]
        return ctx.scenic_index.score(lon, lat)
