from __future__ import annotations

from collections.abc import Iterable

import networkx as nx

from route_planner.criteria.base import EdgeCriterion

RAW_PREFIX = "raw_"
NORM_PREFIX = "norm_"


def raw_attr(name: str) -> str:
    return f"{RAW_PREFIX}{name}"


def norm_attr(name: str) -> str:
    return f"{NORM_PREFIX}{name}"


def normalize_graph(graph: nx.MultiDiGraph, criteria: Iterable[EdgeCriterion]) -> None:
    criteria = list(criteria)
    meta: dict[str, dict] = {}

    for crit in criteria:
        raw_key = raw_attr(crit.name)
        values = [data[raw_key] for _, _, data in graph.edges(data=True) if raw_key in data]
        lo = min(values) if values else 0.0
        hi = max(values) if values else 0.0
        span = hi - lo
        meta[crit.name] = {"min": lo, "max": hi, "sense": crit.sense}

        norm_key = norm_attr(crit.name)
        for _, _, data in graph.edges(data=True):
            raw = data.get(raw_key, lo)
            scaled = 0.0 if span == 0 else (raw - lo) / span
            data[norm_key] = (1.0 - scaled) if crit.sense == "max" else scaled

    graph.graph["normalization"] = meta
    graph.graph["criteria_names"] = [c.name for c in criteria]
