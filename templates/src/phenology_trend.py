"""物候序列(SOS/EOS/Peak)趋势分析 (100%任务):
逐像元 Sen+MK -> 提前/延迟 5级 -> 按植被类型统计 -> 出图。

物候语义: slope>0 = 延迟(变晚), slope<0 = 提前(变早)。
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

from . import viz
from .utils import by_veg_enabled, by_veg_stats, load_lc_aligned, trend_cube, write_single_band

logger = logging.getLogger(__name__)

PHENO_LEVELS = {1: "显著延迟", 2: "轻微延迟", 3: "无显著变化", 4: "轻微提前", 5: "显著提前"}


def classify_pheno(slope: np.ndarray, z: np.ndarray, slope_thr: float, z_crit: float) -> np.ndarray:
    out = np.zeros(slope.shape, dtype=np.int8)
    az = np.abs(z)
    late = slope > slope_thr
    early = slope < -slope_thr
    sig = az >= z_crit
    out[late & sig] = 1
    out[late & ~sig] = 2
    out[~late & ~early] = 3
    out[early & ~sig] = 4
    out[early & sig] = 5
    return out


def run_phenology_trend(cfg: dict[str, Any], pheno_result: dict[str, Any]) -> dict[str, Any]:
    slope_thr = (cfg.get("trend") or {}).get("pheno_slope_threshold", 0.5)  # 物候 DOY/yr 独立阈值(NDVI 的 0.0005 量级不同, 物候斜率 0.1-2 DOY/yr)
    z_crit = cfg["trend"]["z_critical"]
    out = Path(cfg["paths"]["outputs"]) / "phenology_trend"
    out.mkdir(parents=True, exist_ok=True)
    grid_shape = pheno_result["sos_stack"].shape[1:]  # (H, W), 与物候 grid 对齐
    years = pheno_result.get("years") or list(range(pheno_result["sos_stack"].shape[0]))
    method_cfg = (cfg.get("trend") or {}).get("method", "sen_mk")
    method = "sen_mk" if method_cfg == "both" else method_cfg  # both: 主跑 sen_mk, linear 另记均值
    do_veg = by_veg_enabled(cfg)
    lc_arr = load_lc_aligned(str(Path(cfg["paths"]["data"]) / "lc" / "lc_reclass.tif"), grid_shape) if do_veg else None
    prof = pheno_result["profile"]
    summary: dict[str, dict] = {}

    for name, stack in [
        ("SOS", pheno_result["sos_stack"]),
        ("EOS", pheno_result["eos_stack"]),
        ("Peak", pheno_result["peak_stack"]),
    ]:
        slope, z = trend_cube(stack.astype(np.float32), years, method)
        cls = classify_pheno(slope, z, slope_thr, z_crit)
        write_single_band(cls, str(out / f"{name}_trend_class.tif"), prof, dtype="int8", nodata=0)
        viz.plot_spatial_class(cls, PHENO_LEVELS, f"{name} 趋势空间分布", str(out / f"{name}_spatial.png"))
        valid = cls[cls > 0]
        if valid.size:
            vals, cnts = np.unique(valid, return_counts=True)
            viz.plot_pie_ratios(
                cnts / cnts.sum(),
                [PHENO_LEVELS[v] for v in vals],
                f"{name} 趋势面积占比",
                str(out / f"{name}_pie.png"),
            )
        if do_veg:
            veg_stats = by_veg_stats(cls, lc_arr, PHENO_LEVELS)
            summary[name] = veg_stats
            # 按植被趋势等级堆叠柱状图(不同植被 SOS/EOS/Peak 趋势占比)
            veg_names = list(veg_stats.keys())
            order = ["显著延迟", "轻微延迟", "无显著变化", "轻微提前", "显著提前"]
            raw_st = {lv: [veg_stats[vn].get(lv, 0) for vn in veg_names] for lv in order}
            tot = [sum(raw_st[lv][i] for lv in order) for i in range(len(veg_names))]
            pct = {lv: [raw_st[lv][i] / tot[i] * 100 if tot[i] else 0 for i in range(len(veg_names))] for lv in order}
            viz.plot_veg_bar(veg_names, pct, f"不同植被 {name} 趋势等级占比",
                             str(out / f"{name}_veg_bar.png"))
            logger.info("%s 不同植被趋势图完成", name)
        else:
            summary[name] = {}
        if method_cfg == "both":
            # both 增强: linear 也做完整 5 级 classify + 散点对比图 + stats 扩展
            slope_lin, z_lin = trend_cube(stack.astype(np.float32), years, "linear")
            cls_lin = classify_pheno(slope_lin, z_lin, slope_thr, z_crit)
            write_single_band(cls_lin, str(out / f"{name}_linear_trend_class.tif"), prof,
                              dtype="int8", nodata=0)
            viz.plot_slope_compare(
                slope, slope_lin,
                f"{name} Sen-MK vs 线性回归 斜率一致性",
                str(out / f"{name}_slope_compare.png"),
                xlabel="Sen-MK 斜率 (DOY/yr)",
                ylabel="线性回归斜率 (DOY/yr)",
            )
            if not isinstance(summary.get(name), dict):
                summary[name] = {}

            def _ratio(c, lv):
                v = c[c > 0]
                if v.size == 0:
                    return 0.0
                uv, cnt = np.unique(v, return_counts=True)
                d = dict(zip(uv.tolist(), cnt.tolist()))
                return d.get(lv, 0) / v.size

            # Pearson r (nan-safe)
            a = np.asarray(slope, dtype=float).ravel()
            b = np.asarray(slope_lin, dtype=float).ravel()
            m = np.isfinite(a) & np.isfinite(b)
            r = float(np.corrcoef(a[m], b[m])[0, 1]) if m.sum() > 1 else float("nan")
            summary[name]["slope_by_method"] = {
                "sen_mk": float(np.nanmean(slope)),
                "linear": float(np.nanmean(slope_lin)),
                "pearson_r": r,
                "sen_mk_area_ratio": {
                    "显著延迟": _ratio(cls, 1), "显著提前": _ratio(cls, 5),
                    "延迟合计": _ratio(cls, 1) + _ratio(cls, 2),
                    "提前合计": _ratio(cls, 4) + _ratio(cls, 5),
                },
                "linear_area_ratio": {
                    "显著延迟": _ratio(cls_lin, 1), "显著提前": _ratio(cls_lin, 5),
                    "延迟合计": _ratio(cls_lin, 1) + _ratio(cls_lin, 2),
                    "提前合计": _ratio(cls_lin, 4) + _ratio(cls_lin, 5),
                },
            }
            logger.info(
                "%s both: sen_mk=%.4f linear=%.4f DOY/yr, r=%.4f; "
                "linear_trend_class + slope_compare 已生成",
                name, summary[name]["slope_by_method"]["sen_mk"],
                summary[name]["slope_by_method"]["linear"], r,
            )
        logger.info("%s 物候趋势完成", name)

    return {"out_dir": str(out), "summary": summary}
