from __future__ import annotations

import csv

import networkx as nx

from route_planner.benchmark import Profile, run_benchmark
from route_planner.criteria.normalization import norm_attr
from route_planner.geo import haversine_m


def _enriched_grid(rows: int = 4, cols: int = 4) -> nx.MultiDiGraph:
    g = nx.MultiDiGraph()
    for i in range(rows):
        for j in range(cols):
            g.add_node((i, j), x=16.9 + j * 0.003, y=52.4 + i * 0.003)

    def add(a, b):
        length = haversine_m(g.nodes[a]["x"], g.nodes[a]["y"], g.nodes[b]["x"], g.nodes[b]["y"])
        for u, v in [(a, b), (b, a)]:
            g.add_edge(u, v, key=0, length=length, **{norm_attr("travel"): 0.5})

    for i in range(rows):
        for j in range(cols):
            if j + 1 < cols:
                add((i, j), (i, j + 1))
            if i + 1 < rows:
                add((i, j), (i + 1, j))
    g.graph["criteria_names"] = ["travel"]
    return g


def test_run_benchmark_writes_csvs(tmp_path):
    graph = _enriched_grid()
    paths = run_benchmark(
        n_pairs=2,
        seed=1,
        min_km=0.0,
        max_km=100.0,
        profiles=[Profile("shortest", {}, 0.0), Profile("fast", {"travel": 1.0}, 15.0)],
        multi_axes=["distance", "travel"],
        results_dir=tmp_path,
        graph=graph,
    )

    for key in ("single", "multi", "pareto"):
        assert paths[key].exists()

    with open(paths["single"], encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert rows
    assert {"dijkstra", "astar"} == {r["algorithm"] for r in rows}
    assert "pen_travel" in rows[0]

    with open(paths["multi"], encoding="utf-8") as fh:
        multi_rows = list(csv.DictReader(fh))
    assert {"mo_dijkstra", "namoa"} == {r["algorithm"] for r in multi_rows}
