from __future__ import annotations

from pathlib import Path

import networkx as nx
import osmnx as ox

from route_planner.config import AreaConfig, graph_cache_dir, load_area_config

ox.settings.use_cache = True
ox.settings.log_console = False


def _cache_path(area: AreaConfig, cache_dir: Path) -> Path:
    filename = f"{area.name}_{area.network_type}_{area.dist_m}m.graphml"
    return cache_dir / filename


def get_graph(
    area: AreaConfig | None = None,
    *,
    cache_dir: Path | None = None,
    force_download: bool = False,
) -> nx.MultiDiGraph:
    area = area or load_area_config()
    cache_dir = cache_dir or graph_cache_dir()
    path = _cache_path(area, cache_dir)

    if path.exists() and not force_download:
        return ox.load_graphml(path)

    graph = ox.graph_from_point(
        area.center,
        dist=area.dist_m,
        network_type=area.network_type,
    )
    ox.save_graphml(graph, path)
    return graph


def nearest_node(graph: nx.MultiDiGraph, lat: float, lon: float) -> int:
    return ox.distance.nearest_nodes(graph, X=lon, Y=lat)
