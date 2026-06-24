from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SingleRun:
    pair: int
    source: int
    target: int
    od_km: float
    profile: str
    algorithm: str
    found: bool
    runtime_ms: float
    visited_nodes: int
    length_m: float
    total_cost: float
    penalties: dict[str, float] = field(default_factory=dict)


@dataclass
class MultiRun:
    pair: int
    source: int
    target: int
    od_km: float
    algorithm: str
    runtime_ms: float
    visited_nodes: int
    front_size: int


@dataclass
class ParetoPoint:
    pair: int
    algorithm: str
    route_index: int
    n_nodes: int
    axes: dict[str, float] = field(default_factory=dict)


def write_single_csv(records: list[SingleRun], path: Path, criteria_names: list[str]) -> None:
    fields = [
        "pair", "source", "target", "od_km", "profile", "algorithm", "found",
        "runtime_ms", "visited_nodes", "length_m", "total_cost",
    ] + [f"pen_{c}" for c in criteria_names]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for r in records:
            row = {
                "pair": r.pair, "source": r.source, "target": r.target,
                "od_km": round(r.od_km, 4), "profile": r.profile,
                "algorithm": r.algorithm, "found": r.found,
                "runtime_ms": round(r.runtime_ms, 4), "visited_nodes": r.visited_nodes,
                "length_m": round(r.length_m, 2), "total_cost": round(r.total_cost, 4),
            }
            for c in criteria_names:
                row[f"pen_{c}"] = round(r.penalties.get(c, 0.0), 4)
            writer.writerow(row)


def write_multi_csv(records: list[MultiRun], path: Path) -> None:
    fields = [
        "pair", "source", "target", "od_km", "algorithm",
        "runtime_ms", "visited_nodes", "front_size",
    ]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for r in records:
            writer.writerow({
                "pair": r.pair, "source": r.source, "target": r.target,
                "od_km": round(r.od_km, 4), "algorithm": r.algorithm,
                "runtime_ms": round(r.runtime_ms, 4), "visited_nodes": r.visited_nodes,
                "front_size": r.front_size,
            })


def write_pareto_csv(records: list[ParetoPoint], path: Path, axes: list[str]) -> None:
    fields = ["pair", "algorithm", "route_index", "n_nodes"] + axes
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for r in records:
            row = {
                "pair": r.pair, "algorithm": r.algorithm,
                "route_index": r.route_index, "n_nodes": r.n_nodes,
            }
            for a in axes:
                row[a] = round(r.axes.get(a, 0.0), 4)
            writer.writerow(row)
