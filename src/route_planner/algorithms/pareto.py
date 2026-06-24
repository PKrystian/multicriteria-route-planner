from __future__ import annotations

import heapq
import itertools
import time
from collections.abc import Hashable

import networkx as nx

from route_planner.algorithms.base import (
    MultiObjectiveAlgorithm,
    MultiObjectiveResult,
    ParetoRoute,
    VectorWeightFn,
    dominates,
    is_dominated,
)


class _Label:
    __slots__ = ("cost", "node", "parent")

    def __init__(self, cost: tuple[float, ...], node: Hashable, parent: _Label | None):
        self.cost = cost
        self.node = node
        self.parent = parent


def _reconstruct(label: _Label) -> list[Hashable]:
    path = []
    cur: _Label | None = label
    while cur is not None:
        path.append(cur.node)
        cur = cur.parent
    path.reverse()
    return path


def _filter_nondominated(vectors: list[tuple[float, ...]]) -> list[int]:
    keep = []
    for i, v in enumerate(vectors):
        if not any(j != i and dominates(vectors[j], v) for j in range(len(vectors))):
            keep.append(i)
    return keep


# Martins (1984), "On a multicriteria shortest path problem".
class MultiObjectiveDijkstra(MultiObjectiveAlgorithm):
    name = "mo_dijkstra"

    def find_routes(
        self,
        graph: nx.MultiDiGraph,
        source: Hashable,
        target: Hashable,
        vector_fn: VectorWeightFn,
        n_objectives: int,
        objective_names: list[str] | None = None,
    ) -> MultiObjectiveResult:
        start_time = time.perf_counter()
        names = objective_names or [f"obj{i}" for i in range(n_objectives)]

        zero = (0.0,) * n_objectives
        closed: dict[Hashable, list[tuple[float, ...]]] = {}
        target_labels: list[_Label] = []
        target_costs: list[tuple[float, ...]] = []

        counter = itertools.count()
        heap: list[tuple[tuple[float, ...], int, _Label]] = [
            (zero, next(counter), _Label(zero, source, None))
        ]
        expansions = 0

        while heap:
            cost, _, label = heapq.heappop(heap)
            node = label.node

            node_closed = closed.setdefault(node, [])
            if is_dominated(cost, node_closed):
                continue
            if is_dominated(cost, target_costs):
                continue

            node_closed.append(cost)
            expansions += 1

            if node == target:
                target_labels.append(label)
                target_costs.append(cost)
                continue

            for v in graph[node]:
                v_closed = closed.get(v, [])
                for key, data in graph[node][v].items():
                    step = vector_fn(node, v, key, data)
                    new_cost = tuple(c + s for c, s in zip(cost, step, strict=True))
                    if is_dominated(new_cost, v_closed):
                        continue
                    if is_dominated(new_cost, target_costs):
                        continue
                    heapq.heappush(
                        heap, (new_cost, next(counter), _Label(new_cost, v, label))
                    )

        keep = _filter_nondominated([lbl.cost for lbl in target_labels])
        routes = [
            ParetoRoute(path=_reconstruct(target_labels[i]), cost_vector=target_labels[i].cost)
            for i in keep
        ]
        routes.sort(key=lambda r: r.cost_vector)

        return MultiObjectiveResult(
            routes=routes,
            objective_names=names,
            runtime_seconds=time.perf_counter() - start_time,
            visited_nodes=expansions,
        )
