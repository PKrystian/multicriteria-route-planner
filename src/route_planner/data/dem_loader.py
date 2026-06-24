from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path

from route_planner.config import PROJECT_ROOT


def dem_path() -> Path:
    return Path(os.environ.get("DEM_PATH", PROJECT_ROOT / "data" / "dem" / "srtm_30m.tif"))


class DEMSampler:
    def __init__(self, path: Path | str) -> None:
        import rasterio

        self._dataset = rasterio.open(path)
        self._nodata = self._dataset.nodata

    def sample(self, coords: Sequence[tuple[float, float]]) -> list[float | None]:
        results: list[float | None] = []
        for value in self._dataset.sample(coords):
            elev = float(value[0])
            if self._nodata is not None and elev == self._nodata:
                results.append(None)
            else:
                results.append(elev)
        return results

    def close(self) -> None:
        self._dataset.close()


def open_dem(path: Path | str | None = None) -> DEMSampler | None:
    path = Path(path) if path is not None else dem_path()
    if not path.exists():
        return None
    return DEMSampler(path)
