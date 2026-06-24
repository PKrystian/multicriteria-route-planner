from route_planner.algorithms.astar import AStar
from route_planner.algorithms.base import (
    AlgorithmResult,
    MultiObjectiveAlgorithm,
    MultiObjectiveResult,
    ParetoRoute,
    RouteAlgorithm,
)
from route_planner.algorithms.dijkstra import Dijkstra
from route_planner.algorithms.namoa import NAMOAStar
from route_planner.algorithms.pareto import MultiObjectiveDijkstra

SINGLE_OBJECTIVE: dict[str, type[RouteAlgorithm]] = {
    Dijkstra.name: Dijkstra,
    AStar.name: AStar,
}

MULTI_OBJECTIVE: dict[str, type[MultiObjectiveAlgorithm]] = {
    MultiObjectiveDijkstra.name: MultiObjectiveDijkstra,
    NAMOAStar.name: NAMOAStar,
}

__all__ = [
    "AlgorithmResult",
    "RouteAlgorithm",
    "Dijkstra",
    "AStar",
    "MultiObjectiveAlgorithm",
    "MultiObjectiveResult",
    "ParetoRoute",
    "MultiObjectiveDijkstra",
    "NAMOAStar",
    "SINGLE_OBJECTIVE",
    "MULTI_OBJECTIVE",
]
