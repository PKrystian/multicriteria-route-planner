# Multi-criteria Route Planner

Personalized route planning that computes and compares alternative routes
between two points, scoring them with a configurable, weighted combination of
criteria derived from OpenStreetMap and terrain data. Built as a master's thesis
prototype with a research component comparing the effectiveness and performance
of different graph algorithms under different preference configurations.

## Quick start (Docker)

The only requirements are Docker and an OpenTopography API key (free, for the
elevation data). The key is read from `.env`:

```bash
echo "OPENTOPOGRAPHY_API_KEY=your_key_here" >> .env
docker compose up --build
```

Then open:

- map UI: http://localhost:8000/
- API docs: http://localhost:8000/docs

On the first run the container downloads the road network and OSM features for
the configured area and computes all criteria; this is cached under `data/`
(bind-mounted), so subsequent starts are fast. Stop with `docker compose down`.

## Run locally (without Docker)

Requires Python 3.11 or 3.12.

```bash
python -m venv .venv
source .venv/Scripts/activate        # Windows (Git Bash); use .venv/bin/activate on Linux/macOS
pip install -e ".[dev]"               # or: pip install -r requirements.lock for pinned versions

python scripts/download_dem.py        # once: fetch the DEM (needs OPENTOPOGRAPHY_API_KEY)
python scripts/prepare_data.py        # once: download + enrich + cache the graph
uvicorn route_planner.api.main:app    # serve the API + map at http://localhost:8000/
```

## How it works

### Criteria

Each directed edge is scored on six criteria, each normalized across the whole
graph to a `[0, 1]` penalty (0 = best, 1 = worst):

| Criterion    | Meaning                                            | Source                              |
|--------------|----------------------------------------------------|-------------------------------------|
| `travel`     | travel time per meter (inverse free-flow speed)    | highway class -> speed              |
| `congestion` | synthetic congestion level                         | highway class (swappable for real data) |
| `sinuosity`  | curviness = length / straight-line distance        | edge geometry                       |
| `elevation`  | average uphill gradient                            | DEM (SRTM 30 m, OpenTopography)     |
| `road_type`  | avoid/prefer road classes                          | highway class                       |
| `scenic`     | proximity to viewpoints, parks, water, forests     | OSM features                        |

Criteria with a "benefit" sense (e.g. `scenic`) are flipped during normalization
so that every normalized value is a comparable cost-like penalty.

### Cost model

Single-objective algorithms minimize a length-weighted penalty:

```
cost(edge) = length_m * (1 + strength * sum_i w_i * penalty_i(edge))
```

- `length_m` keeps distance as the substrate, so the cost is additive.
- `w_i` are the criterion weights (normalized to sum to 1).
- `strength` (lambda) controls how far routes may deviate from the shortest path
  to satisfy preferences. `strength = 0` gives a pure shortest-distance route.
  This is a key experimental knob for the thesis.

### Algorithms

Single-objective (one least-cost route):

- **Dijkstra** — baseline label-setting search.
- **A\*** — admissible geographic heuristic (great-circle distance to target
  times the minimum per-meter cost); same optimal cost as Dijkstra, fewer
  expanded nodes.

Multi-objective (the Pareto front of routes over configurable axes):

- **MultiObjectiveDijkstra** — Martins' label-setting algorithm (full front).
- **NAMOA\*** — heuristic multi-objective search; same front, fewer labels.

Every algorithm reports the route(s), per-criterion cost, runtime, and number of
expanded nodes.

## Configuration

| File                          | Controls                                             |
|-------------------------------|------------------------------------------------------|
| `config/area.yaml`            | study area center, radius, OSM network type          |
| `config/road_speeds.yaml`     | free-flow speed per highway class                    |
| `config/criteria.yaml`        | congestion, road-type penalties, sinuosity sense, scenic tags |
| `config/default_weights.yaml` | default criterion weights and `strength`             |
| `config/pareto.yaml`          | objective axes for multi-objective search            |

## API

| Method & path     | Purpose                                                              |
|-------------------|---------------------------------------------------------------------|
| `GET /health`     | liveness check                                                      |
| `GET /algorithms` | available single- and multi-objective algorithms                    |
| `GET /criteria`   | criteria names, default weights, strength, Pareto axes              |
| `POST /route`     | compute route(s): body has `source`, `target`, `algorithm`, optional `weights`, `strength`, `pareto_axes`; returns a GeoJSON `FeatureCollection` (one feature per route) plus per-route metrics |

## Command-line tools

```bash
python scripts/download_dem.py     # download the DEM for the configured area
python scripts/prepare_data.py     # download + enrich + cache the graph
python scripts/demo_dijkstra.py    # baseline Dijkstra route by distance
python scripts/demo_weighted.py    # weighted multi-criteria route + cost breakdown
python scripts/demo_compare.py     # Dijkstra vs A*, MO-Dijkstra vs NAMOA*
python scripts/run_benchmark.py --pairs 30 --seed 42   # research benchmark -> CSV
```

## Research analysis

`run_benchmark.py` runs all four algorithms over N reproducible random O/D pairs
and the weight profiles in `config/benchmark_profiles.yaml`, writing three CSVs to
`results/`:

- `benchmark_single.csv` — per (profile, pair, algorithm): runtime, visited nodes,
  length, total cost, per-criterion penalties (Dijkstra vs A*).
- `benchmark_multi.csv` — per (pair, algorithm): runtime, expanded labels, Pareto
  front size (MO-Dijkstra vs NAMOA*).
- `benchmark_pareto.csv` — every Pareto-optimal route's objective vector, for
  trade-off plots.

Then explore the results with the notebook (needs the `analysis` extra):

```bash
pip install -e ".[analysis]"
jupyter lab notebooks/analysis.ipynb
```

## Tests

```bash
pytest          # 42 tests, no network needed (synthetic graphs + preloaded API state)
ruff check .    # linting
```

## Project structure

```
config/                 area, weights, criteria and Pareto configuration (YAML)
data/                   cached graphs and DEM (git-ignored)
frontend/               Leaflet map UI (index.html, app.js, style.css)
src/route_planner/
  config.py             config loading and path resolution
  geo.py                geographic helpers
  data/                 graph download/cache, DEM, enrichment
  criteria/             six edge criteria + normalization
  cost/                 weights + cost functions
  algorithms/           Dijkstra, A*, MultiObjectiveDijkstra, NAMOA*
  api/                  FastAPI backend (routes, schemas, GeoJSON)
scripts/                CLI entry points
tests/                  unit and API tests
```

## Tech stack

Python 3.11+, OSMnx + NetworkX, rasterio, scikit-learn, FastAPI + Uvicorn,
Leaflet, pytest, ruff. All dependencies are free and open source.
