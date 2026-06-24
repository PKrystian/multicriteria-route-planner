from __future__ import annotations

import networkx as nx
import pytest

from route_planner.criteria import (
    CongestionCriterion,
    ElevationCriterion,
    RoadTypeCriterion,
    ScenicCriterion,
    SinuosityCriterion,
    TravelCostCriterion,
)
from route_planner.criteria.base import CriteriaConfig, EnrichmentContext, haversine_m
from route_planner.criteria.normalization import norm_attr, normalize_graph, raw_attr


@pytest.fixture
def criteria_config() -> CriteriaConfig:
    return CriteriaConfig(
        road_speeds={"residential": 30, "motorway": 120},
        default_speed=40,
        congestion_levels={"primary": 0.6, "residential": 0.3},
        default_congestion=0.3,
        road_penalties={"motorway": 0.9, "residential": 0.15},
        default_road_penalty=0.3,
        sinuosity_sense="min",
        scenic={"scale_m": 250},
    )


@pytest.fixture
def ctx(criteria_config) -> EnrichmentContext:
    node_xy = {1: (16.900, 52.400), 2: (16.910, 52.400)}
    return EnrichmentContext(config=criteria_config, node_xy=node_xy)


def _edge(length: float, highway: str = "residential") -> dict:
    return {"length": length, "highway": highway}


def test_travel_cost_is_inverse_speed(ctx):
    crit = TravelCostCriterion()
    value = crit.compute(1, 2, 0, _edge(100, "residential"), ctx)
    assert value == pytest.approx(1.0 / (30 / 3.6), rel=1e-6)


def test_travel_cost_uses_default_speed_for_unknown_class(ctx):
    crit = TravelCostCriterion()
    value = crit.compute(1, 2, 0, _edge(100, "track"), ctx)
    assert value == pytest.approx(1.0 / (40 / 3.6), rel=1e-6)


def test_congestion_lookup(ctx):
    crit = CongestionCriterion()
    assert crit.compute(1, 2, 0, _edge(100, "residential"), ctx) == pytest.approx(0.3)
    assert crit.compute(1, 2, 0, _edge(100, "unknown"), ctx) == pytest.approx(0.3)


def test_road_type_lookup(ctx):
    crit = RoadTypeCriterion()
    assert crit.compute(1, 2, 0, _edge(100, "motorway"), ctx) == pytest.approx(0.9)


def test_sinuosity_ratio(ctx):
    straight = haversine_m(16.900, 52.400, 16.910, 52.400)
    crit = SinuosityCriterion()
    value = crit.compute(1, 2, 0, _edge(2 * straight), ctx)
    assert value == pytest.approx(2.0, rel=1e-3)


def test_sinuosity_straight_edge_is_one(ctx):
    straight = haversine_m(16.900, 52.400, 16.910, 52.400)
    crit = SinuosityCriterion()
    value = crit.compute(1, 2, 0, _edge(straight), ctx)
    assert value == pytest.approx(1.0, rel=1e-3)


def test_elevation_gradient_with_fake_dem(ctx):
    class FakeDEM:
        def sample(self, coords):
            return [100.0, 110.0]

    ctx.dem = FakeDEM()
    crit = ElevationCriterion()
    value = crit.compute(1, 2, 0, _edge(100), ctx)
    assert value == pytest.approx(10.0 / 100.0)


def test_elevation_zero_without_dem(ctx):
    crit = ElevationCriterion()
    assert crit.compute(1, 2, 0, _edge(100), ctx) == 0.0


def test_scenic_zero_without_index(ctx):
    crit = ScenicCriterion()
    assert crit.compute(1, 2, 0, _edge(100), ctx) == 0.0


def test_scenic_uses_index_score(ctx):
    class FakeIndex:
        def score(self, lon, lat):
            return 0.75

    ctx.scenic_index = FakeIndex()
    crit = ScenicCriterion()
    assert crit.compute(1, 2, 0, _edge(100), ctx) == pytest.approx(0.75)


def test_normalization_scales_and_flips_sense():
    graph = nx.MultiDiGraph()
    graph.add_edge(1, 2, key=0, **{raw_attr("c"): 0.0, raw_attr("b"): 0.0})
    graph.add_edge(2, 3, key=0, **{raw_attr("c"): 5.0, raw_attr("b"): 0.5})
    graph.add_edge(3, 4, key=0, **{raw_attr("c"): 10.0, raw_attr("b"): 1.0})

    class C:
        name, sense = "c", "min"

    class B:
        name, sense = "b", "max"

    normalize_graph(graph, [C(), B()])

    norms_c = [d[norm_attr("c")] for _, _, d in graph.edges(data=True)]
    norms_b = [d[norm_attr("b")] for _, _, d in graph.edges(data=True)]
    assert norms_c == pytest.approx([0.0, 0.5, 1.0])
    assert norms_b == pytest.approx([1.0, 0.5, 0.0])
    assert graph.graph["normalization"]["c"]["max"] == 10.0
