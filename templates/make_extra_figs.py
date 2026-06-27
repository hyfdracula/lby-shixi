"""补图脚本(对标范本): 原始/滤波对比 + 各植被NDVI年际 + 各植被物候年际 + 植被趋势堆叠柱状。

读 data + outputs, 不联网、不依赖 GEE。
用法: python make_extra_figs.py config.yaml
by_veg=false 时只出 raw_vs_smooth, 跳过按植被图 (不分类模式)。
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from src import viz
from src.ndvi_trend import TREND_LEVELS
from src.phenology_trend import PHENO_LEVELS
from src.preprocess import load_stack, yearly_mean
from src.utils import (
    by_veg_enabled,
    by_veg_stats,
    load_config,
    load_lc_aligned,
    load_tif,
    veg_labels_from_config,
    years_in_range,
)


def main() -> None:
    cfg = load_config(sys.argv[1] if len(sys.argv) > 1 else "config.yaml")
    data = Path(cfg["paths"]["data"])
    out = Path(cfg["paths"]["outputs"])
    years = years_in_range(cfg)
    from src import viz
    viz.set_style(cfg.get("viz", {}).get("style", "color"))
    ext = out / "extra"
    ext.mkdir(parents=True, exist_ok=True)

    arr0, _ = load_stack(str(data / "ndvi_smoothed" / f"{years[-1]}.tif"))
    do_veg = by_veg_enabled(cfg)
    lc = load_lc_aligned(str(data / "lc" / "lc_reclass.tif"), arr0.shape[1:]) if do_veg else None

    # 1) 原始 vs SG 滤波 (不依赖 lc, 始终出)
    raw, _ = load_stack(str(data / "ndvi" / f"{years[-1]}.tif"))
    viz.plot_raw_vs_smooth(
        np.nanmean(raw, axis=(1, 2)), np.nanmean(arr0, axis=(1, 2)),
        f"{years[-1]} 年 NDVI 原始 vs SG 滤波 (区域均值)", str(ext / "raw_vs_smooth.png"),
    )
    print("出 raw_vs_smooth.png")

    if not do_veg:
        print("by_veg=false: 跳过按植被补图 (不分类模式)")
        print(f"补图完成 (仅全区) -> {ext}")
        return
    veg_labels = veg_labels_from_config(cfg)

    # 2) 各植被 NDVI 年际折线 (4 线)
    series: dict[str, list[float]] = {}
    for v, name in veg_labels.items():
        m = lc == v
        if not m.any():
            continue
        series[name] = [float(np.nanmean(yearly_mean(load_stack(str(data / "ndvi_smoothed" / f"{y}.tif"))[0])[m]))
                    for y in years]
    viz.plot_pheno_yearly_lines(years, series, "不同植被类型 NDVI 年际变化",
                                str(ext / "veg_ndvi_yearly.png"), ylabel="NDVI")
    print("出 veg_ndvi_yearly.png")

    # 3) 各植被物候年际 (SOS/Peak/EOS 各一, 4 植被线)
    for key, label in [("sos", "SOS"), ("peak", "Peak"), ("eos", "EOS")]:
        s: dict[str, list[float]] = {}
        for v, name in veg_labels.items():
            mm = lc == v
            if not mm.any():
                continue
            s[name] = [float(np.nanmean(load_tif(str(out / "phenology" / f"{key}_{y}.tif"))[0][mm]))
                       for y in years]
        viz.plot_pheno_yearly_lines(years, s, f"不同植被 {label} 年际变化 (DOY)",
                                    str(ext / f"veg_{key}_yearly.png"), ylabel="DOY")
        print(f"出 veg_{key}_yearly.png")

    # 4) 各植被 NDVI 趋势等级堆叠柱状 (百分比)
    cls, _ = load_tif(str(out / "ndvi_trend" / "trend_class.tif"))
    stats = by_veg_stats(cls, lc, TREND_LEVELS, veg_labels)
    veg_names = list(stats.keys())
    order = ["显著退化", "轻微退化", "稳定不变", "轻微改善", "显著改善"]
    raw_st = {lv: [stats[vn].get(lv, 0) for vn in veg_names] for lv in order}
    tot = [sum(raw_st[lv][i] for lv in order) for i in range(len(veg_names))]
    pct = {lv: [raw_st[lv][i] / tot[i] * 100 if tot[i] else 0 for i in range(len(veg_names))] for lv in order}
    viz.plot_veg_bar(veg_names, pct, "不同植被 NDVI 趋势等级占比",
                     str(ext / "veg_ndvi_trend_stacked.png"))
    print("出 veg_ndvi_trend_stacked.png")

    # 5) 各植被物候趋势等级堆叠 (SOS/EOS/Peak 各一)
    porder = ["显著延迟", "轻微延迟", "无显著变化", "轻微提前", "显著提前"]
    for name in ["SOS", "EOS", "Peak"]:
        c, _ = load_tif(str(out / "phenology_trend" / f"{name}_trend_class.tif"))
        st = by_veg_stats(c, lc, PHENO_LEVELS, veg_labels)
        vns = list(st.keys())
        st2 = {lv: [st[vn].get(lv, 0) for vn in vns] for lv in porder}
        tot2 = [sum(st2[lv][i] for lv in porder) for i in range(len(vns))]
        pct2 = {lv: [st2[lv][i] / tot2[i] * 100 if tot2[i] else 0 for i in range(len(vns))] for lv in porder}
        viz.plot_veg_bar(vns, pct2, f"不同植被 {name} 趋势等级占比",
                         str(ext / f"veg_{name}_trend_stacked.png"))
        print(f"出 veg_{name}_trend_stacked.png")

    # 图2: IGBP 植被分类(重分类空间图+图例)
    viz.plot_spatial_class(lc, veg_labels, "IGBP 重分类: 植被类型", str(ext / "lc_reclass.png"))
    print("出 lc_reclass.png (图2: IGBP分类图例)")

    print(f"全部补图完成 -> {ext}")


if __name__ == "__main__":
    main()
