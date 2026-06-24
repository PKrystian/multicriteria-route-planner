from __future__ import annotations

from collections.abc import Hashable

import networkx as nx
from fastapi import APIRouter, HTTPException, Request

from route_planner.algorithms import MULTI_OBJECTIVE, SINGLE_OBJECTIVE
from route_planner.api.geojson import feature_collection, route_feature
from route_planner.api.schemas import (
    AlgorithmsResponse,
    CriteriaResponse,
    RouteMetrics,
    RouteRequest,
    RouteResponse,
)
from route_planner.cost import (
    Weights,
    evaluate_path,
    make_vector_cost,
    make_weighted_cost,
)
from route_planner.data.graph_loader import nearest_node

router = APIRouter()


def _state(request: Request):
    state = getattr(request.app.state, "app_state", None)
    if state is None:
        raise HTTPException(status_code=503, detail="Graph not loaded yet.")
    return state


def _path_length_m(graph: nx.MultiDiGraph, path: list[Hashable]) -> float:
    total = 0.0
    for u, v in zip(path, path[1:], strict=False):
        total += min(float(d["length"]) for d in graph[u][v].values())
    return total


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/algorithms", response_model=AlgorithmsResponse)
def algorithms() -> AlgorithmsResponse:
    return AlgorithmsResponse(
        single_objective=sorted(SINGLE_OBJECTIVE),
        multi_objective=sorted(MULTI_OBJECTIVE),
    )


@router.get("/criteria", response_model=CriteriaResponse)
def criteria(request: Request) -> CriteriaResponse:
    state = _state(request)
    return CriteriaResponse(
        criteria=state.criteria_names,
        default_weights=state.default_weights.values,
        default_strength=state.default_weights.strength,
        pareto_axes=state.pareto_axes,
    )


@router.post("/route", response_model=RouteResponse)
def route(request: Request, body: RouteRequest) -> RouteResponse:
    state = _state(request)
    graph = state.graph

    is_single = body.algorithm in SINGLE_OBJECTIVE
    is_multi = body.algorithm in MULTI_OBJECTIVE
    if not (is_single or is_multi):
        raise HTTPException(
            status_code=400,
            detail=f"Unknown algorithm '{body.algorithm}'. "
            f"Single: {sorted(SINGLE_OBJECTIVE)}; multi: {sorted(MULTI_OBJECTIVE)}.",
        )

    source = nearest_node(graph, body.source.lat, body.source.lon)
    target = nearest_node(graph, body.target.lat, body.target.lon)

    if is_single:
        return _route_single(graph, state, body, source, target)
    return _route_multi(graph, state, body, source, target)


def _route_single(graph, state, body, source, target) -> RouteResponse:
    values = dict(state.default_weights.values)
    if body.weights:
        unknown = set(body.weights) - set(values)
        if unknown:
            raise HTTPException(status_code=400, detail=f"Unknown criteria: {sorted(unknown)}")
        values.update(body.weights)
    strength = body.strength if body.strength is not None else state.default_weights.strength
    weights = Weights(values, strength=strength)

    weight_fn = make_weighted_cost(weights, state.criteria_names)
    result = SINGLE_OBJECTIVE[body.algorithm]().find_route(graph, source, target, weight_fn)
    if not result.found:
        raise HTTPException(status_code=404, detail="No route found.")

    per_criterion = evaluate_path(graph, result.path, weight_fn, state.criteria_names)
    metrics = RouteMetrics(
        index=0,
        n_nodes=len(result.path),
        length_m=per_criterion["length_m"],
        runtime_ms=result.runtime_seconds * 1000,
        visited_nodes=result.visited_nodes,
        total_cost=result.total_cost,
        per_criterion={k: v for k, v in per_criterion.items() if k != "length_m"},
    )
    feature = route_feature(graph, result.path, metrics.model_dump())

    return RouteResponse(
        algorithm=body.algorithm,
        multi_objective=False,
        source_node=source,
        target_node=target,
        routes=[metrics],
        geojson=feature_collection([feature]),
    )


def _route_multi(graph, state, body, source, target) -> RouteResponse:
    axes = body.pareto_axes or state.pareto_axes
    vector_fn = make_vector_cost(axes)
    res = MULTI_OBJECTIVE[body.algorithm]().find_routes(
        graph, source, target, vector_fn, len(axes), axes
    )
    if not res.found:
        raise HTTPException(status_code=404, detail="No route found.")

    routes: list[RouteMetrics] = []
    features: list[dict] = []
    for i, pr in enumerate(res.routes):
        cost_vector = dict(zip(axes, pr.cost_vector, strict=True))
        metrics = RouteMetrics(
            index=i,
            n_nodes=len(pr.path),
            length_m=_path_length_m(graph, pr.path),
            runtime_ms=res.runtime_seconds * 1000,
            visited_nodes=res.visited_nodes,
            cost_vector=cost_vector,
        )
        routes.append(metrics)
        features.append(route_feature(graph, pr.path, metrics.model_dump()))

    return RouteResponse(
        algorithm=body.algorithm,
        multi_objective=True,
        source_node=source,
        target_node=target,
        routes=routes,
        geojson=feature_collection(features),
    )
