from __future__ import annotations

import networkx as nx
import pytest

from route_planner.cost import (
    Weights,
    evaluate_path,
    make_weighted_cost,
    select_edge,
)
from route_planner.criteria.normalization import norm_attr


def test_weights_normalize_to_one():
    w = Weights({"a": 1.0, "b": 3.0})
    assert w.normalized() == pytest.approx({"a": 0.25, "b": 0.75})


def test_weights_all_zero_stays_zero():
    w = Weights({"a": 0.0, "b": 0.0})
    assert w.normalized() == {"a": 0.0, "b": 0.0}


def test_negative_weight_rejected():
    with pytest.raises(ValueError):
        Weights({"a": -1.0})


def _graph_with_norms() -> nx.MultiDiGraph:
    g = nx.MultiDiGraph()
    g.add_edge(1, 2, key=0, length=100.0, **{norm_attr("travel"): 0.0})
    g.add_edge(2, 3, key=0, length=100.0, **{norm_attr("travel"): 1.0})
    return g


def test_weighted_cost_applies_penalty_to_length():
    g = _graph_with_norms()
    weight_fn = make_weighted_cost(Weights({"travel": 1.0}, strength=1.0), ["travel"])
    assert weight_fn(1, 2, 0, g[1][2][0]) == pytest.approx(100.0)
    assert weight_fn(2, 3, 0, g[2][3][0]) == pytest.approx(200.0)


def test_strength_scales_penalty():
    g = _graph_with_norms()
    weight_fn = make_weighted_cost(Weights({"travel": 1.0}, strength=10.0), ["travel"])
    assert weight_fn(2, 3, 0, g[2][3][0]) == pytest.approx(1100.0)


def test_zero_weights_give_pure_distance():
    g = _graph_with_norms()
    weight_fn = make_weighted_cost(Weights({"travel": 0.0}), ["travel"])
    assert weight_fn(2, 3, 0, g[2][3][0]) == pytest.approx(100.0)


def test_zero_strength_gives_pure_distance():
    g = _graph_with_norms()
    weight_fn = make_weighted_cost(Weights({"travel": 1.0}, strength=0.0), ["travel"])
    assert weight_fn(2, 3, 0, g[2][3][0]) == pytest.approx(100.0)


def test_select_edge_picks_cheapest_parallel():
    g = nx.MultiDiGraph()
    g.add_edge(1, 2, key=0, length=100.0, **{norm_attr("travel"): 1.0})
    g.add_edge(1, 2, key=1, length=100.0, **{norm_attr("travel"): 0.0})
    weight_fn = make_weighted_cost(Weights({"travel": 1.0}), ["travel"])
    key, data = select_edge(g, 1, 2, weight_fn)
    assert key == 1


def test_evaluate_path_breaks_down_cost():
    g = _graph_with_norms()
    weight_fn = make_weighted_cost(Weights({"travel": 1.0}), ["travel"])
    metrics = evaluate_path(g, [1, 2, 3], weight_fn, ["travel"])
    assert metrics["length_m"] == pytest.approx(200.0)
    assert metrics["travel"] == pytest.approx(100.0)
