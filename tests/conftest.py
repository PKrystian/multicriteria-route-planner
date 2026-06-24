from __future__ import annotations

import networkx as nx
import pytest


@pytest.fixture
def toy_graph() -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    edges = [
        (1, 2, 10.0),
        (2, 3, 5.0),
        (1, 3, 20.0),
        (3, 4, 2.0),
        (2, 4, 15.0),
    ]
    for u, v, length in edges:
        graph.add_edge(u, v, key=0, length=length)
        graph.add_edge(v, u, key=0, length=length)
    return graph
