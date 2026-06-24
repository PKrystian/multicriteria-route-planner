from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Hashable, Iterable
from dataclasses import dataclass, field

import networkx as nx

WeightFn = Callable[[Hashable, Hashable, Hashable, dict], float]

VectorWeightFn = Callable[[Hashable, Hashable, Hashable, dict], tuple[float, ...]]


@dataclass
class AlgorithmResult:
    path: list[Hashable]
    total_cost: float
    per_criterion_cost: dict[str, float] = field(default_factory=dict)
    runtime_seconds: float = 0.0
    visited_nodes: int = 0
    found: bool = True


class RouteAlgorithm(ABC):
    name: str = "base"

    @abstractmethod
    def find_route(
        self,
        graph: nx.MultiDiGraph,
        source: Hashable,
        target: Hashable,
        weight_fn: WeightFn,
    ) -> AlgorithmResult:
        raise NotImplementedError


def dominates(a: tuple[float, ...], b: tuple[float, ...]) -> bool:
    no_worse = all(x <= y for x, y in zip(a, b, strict=True))
    strictly_better = any(x < y for x, y in zip(a, b, strict=True))
    return no_worse and strictly_better


def is_dominated(vec: tuple[float, ...], others: Iterable[tuple[float, ...]]) -> bool:
    for other in others:
        if other == vec or dominates(other, vec):
            return True
    return False


@dataclass
class ParetoRoute:
    path: list[Hashable]
    cost_vector: tuple[float, ...]


@dataclass
class MultiObjectiveResult:
    routes: list[ParetoRoute]
    objective_names: list[str]
    runtime_seconds: float = 0.0
    visited_nodes: int = 0

    @property
    def found(self) -> bool:
        return bool(self.routes)


class MultiObjectiveAlgorithm(ABC):
    name: str = "base-mo"

    @abstractmethod
    def find_routes(
        self,
        graph: nx.MultiDiGraph,
        source: Hashable,
        target: Hashable,
        vector_fn: VectorWeightFn,
        n_objectives: int,
        objective_names: list[str] | None = None,
    ) -> MultiObjectiveResult:
        raise NotImplementedError


def reconstruct_path(
    predecessors: dict[Hashable, Hashable],
    source: Hashable,
    target: Hashable,
) -> list[Hashable]:
    if target not in predecessors and source != target:
        return []
    path = [target]
    while path[-1] != source:
        path.append(predecessors[path[-1]])
    path.reverse()
    return path


def min_edge_weight(
    graph: nx.MultiDiGraph,
    u: Hashable,
    v: Hashable,
    weight_fn: WeightFn,
) -> float:
    best = float("inf")
    for key, data in graph[u][v].items():
        best = min(best, weight_fn(u, v, key, data))
    return best
