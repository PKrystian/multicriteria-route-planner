from __future__ import annotations

import heapq
import itertools
import time
from collections.abc import Hashable

import networkx as nx

from route_planner.algorithms.base import (
    AlgorithmResult,
    RouteAlgorithm,
    WeightFn,
    min_edge_weight,
    reconstruct_path,
)
from route_planner.geo import haversine_m


def min_cost_per_meter(graph: nx.MultiDiGraph, weight_fn: WeightFn) -> float:
    best = float("inf")
    for u, v, key, data in graph.edges(keys=True, data=True):
        length = float(data.get("length", 0.0))
        if length <= 0:
            continue
        best = min(best, weight_fn(u, v, key, data) / length)
    return best if best != float("inf") else 0.0


class AStar(RouteAlgorithm):
    name = "astar"

    def __init__(self, cost_per_meter: float | None = None) -> None:
        self._cost_per_meter = cost_per_meter

    def find_route(
        self,
        graph: nx.MultiDiGraph,
        source: Hashable,
        target: Hashable,
        weight_fn: WeightFn,
    ) -> AlgorithmResult:
        factor = (
            self._cost_per_meter
            if self._cost_per_meter is not None
            else min_cost_per_meter(graph, weight_fn)
        )

        start_time = time.perf_counter()

        tx, ty = graph.nodes[target]["x"], graph.nodes[target]["y"]

        def h(node: Hashable) -> float:
            nx_, ny_ = graph.nodes[node]["x"], graph.nodes[node]["y"]
            return haversine_m(nx_, ny_, tx, ty) * factor

        g_score: dict[Hashable, float] = {source: 0.0}
        predecessors: dict[Hashable, Hashable] = {}
        settled: set[Hashable] = set()
        counter = itertools.count()
        heap: list[tuple[float, int, Hashable]] = [(h(source), next(counter), source)]
        visited_nodes = 0

        while heap:
            _f, _, u = heapq.heappop(heap)
            if u in settled:
                continue
            settled.add(u)
            visited_nodes += 1

            if u == target:
                break

            gu = g_score[u]
            for v in graph[u]:
                if v in settled:
                    continue
                tentative = gu + min_edge_weight(graph, u, v, weight_fn)
                if tentative < g_score.get(v, float("inf")):
                    g_score[v] = tentative
                    predecessors[v] = u
                    heapq.heappush(heap, (tentative + h(v), next(counter), v))

        runtime = time.perf_counter() - start_time
        found = target in settled

        return AlgorithmResult(
            path=reconstruct_path(predecessors, source, target) if found else [],
            total_cost=g_score.get(target, float("inf")) if found else float("inf"),
            runtime_seconds=runtime,
            visited_nodes=visited_nodes,
            found=found,
        )
