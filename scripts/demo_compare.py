from __future__ import annotations

import argparse

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from route_planner.algorithms import AStar, Dijkstra, MultiObjectiveDijkstra, NAMOAStar
from route_planner.config import load_area_config, load_pareto_axes
from route_planner.cost import (
    evaluate_path,
    load_weights,
    make_vector_cost,
    make_weighted_cost,
)
from route_planner.data.graph_enrichment import get_enriched_graph
from route_planner.data.graph_loader import nearest_node

DEFAULT_DESTINATION = (52.418, 16.943)


def parse_latlon(value: str) -> tuple[float, float]:
    lat, lon = (float(x) for x in value.split(","))
    return lat, lon


def main() -> None:
    area = load_area_config()
    parser = argparse.ArgumentParser(description="Compare routing algorithms.")
    parser.add_argument("--from", dest="origin", type=parse_latlon, default=area.center)
    parser.add_argument("--to", dest="destination", type=parse_latlon,
                        default=DEFAULT_DESTINATION)
    args = parser.parse_args()

    graph = get_enriched_graph(area)
    names = graph.graph["criteria_names"]
    source = nearest_node(graph, *args.origin)
    target = nearest_node(graph, *args.destination)

    weight_fn = make_weighted_cost(load_weights(), names)
    print("Single-objective (weighted cost):")
    print(f"  {'algorithm':12s} {'cost':>10s} {'length_m':>9s} {'visited':>8s} {'ms':>7s}")
    for algo in (Dijkstra(), AStar()):
        r = algo.find_route(graph, source, target, weight_fn)
        m = evaluate_path(graph, r.path, weight_fn, names)
        print(f"  {algo.name:12s} {r.total_cost:10.1f} {m['length_m']:9.0f} "
              f"{r.visited_nodes:8d} {r.runtime_seconds * 1000:7.1f}")

    axes = load_pareto_axes()
    vector_fn = make_vector_cost(axes)
    print(f"\nMulti-objective Pareto front, axes = {axes}:")
    for algo in (MultiObjectiveDijkstra(), NAMOAStar()):
        res = algo.find_routes(graph, source, target, vector_fn, len(axes), axes)
        print(f"  {algo.name:12s} front size={len(res.routes):3d}  "
              f"expanded={res.visited_nodes:6d}  {res.runtime_seconds * 1000:7.1f} ms")
    print(f"  axes order: {axes}")
    for route in res.routes:
        vec = "  ".join(f"{c:8.1f}" for c in route.cost_vector)
        print(f"    [{vec}]  ({len(route.path)} nodes)")


if __name__ == "__main__":
    main()
