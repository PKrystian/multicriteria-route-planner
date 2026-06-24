from __future__ import annotations

from collections.abc import Hashable

import networkx as nx

from route_planner.algorithms.base import VectorWeightFn, WeightFn
from route_planner.cost.weights import Weights
from route_planner.criteria.normalization import norm_attr

DISTANCE_OBJECTIVE = "distance"


def distance_weight(u: Hashable, v: Hashable, key: Hashable, edge_data: dict) -> float:
    return float(edge_data["length"])


def make_weighted_cost(weights: Weights, criteria_names: list[str]) -> WeightFn:
    norm = weights.normalized()
    strength = weights.strength
    active = [(name, norm.get(name, 0.0), norm_attr(name)) for name in criteria_names]

    def weight_fn(u: Hashable, v: Hashable, key: Hashable, data: dict) -> float:
        penalty = 0.0
        for _name, w, attr in active:
            if w:
                penalty += w * data.get(attr, 0.0)
        return float(data["length"]) * (1.0 + strength * penalty)

    return weight_fn


def make_vector_cost(objective_names: list[str]) -> VectorWeightFn:
    attrs = [
        (name, None if name == DISTANCE_OBJECTIVE else norm_attr(name))
        for name in objective_names
    ]

    def vector_fn(u: Hashable, v: Hashable, key: Hashable, data: dict) -> tuple[float, ...]:
        length = float(data["length"])
        return tuple(
            length if attr is None else length * data.get(attr, 0.0)
            for _name, attr in attrs
        )

    return vector_fn


def select_edge(
    graph: nx.MultiDiGraph,
    u: Hashable,
    v: Hashable,
    weight_fn: WeightFn,
) -> tuple[Hashable, dict]:
    best_key, best_data, best_cost = None, None, float("inf")
    for key, data in graph[u][v].items():
        cost = weight_fn(u, v, key, data)
        if cost < best_cost:
            best_key, best_data, best_cost = key, data, cost
    return best_key, best_data


def evaluate_path(
    graph: nx.MultiDiGraph,
    path: list[Hashable],
    weight_fn: WeightFn,
    criteria_names: list[str],
) -> dict[str, float]:
    metrics: dict[str, float] = {"length_m": 0.0}
    for name in criteria_names:
        metrics[name] = 0.0

    for u, v in zip(path, path[1:], strict=False):
        _key, data = select_edge(graph, u, v, weight_fn)
        if data is None:
            continue
        length = float(data["length"])
        metrics["length_m"] += length
        for name in criteria_names:
            metrics[name] += length * data.get(norm_attr(name), 0.0)
    return metrics
