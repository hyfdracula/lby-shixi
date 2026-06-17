"""通用工具: 配置、目录、GeoTIFF 读写、植被重分类、逐像元 Sen-MK 趋势。"""
from __future__ import annotations

import os

# ── PROJ / GDAL 数据库冲突修复 ──
for _k in ("PROJ_LIB", "PROJ_DATA", "GDAL_DATA"):
    os.environ.pop(_k, None)
try:
    import rasterio as _rio

    _rdir = os.path.dirname(_rio.__file__)
    _pd = os.path.join(_rdir, "proj_data")
    if os.path.isdir(_pd):
        os.environ["PROJ_LIB"] = _pd
        os.environ["PROJ_DATA"] = _pd
    _gd = os.path.join(_rdir, "gdal_data")
    if os.path.isdir(_gd):
        os.environ["GDAL_DATA"] = _gd
except Exception:  # noqa: BLE001
    pass

import logging
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
import yaml

logger = logging.getLogger(__name__)

VEG_LABELS: dict[int, str] = {1: "森林", 2: "草地", 3: "农田", 4: "湿地"}


def load_config(config_path: str = "config.yaml") -> dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dirs(cfg: dict[str, Any]) -> None:
    for p in (cfg["paths"]["data"], cfg["paths"]["outputs"], cfg["paths"]["report"]):
        Path(p).mkdir(parents=True, exist_ok=True)


def years_in_range(cfg: dict[str, Any]) -> list[int]:
    s = int(str(cfg["date"]["start"])[:4])
    e = int(str(cfg["date"]["end"])[:4])
    if s > e:
        raise ValueError(f"date.start ({s}) > date.end ({e})")
    return list(range(s, e + 1))


def write_single_band(
    arr: np.ndarray, path: str, prof: dict[str, Any], dtype: str = "float32", nodata: Any = np.nan
) -> str:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    p = prof.copy()
    p.update(dtype=dtype, count=1, nodata=nodata)
    with rasterio.open(path, "w", **p) as dst:
        dst.write(np.asarray(arr, dtype=dtype), 1)
    return path


def load_tif(path: str) -> tuple[np.ndarray, dict[str, Any]]:
    with rasterio.open(path) as src:
        return src.read(1), src.profile


def load_lc_aligned(lc_path: str, target_shape: tuple[int, int]) -> np.ndarray:
    """读 LC 重分类 tif, 最近邻重采样到 target_shape (与 NDVI/趋势 grid 对齐)。

    解决大区域下载时 NDVI 与 LC 分辨率不一致 (NDVI 降采样而 LC 未降) 导致的形状不匹配。
    """
    from rasterio.enums import Resampling

    with rasterio.open(lc_path) as src:
        return src.read(1, out_shape=target_shape, resampling=Resampling.nearest)


def reclass_lc(lc_arr: np.ndarray, veg_map: dict[str, list[int]]) -> np.ndarray:
    label = {"forest": 1, "grassland": 2, "cropland": 3, "wetland": 4}
    out = np.zeros(lc_arr.shape, dtype=np.int8)
    for name, ids in veg_map.items():
        out[np.isin(lc_arr, ids)] = label[name]
    return out


def sen_mk_cube(cube: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    import pymannkendall as mk
    from tqdm import tqdm

    Y, H, W = cube.shape
    slope = np.full((H, W), np.nan, dtype=np.float32)
    z = np.full((H, W), np.nan, dtype=np.float32)
    for i in tqdm(range(H), desc="Sen-MK 趋势", unit="row"):
        for j in range(W):
            ts = cube[:, i, j].astype(float)
            if np.isnan(ts).all():
                continue
            ts = np.nan_to_num(ts, nan=np.nanmean(ts))
            if np.std(ts) == 0:
                continue
            r = mk.original_test(ts)
            slope[i, j] = r.slope
            z[i, j] = 0.0 if r.z is None else r.z
    return slope, z


def by_veg_stats(class_arr: np.ndarray, lc_arr: np.ndarray, levels: dict[int, str]) -> dict:
    stats: dict[str, dict[str, int]] = {}
    for v, name in VEG_LABELS.items():
        m = lc_arr == v
        if not m.any():
            continue
        vals, cnts = np.unique(class_arr[m], return_counts=True)
        stats[name] = {
            levels.get(int(vv), "?"): int(cc) for vv, cc in zip(vals, cnts) if vv != 0
        }
    return stats
