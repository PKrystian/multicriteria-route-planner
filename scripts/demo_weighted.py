from __future__ import annotations

import argparse

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from route_planner.algorithms import Dijkstra
from route_planner.config import load_area_config
from route_planner.cost import evaluate_path, load_weights, make_weighted_cost
from route_planner.data.graph_enrichment import get_enriched_graph
from route_planner.data.graph_loader import nearest_node

DEFAULT_DESTINATION = (52.4084, 16.9342)


def parse_latlon(value: str) -> tuple[float, float]:
    lat, lon = (float(x) for x in value.split(","))
    return lat, lon


def main() -> None:
    area = load_area_config()
    parser = argparse.ArgumentParser(description="Weighted multi-criteria route demo.")
    parser.add_argument("--from", dest="origin", type=parse_latlon, default=area.center)
    parser.add_argument("--to", dest="destination", type=parse_latlon,
                        default=DEFAULT_DESTINATION)
    args = parser.parse_args()

    graph = get_enriched_graph(area)
    criteria_names = graph.graph["criteria_names"]
    weights = load_weights()
    print("Weights (normalized):")
    for name, w in weights.normalized().items():
        print(f"  {name:10s} {w:.3f}")

    weight_fn = make_weighted_cost(weights, criteria_names)
    source = nearest_node(graph, *args.origin)
    target = nearest_node(graph, *args.destination)

    result = Dijkstra().find_route(graph, source, target, weight_fn)
    if not result.found:
        print("No route found.")
        return

    metrics = evaluate_path(graph, result.path, weight_fn, criteria_names)
    print(f"\nRoute: {len(result.path)} nodes, length {metrics['length_m']:.0f} m")
    print(f"Weighted cost: {result.total_cost:.1f}  "
          f"(visited {result.visited_nodes} nodes, {result.runtime_seconds * 1000:.1f} ms)")
    print("Per-criterion penalty-distance (length_m * normalized penalty):")
    for name in criteria_names:
        print(f"  {name:10s} {metrics[name]:.1f}")


if __name__ == "__main__":
    main()
