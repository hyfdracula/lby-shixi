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
VEG_NAME_ZH: dict[str, str] = {
    "forest": "森林",
    "grassland": "草地",
    "cropland": "农田",
    "wetland": "湿地",
    "shrub": "灌丛",
    "barren": "裸地",
    "urban": "城市",
}
NON_VEG_KEYS = {"non_veg", "nonveg", "water", "snow", "ice", "snow_ice", "exclude", "excluded"}


def _iter_veg_items(veg_map: dict[str, list[int]]):
    for name, ids in veg_map.items():
        if name in NON_VEG_KEYS:
            continue
        yield name, ids


def veg_labels_from_map(veg_map: dict[str, list[int]] | None) -> dict[int, str]:
    if not veg_map:
        return VEG_LABELS.copy()
    return {idx: VEG_NAME_ZH.get(name, name) for idx, (name, _ids) in enumerate(_iter_veg_items(veg_map), start=1)}


def veg_labels_from_config(cfg: dict[str, Any]) -> dict[int, str]:
    return veg_labels_from_map(cfg.get("veg_reclass") or {})


def by_veg_enabled(cfg: dict[str, Any]) -> bool:
    """是否按植被分类出图。true=需 lc(默认); false=只全区整体, 不下 lc/不按植被(不分类模式)。"""
    return bool((cfg.get("analysis") or {}).get("by_veg", True))


def load_config(config_path: str = "config.yaml") -> dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dirs(cfg: dict[str, Any]) -> None:
    for p in (cfg["paths"]["data"], cfg["paths"]["outputs"], cfg["paths"]["report"]):
        Path(p).mkdir(parents=True, exist_ok=True)


def clean_raster_profile(profile: dict[str, Any]) -> dict[str, Any]:
    """Return a write-safe rasterio profile copied from an existing dataset."""
    out = profile.copy()
    if not out.get("tiled", False):
        out.pop("blockxsize", None)
        out.pop("blockysize", None)
    return out


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
    p = clean_raster_profile(prof)
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
    out = np.zeros(lc_arr.shape, dtype=np.int8)
    for i, (_name, ids) in enumerate(_iter_veg_items(veg_map), start=1):
        out[np.isin(lc_arr, ids)] = i  # 按 veg_map 顺序编码 1,2,...; 未映射/非植被保持 0 背景
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
            ts = np.nan_to_num(ts, nan=np.nanmean(ts))  # 已知局限: nanmean填部分NaN会引入空间自相关伪信号; 严格可改时空插值(但 pymannkendall 不接受 NaN, 需先填)
            if np.std(ts) == 0:
                continue
            r = mk.original_test(ts)
            slope[i, j] = r.slope
            z[i, j] = 0.0 if r.z is None else r.z
    return slope, z


def linear_trend_cube(cube: np.ndarray, years: list[int]) -> tuple[np.ndarray, np.ndarray]:
    """逐像元最小二乘线性回归斜率 + t 统计量(大 n 近似 z, 供 classify 用)。"""
    from tqdm import tqdm

    H, W = cube.shape[1], cube.shape[2]
    slope = np.full((H, W), np.nan, dtype=np.float32)
    z = np.full((H, W), np.nan, dtype=np.float32)
    for i in tqdm(range(H), desc="线性趋势", unit="row"):
        for j in range(W):
            ts = cube[:, i, j].astype(float)
            mask = ~np.isnan(ts)
            if mask.sum() < 3:
                continue
            xv, yv = np.asarray(years, dtype=float)[mask], ts[mask]
            xvm = xv - xv.mean()
            den = (xvm ** 2).sum()
            if den == 0:
                continue
            b = (xvm * yv).sum() / den  # 斜率
            r_num = (xvm * (yv - yv.mean())).sum()
            r_den = np.sqrt(den * ((yv - yv.mean()) ** 2).sum())
            r = r_num / r_den if r_den > 0 else 0.0
            n = mask.sum()
            t = r * np.sqrt((n - 2) / max(1 - r ** 2, 1e-12))  # t ≈ z (大 n)
            slope[i, j] = b
            z[i, j] = t
    return slope, z


def trend_cube(cube: np.ndarray, years: list[int], method: str = "sen_mk") -> tuple[np.ndarray, np.ndarray]:
    """趋势分析分发: sen_mk(默认, Sen+MK) / linear(最小二乘)。返回 (slope, z) 接口一致。"""
    if method == "linear":
        return linear_trend_cube(cube, years)
    return sen_mk_cube(cube)


def by_veg_stats(
    class_arr: np.ndarray,
    lc_arr: np.ndarray,
    levels: dict[int, str],
    labels: dict[int, str] | None = None,
) -> dict:
    labels = labels or VEG_LABELS
    stats: dict[str, dict[str, int]] = {}
    for v, name in labels.items():
        m = lc_arr == v
        if not m.any():
            continue
        vals, cnts = np.unique(class_arr[m], return_counts=True)
        stats[name] = {
            levels.get(int(vv), "?"): int(cc) for vv, cc in zip(vals, cnts) if vv != 0
        }
    return stats
