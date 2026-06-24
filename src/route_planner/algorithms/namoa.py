from __future__ import annotations

import heapq
import itertools
import time
from collections.abc import Callable, Hashable

import networkx as nx

from route_planner.algorithms.base import (
    MultiObjectiveAlgorithm,
    MultiObjectiveResult,
    ParetoRoute,
    VectorWeightFn,
    dominates,
    is_dominated,
)
from route_planner.algorithms.pareto import _filter_nondominated, _Label, _reconstruct
from route_planner.geo import haversine_m

VectorHeuristic = Callable[[Hashable], tuple[float, ...]]


def _min_cost_per_meter_vector(
    graph: nx.MultiDiGraph, vector_fn: VectorWeightFn, n_objectives: int
) -> tuple[float, ...]:
    best = [float("inf")] * n_objectives
    for u, v, key, data in graph.edges(keys=True, data=True):
        length = float(data.get("length", 0.0))
        if length <= 0:
            continue
        vec = vector_fn(u, v, key, data)
        for i in range(n_objectives):
            best[i] = min(best[i], vec[i] / length)
    return tuple(b if b != float("inf") else 0.0 for b in best)


def _build_default_heuristic(
    graph: nx.MultiDiGraph,
    target: Hashable,
    vector_fn: VectorWeightFn,
    n_objectives: int,
) -> VectorHeuristic:
    if "x" not in graph.nodes[target]:
        zero = (0.0,) * n_objectives
        return lambda node: zero

    factors = _min_cost_per_meter_vector(graph, vector_fn, n_objectives)
    tx, ty = graph.nodes[target]["x"], graph.nodes[target]["y"]

    def heuristic(node: Hashable) -> tuple[float, ...]:
        nx_, ny_ = graph.nodes[node]["x"], graph.nodes[node]["y"]
        dist = haversine_m(nx_, ny_, tx, ty)
        return tuple(dist * f for f in factors)

    return heuristic


# Mandow & Perez de la Cruz (2010), "Multiobjective A* search".
class NAMOAStar(MultiObjectiveAlgorithm):
    name = "namoa"

    def __init__(self, heuristic: VectorHeuristic | None = None) -> None:
        self._heuristic = heuristic

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
        h = self._heuristic or _build_default_heuristic(
            graph, target, vector_fn, n_objectives
        )

        def add(a: tuple[float, ...], b: tuple[float, ...]) -> tuple[float, ...]:
            return tuple(x + y for x, y in zip(a, b, strict=True))

        zero = (0.0,) * n_objectives
        gop: dict[Hashable, list[tuple[float, ...]]] = {source: [zero]}
        gcl: dict[Hashable, list[tuple[float, ...]]] = {}
        costs: list[tuple[float, ...]] = []
        solutions: list[_Label] = []

        counter = itertools.count()
        heap: list[tuple[tuple[float, ...], int, _Label]] = [
            (add(zero, h(source)), next(counter), _Label(zero, source, None))
        ]
        expansions = 0

        while heap:
            f, _, label = heapq.heappop(heap)
            node, g = label.node, label.cost

            if g not in gop.get(node, ()):
                continue
            if is_dominated(f, costs):
                gop[node].remove(g)
                continue

            gop[node].remove(g)
            gcl.setdefault(node, []).append(g)
            expansions += 1

            if node == target:
                costs[:] = [c for c in costs if not dominates(g, c)]
                if not is_dominated(g, costs):
                    costs.append(g)
                    solutions.append(label)
                continue

            for v in graph[node]:
                v_open = gop.get(v, [])
                v_closed = gcl.get(v, [])
                for key, data in graph[node][v].items():
                    g2 = add(g, vector_fn(node, v, key, data))
                    f2 = add(g2, h(v))
                    if is_dominated(f2, costs):
                        continue
                    if is_dominated(g2, v_closed) or is_dominated(g2, v_open):
                        continue
                    gop[v] = [c for c in v_open if not dominates(g2, c)]
                    gop[v].append(g2)
                    v_open = gop[v]
                    heapq.heappush(heap, (f2, next(counter), _Label(g2, v, label)))

        keep = _filter_nondominated([lbl.cost for lbl in solutions])
        routes = [
            ParetoRoute(path=_reconstruct(solutions[i]), cost_vector=solutions[i].cost)
            for i in keep
        ]
        routes.sort(key=lambda r: r.cost_vector)

        return MultiObjectiveResult(
            routes=routes,
            objective_names=names,
            runtime_seconds=time.perf_counter() - start_time,
            visited_nodes=expansions,
        )
