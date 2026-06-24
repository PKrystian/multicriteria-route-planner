from __future__ import annotations

import pickle
from pathlib import Path

import networkx as nx

from route_planner.config import (
    AreaConfig,
    graph_cache_dir,
    load_area_config,
    load_criteria_config,
)
from route_planner.criteria import default_criteria
from route_planner.criteria.base import CriteriaConfig, EdgeCriterion, EnrichmentContext
from route_planner.criteria.normalization import normalize_graph, raw_attr
from route_planner.criteria.scenic import build_scenic_index
from route_planner.data.dem_loader import open_dem
from route_planner.data.graph_loader import get_graph


def build_context(
    graph: nx.MultiDiGraph,
    area: AreaConfig,
    criteria_config: CriteriaConfig,
    *,
    use_dem: bool = True,
    use_scenic: bool = True,
) -> EnrichmentContext:
    node_xy = {n: (float(d["x"]), float(d["y"])) for n, d in graph.nodes(data=True)}

    dem = open_dem() if use_dem else None
    if use_dem and dem is None:
        print("  [elevation] no DEM file found; elevation gradient = 0")

    scenic_index = (
        build_scenic_index(area.bbox(), criteria_config.scenic) if use_scenic else None
    )

    return EnrichmentContext(
        config=criteria_config,
        node_xy=node_xy,
        dem=dem,
        scenic_index=scenic_index,
    )


def enrich_graph(
    graph: nx.MultiDiGraph,
    *,
    area: AreaConfig | None = None,
    criteria_config: CriteriaConfig | None = None,
    criteria: list[EdgeCriterion] | None = None,
    use_dem: bool = True,
    use_scenic: bool = True,
) -> nx.MultiDiGraph:
    area = area or load_area_config()
    criteria_config = criteria_config or load_criteria_config()
    criteria = criteria or default_criteria(criteria_config)
    ctx = build_context(
        graph, area, criteria_config, use_dem=use_dem, use_scenic=use_scenic
    )

    for u, v, key, data in graph.edges(keys=True, data=True):
        for crit in criteria:
            data[raw_attr(crit.name)] = crit.compute(u, v, key, data, ctx)

    normalize_graph(graph, criteria)
    graph.graph["enriched"] = True

    if ctx.dem is not None:
        ctx.dem.close()
    return graph


def enriched_cache_path(area: AreaConfig, cache_dir: Path) -> Path:
    return cache_dir / f"{area.name}_{area.network_type}_{area.dist_m}m_enriched.pkl"


def get_enriched_graph(
    area: AreaConfig | None = None,
    *,
    cache_dir: Path | None = None,
    force: bool = False,
    **enrich_kwargs,
) -> nx.MultiDiGraph:
    area = area or load_area_config()
    cache_dir = cache_dir or graph_cache_dir()
    path = enriched_cache_path(area, cache_dir)

    if path.exists() and not force:
        with open(path, "rb") as fh:
            return pickle.load(fh)

    graph = get_graph(area, cache_dir=cache_dir)
    enrich_graph(graph, area=area, **enrich_kwargs)
    with open(path, "wb") as fh:
        pickle.dump(graph, fh)
    return graph
