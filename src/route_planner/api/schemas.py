from __future__ import annotations

from pydantic import BaseModel, Field


class Point(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class RouteRequest(BaseModel):
    source: Point
    target: Point
    algorithm: str = "dijkstra"
    weights: dict[str, float] | None = None
    strength: float | None = None
    pareto_axes: list[str] | None = None


class RouteMetrics(BaseModel):
    index: int
    n_nodes: int
    length_m: float
    runtime_ms: float
    visited_nodes: int
    total_cost: float | None = None
    per_criterion: dict[str, float] | None = None
    cost_vector: dict[str, float] | None = None


class RouteResponse(BaseModel):
    algorithm: str
    multi_objective: bool
    source_node: int
    target_node: int
    routes: list[RouteMetrics]
    geojson: dict


class AlgorithmsResponse(BaseModel):
    single_objective: list[str]
    multi_objective: list[str]


class CriteriaResponse(BaseModel):
    criteria: list[str]
    default_weights: dict[str, float]
    default_strength: float
    pareto_axes: list[str]
