from __future__ import annotations

import heapq
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


class Dijkstra(RouteAlgorithm):
    name = "dijkstra"

    def find_route(
        self,
        graph: nx.MultiDiGraph,
        source: Hashable,
        target: Hashable,
        weight_fn: WeightFn,
    ) -> AlgorithmResult:
        start_time = time.perf_counter()

        dist: dict[Hashable, float] = {source: 0.0}
        predecessors: dict[Hashable, Hashable] = {}
        settled: set[Hashable] = set()
        heap: list[tuple[float, Hashable]] = [(0.0, source)]
        visited_nodes = 0

        while heap:
            d, u = heapq.heappop(heap)
            if u in settled:
                continue
            settled.add(u)
            visited_nodes += 1

            if u == target:
                break

            for v in graph[u]:
                if v in settled:
                    continue
                weight = min_edge_weight(graph, u, v, weight_fn)
                new_dist = d + weight
                if new_dist < dist.get(v, float("inf")):
                    dist[v] = new_dist
                    predecessors[v] = u
                    heapq.heappush(heap, (new_dist, v))

        runtime = time.perf_counter() - start_time
        found = target in settled

        return AlgorithmResult(
            path=reconstruct_path(predecessors, source, target) if found else [],
            total_cost=dist.get(target, float("inf")) if found else float("inf"),
            runtime_seconds=runtime,
            visited_nodes=visited_nodes,
            found=found,
        )
