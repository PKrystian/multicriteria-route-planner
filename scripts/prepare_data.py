from __future__ import annotations

import argparse

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from route_planner.config import load_area_config
from route_planner.data.graph_enrichment import get_enriched_graph


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare and cache the enriched graph.")
    parser.add_argument("--force", action="store_true", help="Rebuild even if cached.")
    parser.add_argument("--no-dem", action="store_true", help="Skip elevation (no DEM).")
    parser.add_argument("--no-scenic", action="store_true", help="Skip scenic features.")
    args = parser.parse_args()

    area = load_area_config()
    print(f"Area: {area.name} ({area.description})")
    print(f"Center: {area.center}, radius: {area.dist_m} m, network: {area.network_type}")
    print("Building enriched graph (may download from OSM / read DEM on first run)...")

    graph = get_enriched_graph(
        area,
        force=args.force,
        use_dem=not args.no_dem,
        use_scenic=not args.no_scenic,
    )

    print(f"Done. Nodes: {graph.number_of_nodes()}, edges: {graph.number_of_edges()}")
    print("Criterion normalization (raw min..max over edges):")
    for name, meta in graph.graph.get("normalization", {}).items():
        print(f"  {name:10s} sense={meta['sense']:>3s}  "
              f"min={meta['min']:.4g}  max={meta['max']:.4g}")


if __name__ == "__main__":
    main()
