from __future__ import annotations

import argparse

from route_planner.algorithms import Dijkstra
from route_planner.config import load_area_config
from route_planner.cost import distance_weight
from route_planner.data.graph_loader import get_graph, nearest_node

DEFAULT_DESTINATION = (52.4084, 16.9342)


def parse_latlon(value: str) -> tuple[float, float]:
    lat, lon = (float(x) for x in value.split(","))
    return lat, lon


def main() -> None:
    area = load_area_config()
    parser = argparse.ArgumentParser(description="Dijkstra route demo.")
    parser.add_argument(
        "--from",
        dest="origin",
        type=parse_latlon,
        default=area.center,
        help='Origin as "lat,lon". Defaults to the area center.',
    )
    parser.add_argument(
        "--to",
        dest="destination",
        type=parse_latlon,
        default=DEFAULT_DESTINATION,
        help='Destination as "lat,lon". Defaults to Poznan Old Market Square.',
    )
    args = parser.parse_args()

    graph = get_graph(area)
    source = nearest_node(graph, *args.origin)
    target = nearest_node(graph, *args.destination)
    print(f"Source node: {source}  Target node: {target}")

    result = Dijkstra().find_route(graph, source, target, distance_weight)

    if not result.found:
        print("No route found.")
        return

    print(f"Route found: {len(result.path)} nodes")
    print(f"Total distance: {result.total_cost:.1f} m")
    print(f"Visited nodes: {result.visited_nodes}")
    print(f"Runtime: {result.runtime_seconds * 1000:.2f} ms")


if __name__ == "__main__":
    main()
