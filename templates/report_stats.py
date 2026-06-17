"""读 outputs_hunan, 算报告所需全部统计数值, 打印 (供填报告)。

用法: python report_stats.py config_hunan.yaml
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from src.ndvi_trend import TREND_LEVELS
from src.phenology_trend import PHENO_LEVELS
from src.utils import VEG_LABELS, by_veg_stats, load_config, load_lc_aligned, load_tif


def main() -> None:
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else "config_hunan.yaml"
    cfg = load_config(cfg_path)
    data = cfg["paths"]["data"]
    out = cfg["paths"]["outputs"]

    # ── NDVI 趋势 ──
    cls, _ = load_tif(f"{out}/ndvi_trend/trend_class.tif")
    slope, _ = load_tif(f"{out}/ndvi_trend/sen_slope.tif")
    lc = load_lc_aligned(f"{data}/lc/lc_reclass.tif", cls.shape)

    print("========== NDVI 趋势 ==========")
    print(f"区域 Sen 斜率均值: {np.nanmean(slope):.6f} /yr")
    valid = cls[cls > 0]
    vals, cnts = np.unique(valid, return_counts=True)
    total = cnts.sum()
    print("5 级面积占比:")
    for v, c in zip(vals, cnts):
        print(f"  {TREND_LEVELS[int(v)]}: {int(c)} px ({c / total * 100:.2f}%)")
    print("按植被各级像素:")
    for veg, d in by_veg_stats(cls, lc, TREND_LEVELS).items():
        print(f"  {veg}: {d}")
    print("各植被 Sen 斜率:")
    for v, name in VEG_LABELS.items():
        m = lc == v
        if m.any():
            print(f"  {name}: {np.nanmean(slope[m]):.6f} /yr  (像元{int(m.sum())})")

    # ── 物候均值 ──
    print("\n========== 物候多年均值 ==========")
    for k in ["sos", "eos", "peak"]:
        arr, _ = load_tif(f"{out}/phenology/{k}_mean.tif")
        print(f"{k.upper()} 均值DOY={np.nanmean(arr):.1f}  中位数={np.nanmedian(arr):.0f}  std={np.nanstd(arr):.1f}")

    # ── 物候趋势 ──
    print("\n========== 物候趋势 ==========")
    for name in ["SOS", "EOS", "Peak"]:
        c, _ = load_tif(f"{out}/phenology_trend/{name}_trend_class.tif")
        vv = c[c > 0]
        if not vv.size:
            print(f"{name}: 无有效像元")
            continue
        v2, cc2 = np.unique(vv, return_counts=True)
        t2 = cc2.sum()
        print(f"{name} 趋势占比:")
        for a, b in zip(v2, cc2):
            print(f"  {PHENO_LEVELS[int(a)]}: {b / t2 * 100:.2f}%")
        print(f"{name} 按植被: {by_veg_stats(c, lc, PHENO_LEVELS)}")


if __name__ == "__main__":
    main()
