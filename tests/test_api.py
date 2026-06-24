from __future__ import annotations

import networkx as nx
import pytest
from fastapi.testclient import TestClient

from route_planner.api.main import AppState, create_app
from route_planner.config import AreaConfig
from route_planner.cost import Weights
from route_planner.criteria.normalization import norm_attr
from route_planner.geo import haversine_m

CRITERIA = ["travel"]
AXES = ["distance", "travel"]


def _fake_graph() -> nx.MultiDiGraph:
    g = nx.MultiDiGraph()
    coords = {1: (16.900, 52.400), 2: (16.905, 52.400), 3: (16.910, 52.400)}
    for n, (x, y) in coords.items():
        g.add_node(n, x=x, y=y)
    for a, b, pen in [(1, 2, 0.2), (2, 3, 0.8)]:
        length = haversine_m(*coords[a], *coords[b])
        for u, v in [(a, b), (b, a)]:
            g.add_edge(u, v, key=0, length=length, **{norm_attr("travel"): pen})
    g.graph["criteria_names"] = CRITERIA
    g.graph["crs"] = "epsg:4326"
    return g


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    app.state.app_state = AppState(
        graph=_fake_graph(),
        criteria_names=CRITERIA,
        area=AreaConfig("test", "", 52.4, 16.905, 1000, "drive"),
        default_weights=Weights({"travel": 1.0}, strength=15.0),
        pareto_axes=AXES,
    )
    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_algorithms_lists_all(client):
    data = client.get("/algorithms").json()
    assert "dijkstra" in data["single_objective"]
    assert "astar" in data["single_objective"]
    assert "mo_dijkstra" in data["multi_objective"]
    assert "namoa" in data["multi_objective"]


def test_criteria_endpoint(client):
    data = client.get("/criteria").json()
    assert data["criteria"] == CRITERIA
    assert data["default_strength"] == 15.0
    assert data["pareto_axes"] == AXES


def _route_body(algorithm: str, **extra) -> dict:
    return {
        "source": {"lat": 52.400, "lon": 16.900},
        "target": {"lat": 52.400, "lon": 16.910},
        "algorithm": algorithm,
        **extra,
    }


@pytest.mark.parametrize("algo", ["dijkstra", "astar"])
def test_route_single_objective(client, algo):
    resp = client.post("/route", json=_route_body(algo))
    assert resp.status_code == 200
    data = resp.json()
    assert data["multi_objective"] is False
    assert len(data["routes"]) == 1
    route = data["routes"][0]
    assert route["length_m"] > 0
    assert "travel" in route["per_criterion"]
    fc = data["geojson"]
    assert fc["type"] == "FeatureCollection"
    assert fc["features"][0]["geometry"]["type"] == "LineString"
    assert len(fc["features"][0]["geometry"]["coordinates"]) >= 2


def test_route_multi_objective(client):
    resp = client.post("/route", json=_route_body("mo_dijkstra"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["multi_objective"] is True
    assert len(data["routes"]) >= 1
    assert set(data["routes"][0]["cost_vector"]) == set(AXES)
    assert len(data["geojson"]["features"]) == len(data["routes"])


def test_route_weight_override(client):
    body = _route_body("dijkstra", weights={"travel": 0.0}, strength=0.0)
    resp = client.post("/route", json=body)
    assert resp.status_code == 200


def test_unknown_algorithm_400(client):
    resp = client.post("/route", json=_route_body("nope"))
    assert resp.status_code == 400


def test_unknown_criterion_400(client):
    resp = client.post("/route", json=_route_body("dijkstra", weights={"banana": 1.0}))
    assert resp.status_code == 400


def test_invalid_coordinates_422(client):
    body = _route_body("dijkstra")
    body["source"]["lat"] = 999
    assert client.post("/route", json=body).status_code == 422
