from __future__ import annotations

import networkx as nx
import pytest

from route_planner.algorithms import MultiObjectiveDijkstra, NAMOAStar
from route_planner.algorithms.base import dominates, is_dominated


def vector_fn(u, v, key, data):
    return data["vec"]


@pytest.fixture
def two_objective_graph() -> nx.MultiDiGraph:
    g = nx.MultiDiGraph()
    edges = {
        (1, 2): (1, 2), (2, 4): (1, 3),
        (1, 3): (2, 1), (3, 4): (3, 1),
        (1, 4): (3, 3),
        (1, 5): (2, 2), (5, 4): (2, 2),
    }
    for (u, v), vec in edges.items():
        g.add_edge(u, v, key=0, vec=vec, length=1.0)
    return g


EXPECTED_FRONT = {(2.0, 5.0), (3.0, 3.0), (5.0, 2.0)}


def _front_set(result) -> set:
    return {tuple(r.cost_vector) for r in result.routes}


def test_dominance_helpers():
    assert dominates((1, 2), (2, 3))
    assert not dominates((1, 3), (2, 2))
    assert not dominates((2, 2), (2, 2))
    assert is_dominated((3, 3), [(2, 2)])
    assert is_dominated((2, 2), [(2, 2)])
    assert not is_dominated((1, 5), [(2, 4)])


def test_mo_dijkstra_finds_expected_front(two_objective_graph):
    res = MultiObjectiveDijkstra().find_routes(two_objective_graph, 1, 4, vector_fn, 2)
    assert _front_set(res) == EXPECTED_FRONT
    assert res.visited_nodes > 0


def test_namoa_finds_expected_front(two_objective_graph):
    res = NAMOAStar().find_routes(two_objective_graph, 1, 4, vector_fn, 2)
    assert _front_set(res) == EXPECTED_FRONT


def test_mo_dijkstra_and_namoa_agree(two_objective_graph):
    a = MultiObjectiveDijkstra().find_routes(two_objective_graph, 1, 4, vector_fn, 2)
    b = NAMOAStar().find_routes(two_objective_graph, 1, 4, vector_fn, 2)
    assert _front_set(a) == _front_set(b)


def test_front_routes_are_mutually_nondominated(two_objective_graph):
    res = MultiObjectiveDijkstra().find_routes(two_objective_graph, 1, 4, vector_fn, 2)
    vecs = [tuple(r.cost_vector) for r in res.routes]
    for i, v in enumerate(vecs):
        others = [vecs[j] for j in range(len(vecs)) if j != i]
        assert not is_dominated(v, others)


def test_paths_are_valid(two_objective_graph):
    res = MultiObjectiveDijkstra().find_routes(two_objective_graph, 1, 4, vector_fn, 2)
    for route in res.routes:
        assert route.path[0] == 1
        assert route.path[-1] == 4
