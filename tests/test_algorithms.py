from __future__ import annotations

import random

import networkx as nx
import pytest

from route_planner.algorithms import AStar, Dijkstra
from route_planner.cost import distance_weight
from route_planner.geo import haversine_m


def test_dijkstra_finds_known_shortest_path(toy_graph):
    result = Dijkstra().find_route(toy_graph, 1, 4, distance_weight)

    assert result.found
    assert result.path == [1, 2, 3, 4]
    assert result.total_cost == 17.0
    assert result.visited_nodes >= len(result.path)


def test_dijkstra_matches_networkx(toy_graph):
    result = Dijkstra().find_route(toy_graph, 1, 4, distance_weight)
    nx_cost = nx.shortest_path_length(toy_graph, 1, 4, weight="length")
    nx_path = nx.shortest_path(toy_graph, 1, 4, weight="length")

    assert result.total_cost == nx_cost
    assert result.path == nx_path


def test_dijkstra_trivial_same_source_target(toy_graph):
    result = Dijkstra().find_route(toy_graph, 1, 1, distance_weight)

    assert result.found
    assert result.path == [1]
    assert result.total_cost == 0.0


def test_dijkstra_no_path_when_disconnected():
    graph = nx.MultiDiGraph()
    graph.add_edge(1, 2, key=0, length=5.0)
    graph.add_node(99)

    result = Dijkstra().find_route(graph, 1, 99, distance_weight)

    assert not result.found
    assert result.path == []


@pytest.fixture
def geo_line_graph() -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    coords = {1: (16.90, 52.40), 2: (16.91, 52.40), 3: (16.92, 52.40), 4: (16.93, 52.40)}
    for node, (x, y) in coords.items():
        graph.add_node(node, x=x, y=y)

    def seg(a, b):
        return haversine_m(*coords[a], *coords[b])

    for a, b in [(1, 2), (2, 3), (3, 4)]:
        graph.add_edge(a, b, key=0, length=seg(a, b))
        graph.add_edge(b, a, key=0, length=seg(a, b))
    direct = seg(1, 2) + seg(2, 3) + seg(3, 4) + 10.0
    graph.add_edge(1, 4, key=0, length=direct)
    graph.add_edge(4, 1, key=0, length=direct)
    return graph


def test_astar_matches_dijkstra_cost_and_path(geo_line_graph):
    a = AStar().find_route(geo_line_graph, 1, 4, distance_weight)
    d = Dijkstra().find_route(geo_line_graph, 1, 4, distance_weight)

    assert a.found and d.found
    assert a.total_cost == pytest.approx(d.total_cost)
    assert a.path == [1, 2, 3, 4]


def _grid_graph(rows: int, cols: int) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    for i in range(rows):
        for j in range(cols):
            graph.add_node((i, j), x=16.9 + j * 0.002, y=52.4 + i * 0.002)

    def add(a, b):
        length = haversine_m(*(graph.nodes[a]["x"], graph.nodes[a]["y"]),
                             *(graph.nodes[b]["x"], graph.nodes[b]["y"]))
        graph.add_edge(a, b, key=0, length=length)
        graph.add_edge(b, a, key=0, length=length)

    for i in range(rows):
        for j in range(cols):
            if j + 1 < cols:
                add((i, j), (i, j + 1))
            if i + 1 < rows:
                add((i, j), (i + 1, j))
    return graph


def test_astar_equals_dijkstra_on_random_pairs():
    graph = _grid_graph(6, 6)
    nodes = list(graph.nodes)
    rng = random.Random(0)
    for _ in range(25):
        s, t = rng.choice(nodes), rng.choice(nodes)
        a = AStar().find_route(graph, s, t, distance_weight)
        d = Dijkstra().find_route(graph, s, t, distance_weight)
        assert a.found == d.found
        if d.found:
            assert a.total_cost == pytest.approx(d.total_cost)


def test_astar_equals_dijkstra_on_toy_graph(toy_graph):
    for n in toy_graph.nodes:
        toy_graph.nodes[n]["x"] = 0.0
        toy_graph.nodes[n]["y"] = 0.0
    a = AStar().find_route(toy_graph, 1, 4, distance_weight)
    assert a.path == [1, 2, 3, 4]
    assert a.total_cost == 17.0
