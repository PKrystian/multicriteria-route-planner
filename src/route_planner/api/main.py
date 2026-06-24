from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass

import networkx as nx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from route_planner.api.routes import router
from route_planner.config import PROJECT_ROOT, AreaConfig, load_area_config, load_pareto_axes
from route_planner.cost import Weights, load_weights
from route_planner.data.graph_enrichment import get_enriched_graph


@dataclass
class AppState:
    graph: nx.MultiDiGraph
    criteria_names: list[str]
    area: AreaConfig
    default_weights: Weights
    pareto_axes: list[str]


def load_state(area: AreaConfig | None = None) -> AppState:
    area = area or load_area_config()
    graph = get_enriched_graph(area)
    return AppState(
        graph=graph,
        criteria_names=list(graph.graph["criteria_names"]),
        area=area,
        default_weights=load_weights(),
        pareto_axes=load_pareto_axes(),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    if getattr(app.state, "app_state", None) is None:
        app.state.app_state = load_state()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Multi-criteria Route Planner", lifespan=lifespan)
    app.state.app_state = None
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    frontend_dir = PROJECT_ROOT / "frontend"
    if frontend_dir.exists():
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

    return app


app = create_app()
