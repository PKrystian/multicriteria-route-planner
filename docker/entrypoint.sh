#!/usr/bin/env sh
set -e

DEM="${DEM_PATH:-data/dem/srtm_30m.tif}"

if [ -n "$OPENTOPOGRAPHY_API_KEY" ] && [ ! -f "$DEM" ]; then
    python scripts/download_dem.py || echo "DEM download failed; continuing without elevation"
fi

python scripts/prepare_data.py

exec uvicorn route_planner.api.main:app --host 0.0.0.0 --port 8000
