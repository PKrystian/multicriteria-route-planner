from __future__ import annotations

import os
import sys

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

import requests

from route_planner.config import load_area_config
from route_planner.data.dem_loader import dem_path

API_URL = "https://portal.opentopography.org/API/globaldem"
DEM_TYPE = "SRTMGL1"


def main() -> None:
    api_key = os.environ.get("OPENTOPOGRAPHY_API_KEY")
    if not api_key:
        sys.exit("OPENTOPOGRAPHY_API_KEY is not set (see .env.example).")

    area = load_area_config()
    west, south, east, north = area.bbox()
    out_path = dem_path()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {DEM_TYPE} DEM for bbox W={west:.4f} S={south:.4f} "
          f"E={east:.4f} N={north:.4f}")
    params = {
        "demtype": DEM_TYPE,
        "west": west,
        "south": south,
        "east": east,
        "north": north,
        "outputFormat": "GTiff",
        "API_Key": api_key,
    }
    response = requests.get(API_URL, params=params, timeout=120)
    response.raise_for_status()

    with open(out_path, "wb") as fh:
        fh.write(response.content)
    print(f"Saved DEM to {out_path} ({len(response.content) / 1024:.0f} KiB)")


if __name__ == "__main__":
    main()
