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
    by_veg_enabled,
    by_veg_stats,
    load_lc_aligned,
    trend_cube,
    veg_labels_from_config,
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
    method_cfg = (cfg.get("trend") or {}).get("method", "sen_mk")
    method = "sen_mk" if method_cfg == "both" else method_cfg  # both: 主跑 sen_mk, linear 另记均值
    slope, z = trend_cube(cube, years, method)
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

    # LC 重采样对齐到 NDVI 趋势 grid (大区域 NDVI/LC 分辨率可能不一致); by_veg=false 跳过
    stats: dict[str, Any] = {}
    if by_veg_enabled(cfg):
        lc_arr = load_lc_aligned(str(Path(cfg["paths"]["data"]) / "lc" / "lc_reclass.tif"), cls.shape)
        veg_labels = veg_labels_from_config(cfg)
        stats = by_veg_stats(cls, lc_arr, TREND_LEVELS, veg_labels)
        logger.info("NDVI趋势 按植被类型: %s", stats)

        # 森林 slope 健壮性修复: 像元存在但 slope 全 NaN 时, np.nanmean 会返回 NaN+RuntimeWarning,
        # 进图后画一根看不见的"0柱"误导。改为: 有效 slope 才取均值; 否则置 NaN 并在图上诚实标注
        # "样本不足"。不伪造数据 (如森林被 mask_low_ndvi/evergreen 过滤导致无有效趋势, 如实呈现)。
        veg_names = list(veg_labels.values())
        slopes_by_veg: list[float] = []
        sample_notes: dict[str, str] = {}  # 植被名 -> 备注 (供 viz 在柱顶标注)
        for v, name in veg_labels.items():
            m = lc_arr == v
            if not m.any():
                slopes_by_veg.append(0.0)
                sample_notes[name] = "lc 无此类"
                continue
            slv = slope[m]
            n_valid = int(np.isfinite(slv).sum())
            if n_valid == 0:
                slopes_by_veg.append(float("nan"))
                sample_notes[name] = "有效 slope=0"
                logger.warning("植被 %s (lc=%d): %d 像元全部无有效 Sen 斜率 (可能被 evergreen/std=0 过滤), 图中标注为样本不足",
                               name, v, int(m.sum()))
            else:
                slopes_by_veg.append(float(np.nanmean(slv)))
        viz.plot_sen_slopes(veg_names, slopes_by_veg, "不同植被 NDVI Sen 斜率",
                            str(out / "sen_by_veg.png"), sample_notes=sample_notes)
    else:
        logger.info("by_veg=false: 跳过按植被统计 (不分类模式)")

    slope_by_method = None
    if method_cfg == "both":
        # both 增强: linear 也做完整 5 级 classify + 散点对比图 + stats 扩展
        slope_lin, z_lin = trend_cube(cube, years, "linear")
        cls_lin = classify_ndvi(slope_lin, z_lin, cfg["trend"]["slope_threshold"], cfg["trend"]["z_critical"])
        write_single_band(slope_lin, str(out / "linear_slope.tif"), prof, dtype="float32", nodata=np.nan)
        write_single_band(cls_lin, str(out / "linear_trend_class.tif"), prof, dtype="int8", nodata=0)
        # 散点对比: sen_mk vs linear 逐像元斜率 + 1:1 线 + Pearson r
        viz.plot_slope_compare(slope, slope_lin, "NDVI 趋势 Sen-MK vs 线性回归 斜率一致性",
                               str(out / "slope_compare.png"),
                               xlabel="Sen-MK 斜率 (/yr)", ylabel="线性回归斜率 (/yr)")
        # stats 扩展: 两法 region_mean_slope + 关键面积占比 (显著退化 1 + 显著改善 5)
        def _ratio(c, lvl):
            v = c[c > 0]
            if v.size == 0:
                return 0.0
            uv, cnt = np.unique(v, return_counts=True)
            d = dict(zip(uv.tolist(), cnt.tolist()))
            return d.get(lvl, 0) / v.size
        slope_by_method = {
            "sen_mk": float(np.nanmean(slope)),
            "linear": float(np.nanmean(slope_lin)),
            "pearson_r": float(np.corrcoef(
                np.nan_to_num(slope, nan=0.0).ravel(),
                np.nan_to_num(slope_lin, nan=0.0).ravel(),
            )[0, 1]),
            "sen_mk_area_ratio": {
                "显著退化": _ratio(cls, 1), "显著改善": _ratio(cls, 5),
                "退化合计": _ratio(cls, 1) + _ratio(cls, 2),
                "改善合计": _ratio(cls, 4) + _ratio(cls, 5),
            },
            "linear_area_ratio": {
                "显著退化": _ratio(cls_lin, 1), "显著改善": _ratio(cls_lin, 5),
                "退化合计": _ratio(cls_lin, 1) + _ratio(cls_lin, 2),
                "改善合计": _ratio(cls_lin, 4) + _ratio(cls_lin, 5),
            },
        }
        logger.info(
            "trend.method=both: sen_mk=%.6f linear=%.6f /yr, Pearson r=%.4f; "
            "sen_mk 显著退化=%.2f%% 显著改善=%.2f%% | linear 显著退化=%.2f%% 显著改善=%.2f%%",
            slope_by_method["sen_mk"], slope_by_method["linear"], slope_by_method["pearson_r"],
            slope_by_method["sen_mk_area_ratio"]["显著退化"] * 100,
            slope_by_method["sen_mk_area_ratio"]["显著改善"] * 100,
            slope_by_method["linear_area_ratio"]["显著退化"] * 100,
            slope_by_method["linear_area_ratio"]["显著改善"] * 100,
        )
        logger.info("both: linear_trend_class.tif + slope_compare.png 已生成, 可据此论证两法一致性")

    return {"class_tif": str(out / "trend_class.tif"), "region_mean_slope": float(np.nanmean(slope)), "stats": stats, "slope_by_method": slope_by_method}
