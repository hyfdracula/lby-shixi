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
from .utils import by_veg_stats, load_lc_aligned, sen_mk_cube, write_single_band

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
    slope_thr = cfg["trend"]["slope_threshold"]
    z_crit = cfg["trend"]["z_critical"]
    out = Path(cfg["paths"]["outputs"]) / "phenology_trend"
    out.mkdir(parents=True, exist_ok=True)
    grid_shape = pheno_result["sos_stack"].shape[1:]  # (H, W), 与物候 grid 对齐
    lc_arr = load_lc_aligned(str(Path(cfg["paths"]["data"]) / "lc" / "lc_reclass.tif"), grid_shape)
    prof = pheno_result["profile"]
    summary: dict[str, dict] = {}

    for name, stack in [
        ("SOS", pheno_result["sos_stack"]),
        ("EOS", pheno_result["eos_stack"]),
        ("Peak", pheno_result["peak_stack"]),
    ]:
        slope, z = sen_mk_cube(stack.astype(np.float32))
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
        summary[name] = by_veg_stats(cls, lc_arr, PHENO_LEVELS)
        logger.info("%s 物候趋势完成", name)

    return {"out_dir": str(out), "summary": summary}
