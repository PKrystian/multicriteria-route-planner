from __future__ import annotations

from collections.abc import Hashable

import networkx as nx


def _node_xy(graph: nx.MultiDiGraph, node: Hashable) -> tuple[float, float]:
    data = graph.nodes[node]
    return (float(data["x"]), float(data["y"]))


def path_coordinates(
    graph: nx.MultiDiGraph, path: list[Hashable]
) -> list[list[float]]:
    coords: list[list[float]] = []
    for u, v in zip(path, path[1:], strict=False):
        data = min(graph[u][v].values(), key=lambda d: d.get("length", float("inf")))
        geom = data.get("geometry")
        if geom is not None:
            seg = [[float(x), float(y)] for x, y in geom.coords]
        else:
            seg = [list(_node_xy(graph, u)), list(_node_xy(graph, v))]

        start = list(_node_xy(graph, u))
        if seg and seg[0] != start and seg[-1] == start:
            seg.reverse()
        if coords and seg and coords[-1] == seg[0]:
            seg = seg[1:]
        coords.extend(seg)
    return coords


def route_feature(
    graph: nx.MultiDiGraph,
    path: list[Hashable],
    properties: dict,
) -> dict:
    return {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": path_coordinates(graph, path),
        },
        "properties": properties,
    }


def feature_collection(features: list[dict]) -> dict:
    return {"type": "FeatureCollection", "features": features}
