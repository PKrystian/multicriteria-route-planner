from route_planner.criteria.base import (
    CriteriaConfig,
    EdgeCriterion,
    EnrichmentContext,
)
from route_planner.criteria.congestion import CongestionCriterion
from route_planner.criteria.elevation import ElevationCriterion
from route_planner.criteria.road_type import RoadTypeCriterion
from route_planner.criteria.scenic import ScenicCriterion
from route_planner.criteria.sinuosity import SinuosityCriterion
from route_planner.criteria.travel_cost import TravelCostCriterion


def default_criteria(config: CriteriaConfig) -> list[EdgeCriterion]:
    return [
        TravelCostCriterion(),
        CongestionCriterion(),
        SinuosityCriterion(sense=config.sinuosity_sense),
        ElevationCriterion(),
        RoadTypeCriterion(),
        ScenicCriterion(),
    ]


__all__ = [
    "CriteriaConfig",
    "EdgeCriterion",
    "EnrichmentContext",
    "TravelCostCriterion",
    "CongestionCriterion",
    "SinuosityCriterion",
    "ElevationCriterion",
    "RoadTypeCriterion",
    "ScenicCriterion",
    "default_criteria",
]
