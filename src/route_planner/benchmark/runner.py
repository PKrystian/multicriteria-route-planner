from __future__ import annotations

import os
import random
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from route_planner.algorithms import AStar, Dijkstra, MultiObjectiveDijkstra, NAMOAStar
from route_planner.algorithms.astar import min_cost_per_meter
from route_planner.benchmark.metrics import (
    MultiRun,
    ParetoPoint,
    SingleRun,
    write_multi_csv,
    write_pareto_csv,
    write_single_csv,
)
from route_planner.config import (
    CONFIG_DIR,
    PROJECT_ROOT,
    AreaConfig,
    load_area_config,
    load_pareto_axes,
)
from route_planner.cost import (
    Weights,
    distance_weight,
    evaluate_path,
    make_vector_cost,
    make_weighted_cost,
)
from route_planner.data.graph_enrichment import get_enriched_graph
from route_planner.geo import haversine_m


@dataclass
class Profile:
    name: str
    weights: dict[str, float] = field(default_factory=dict)
    strength: float = 15.0


def load_profiles(path: Path | str | None = None) -> list[Profile]:
    path = Path(path) if path else CONFIG_DIR / "benchmark_profiles.yaml"
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return [
        Profile(
            name=p["name"],
            weights=p.get("weights", {}),
            strength=float(p.get("strength", 15.0)),
        )
        for p in data["profiles"]
    ]


def _results_dir() -> Path:
    path = Path(os.environ.get("RESULTS_DIR", PROJECT_ROOT / "results"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def sample_pairs(
    graph, n_pairs: int, seed: int, min_km: float, max_km: float
) -> list[tuple[int, int, float]]:
    rng = random.Random(seed)
    nodes = list(graph.nodes)
    pairs: list[tuple[int, int, float]] = []
    attempts = 0
    limit = n_pairs * 500
    while len(pairs) < n_pairs and attempts < limit:
        attempts += 1
        s, t = rng.choice(nodes), rng.choice(nodes)
        if s == t:
            continue
        sx, sy = graph.nodes[s]["x"], graph.nodes[s]["y"]
        tx, ty = graph.nodes[t]["x"], graph.nodes[t]["y"]
        od_km = haversine_m(sx, sy, tx, ty) / 1000.0
        if not (min_km <= od_km <= max_km):
            continue
        if Dijkstra().find_route(graph, s, t, distance_weight).found:
            pairs.append((s, t, od_km))
    return pairs


def run_benchmark(
    *,
    n_pairs: int = 20,
    seed: int = 42,
    min_km: float = 0.5,
    max_km: float = 5.0,
    profiles: list[Profile] | None = None,
    multi_axes: list[str] | None = None,
    area: AreaConfig | None = None,
    results_dir: Path | None = None,
    graph=None,
) -> dict[str, Path]:
    profiles = profiles or load_profiles()
    multi_axes = multi_axes or load_pareto_axes()
    results_dir = results_dir or _results_dir()

    if graph is None:
        graph = get_enriched_graph(area or load_area_config())
    criteria_names = graph.graph["criteria_names"]
    pairs = sample_pairs(graph, n_pairs, seed, min_km, max_km)

    single: list[SingleRun] = []
    for profile in profiles:
        weights = Weights(profile.weights, strength=profile.strength)
        weight_fn = make_weighted_cost(weights, criteria_names)
        factor = min_cost_per_meter(graph, weight_fn)
        algorithms = [Dijkstra(), AStar(cost_per_meter=factor)]
        for index, (s, t, od_km) in enumerate(pairs):
            for algo in algorithms:
                result = algo.find_route(graph, s, t, weight_fn)
                penalties = (
                    evaluate_path(graph, result.path, weight_fn, criteria_names)
                    if result.found
                    else {}
                )
                single.append(SingleRun(
                    pair=index, source=s, target=t, od_km=od_km, profile=profile.name,
                    algorithm=algo.name, found=result.found,
                    runtime_ms=result.runtime_seconds * 1000,
                    visited_nodes=result.visited_nodes,
                    length_m=penalties.get("length_m", 0.0),
                    total_cost=result.total_cost if result.found else float("inf"),
                    penalties={c: penalties.get(c, 0.0) for c in criteria_names},
                ))

    vector_fn = make_vector_cost(multi_axes)
    multi: list[MultiRun] = []
    fronts: list[ParetoPoint] = []
    for algo_cls in (MultiObjectiveDijkstra, NAMOAStar):
        for index, (s, t, od_km) in enumerate(pairs):
            result = algo_cls().find_routes(graph, s, t, vector_fn, len(multi_axes), multi_axes)
            multi.append(MultiRun(
                pair=index, source=s, target=t, od_km=od_km, algorithm=algo_cls.name,
                runtime_ms=result.runtime_seconds * 1000,
                visited_nodes=result.visited_nodes, front_size=len(result.routes),
            ))
            for route_index, route in enumerate(result.routes):
                fronts.append(ParetoPoint(
                    pair=index, algorithm=algo_cls.name, route_index=route_index,
                    n_nodes=len(route.path),
                    axes=dict(zip(multi_axes, route.cost_vector, strict=True)),
                ))

    paths = {
        "single": results_dir / "benchmark_single.csv",
        "multi": results_dir / "benchmark_multi.csv",
        "pareto": results_dir / "benchmark_pareto.csv",
    }
    write_single_csv(single, paths["single"], criteria_names)
    write_multi_csv(multi, paths["multi"])
    write_pareto_csv(fronts, paths["pareto"], multi_axes)
    return paths
