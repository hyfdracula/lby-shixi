"""NDVI 长期趋势分析 (70%保底任务):
逐年均值数据立方体 -> 逐像元 Sen+MK -> 5级分类 -> 按植被类型统计 -> 出图。
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

from . import viz
from .preprocess import load_stack, yearly_mean
from .utils import (
    VEG_LABELS,
    by_veg_stats,
    load_lc_aligned,
    sen_mk_cube,
    write_single_band,
    years_in_range,
)

logger = logging.getLogger(__name__)

TREND_LEVELS = {1: "显著退化", 2: "轻微退化", 3: "稳定不变", 4: "轻微改善", 5: "显著改善"}


def build_yearly_mean_cube(cfg: dict[str, Any], years: list[int]):
    base = Path(cfg["paths"]["data"]) / "ndvi_smoothed"
    frames, prof = [], None
    for y in years:
        arr, prof = load_stack(str(base / f"{y}.tif"))
        frames.append(yearly_mean(arr))
    return np.stack(frames, axis=0), prof


def classify_ndvi(slope: np.ndarray, z: np.ndarray, slope_thr: float, z_crit: float) -> np.ndarray:
    out = np.zeros(slope.shape, dtype=np.int8)
    az = np.abs(z)
    deg = slope < -slope_thr
    imp = slope > slope_thr
    sig = az >= z_crit
    out[deg & sig] = 1
    out[deg & ~sig] = 2
    out[~deg & ~imp] = 3
    out[imp & ~sig] = 4
    out[imp & sig] = 5
    return out


def run_ndvi_trend(cfg: dict[str, Any]) -> dict[str, Any]:
    years = years_in_range(cfg)
    cube, prof = build_yearly_mean_cube(cfg, years)
    slope, z = sen_mk_cube(cube)
    cls = classify_ndvi(slope, z, cfg["trend"]["slope_threshold"], cfg["trend"]["z_critical"])

    out = Path(cfg["paths"]["outputs"]) / "ndvi_trend"
    out.mkdir(parents=True, exist_ok=True)
    write_single_band(cls, str(out / "trend_class.tif"), prof, dtype="int8", nodata=0)
    write_single_band(slope, str(out / "sen_slope.tif"), prof, dtype="float32", nodata=np.nan)

    region_mean = np.array([np.nanmean(cube[k]) for k in range(len(years))])
    viz.plot_yearly_trend(years, region_mean, "区域年均 NDVI 年际变化", str(out / "ndvi_yearly.png"))

    viz.plot_spatial_class(cls, TREND_LEVELS, "NDVI 趋势空间分布", str(out / "trend_spatial.png"))
    valid = cls[cls > 0]
    vals, cnts = np.unique(valid, return_counts=True)
    viz.plot_pie_ratios(
        cnts / cnts.sum(), [TREND_LEVELS[v] for v in vals], "NDVI 趋势面积占比", str(out / "trend_pie.png")
    )

    # LC 重采样对齐到 NDVI 趋势 grid (大区域 NDVI/LC 分辨率可能不一致)
    lc_arr = load_lc_aligned(str(Path(cfg["paths"]["data"]) / "lc" / "lc_reclass.tif"), cls.shape)
    stats = by_veg_stats(cls, lc_arr, TREND_LEVELS)
    logger.info("NDVI趋势 按植被类型: %s", stats)

    veg_names = list(VEG_LABELS.values())
    slopes_by_veg = [
        float(np.nanmean(slope[lc_arr == v])) if (lc_arr == v).any() else 0.0 for v in VEG_LABELS
    ]
    viz.plot_sen_slopes(veg_names, slopes_by_veg, "不同植被 NDVI Sen 斜率", str(out / "sen_by_veg.png"))

    return {"class_tif": str(out / "trend_class.tif"), "region_mean_slope": float(np.nanmean(slope)), "stats": stats}
