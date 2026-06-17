"""深化报告所需数值: 逐年NDVI均值(三阶段) + 物候空间分位数 + 各植被物候均值。

用法: python report_stats2.py config_hunan.yaml
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from src.preprocess import load_stack, yearly_mean
from src.utils import VEG_LABELS, load_config, load_lc_aligned, load_tif, years_in_range


def main() -> None:
    cfg = load_config(sys.argv[1] if len(sys.argv) > 1 else "config_hunan.yaml")
    data = Path(cfg["paths"]["data"])
    out = Path(cfg["paths"]["outputs"])
    years = years_in_range(cfg)

    arr0, _ = load_stack(str(data / "ndvi_smoothed" / f"{years[-1]}.tif"))
    grid = arr0.shape[1:]
    lc = load_lc_aligned(str(data / "lc" / "lc_reclass.tif"), grid)

    print("=== 逐年 NDVI 区域均值 (三阶段分析) ===")
    ym: list[float] = []
    for y in years:
        a, _ = load_stack(str(data / "ndvi_smoothed" / f"{y}.tif"))
        v = float(np.nanmean(yearly_mean(a)))
        ym.append(v)
        print(f"  {y}: {v:.4f}")
    for tag, sub in [("2001-2006 低值波动", years[0:6]), ("2007-2012 快速抬升", years[6:12]), ("2013-2020 高位趋稳", years[12:])]:
        idx = [years.index(y) for y in sub if y in years]
        seg = [ym[i] for i in idx]
        if seg:
            print(f"  >>> {tag}: 均值 {np.mean(seg):.4f}")

    print("\n=== 物候多年均值 空间分位数 (DOY) ===")
    for key in ["sos", "peak", "eos"]:
        arr, _ = load_tif(str(out / "phenology" / f"{key}_mean.tif"))
        v = arr[np.isfinite(arr)]
        if v.size == 0:
            continue
        print(f"  {key.upper()}: min={np.min(v):.0f} p25={np.percentile(v,25):.0f} "
              f"med={np.percentile(v,50):.0f} p75={np.percentile(v,75):.0f} max={np.max(v):.0f}")

    print("\n=== 各植被物候多年均值 (DOY) ===")
    for key in ["sos", "peak", "eos"]:
        arr, _ = load_tif(str(out / "phenology" / f"{key}_mean.tif"))
        line = f"  {key.upper()}: "
        for vv, name in VEG_LABELS.items():
            m = lc == vv
            if m.any():
                line += f"{name}={np.nanmean(arr[m]):.1f} "
        print(line)


if __name__ == "__main__":
    main()
