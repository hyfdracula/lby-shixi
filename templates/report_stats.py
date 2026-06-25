"""读 outputs, 算报告所需全部统计数值, 打印 + 写 stats.json (供 handoff/最终报告填真值)。

用法: python report_stats.py config.yaml
by_veg=false 时跳过按植被统计 (不分类模式)。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from src.ndvi_trend import TREND_LEVELS
from src.phenology_trend import PHENO_LEVELS
from src.utils import by_veg_enabled, by_veg_stats, load_config, load_lc_aligned, load_tif, veg_labels_from_config, years_in_range


def collect_stats(cfg: dict) -> dict:
    """收集报告所需的全部统计 -> dict (供 handoff/最终报告填结果占位 + 写 stats.json)。"""
    data = cfg["paths"]["data"]
    out = cfg["paths"]["outputs"]
    do_veg = by_veg_enabled(cfg)
    veg_labels = veg_labels_from_config(cfg)
    stats: dict = {}

    p = f"{out}/ndvi_trend/sen_slope.tif"
    if Path(p).exists():
        slope, _ = load_tif(p)
        stats["ndvi_slope_mean"] = round(float(np.nanmean(slope)), 6)
        cls, _ = load_tif(f"{out}/ndvi_trend/trend_class.tif")
        valid = cls[cls > 0]
        if valid.size:
            vals, cnts = np.unique(valid, return_counts=True)
            total = cnts.sum()
            stats["ndvi_trend_pct"] = {TREND_LEVELS[int(v)]: round(float(c / total * 100), 2)
                                       for v, c in zip(vals, cnts)}
        if do_veg:
            lc = load_lc_aligned(f"{data}/lc/lc_reclass.tif", cls.shape)
            stats["ndvi_slope_by_veg"] = {
                veg_labels[v]: round(float(np.nanmean(slope[lc == v])), 6)
                for v in veg_labels if (lc == v).any()
            }

    for k in ["sos", "eos", "peak"]:
        pp = f"{out}/phenology/{k}_mean.tif"
        if Path(pp).exists():
            arr, _ = load_tif(pp)
            stats[f"{k}_mean_doy"] = round(float(np.nanmean(arr)), 1)

    for name in ["SOS", "EOS", "Peak"]:
        pp = f"{out}/phenology_trend/{name}_trend_class.tif"
        if not Path(pp).exists():
            continue
        c, _ = load_tif(pp)
        vv = c[c > 0]
        if not vv.size:
            continue
        v2, cc2 = np.unique(vv, return_counts=True)
        t2 = cc2.sum()
        stats[f"{name.lower()}_trend_pct"] = {PHENO_LEVELS[int(a)]: round(float(b / t2 * 100), 2)
                                              for a, b in zip(v2, cc2)}

    # 多源 LAI/GPP 区域年均线性斜率 (供模板 {lai_slope}/{gpp_slope} 占位回填)
    try:
        from src.preprocess import load_stack, yearly_mean
        for param in ("lai", "gpp"):
            ys, series = [], []
            ok = True
            for y in years_in_range(cfg):
                p = Path(data) / param / f"{y}.tif"
                if not p.exists():
                    ok = False
                    break
                arr, _ = load_stack(str(p))
                ys.append(y)
                series.append(float(np.nanmean(yearly_mean(arr))))
            if ok and len(ys) >= 2:
                slope = float(np.polyfit(ys, series, 1)[0])
                stats[f"{param}_slope"] = round(slope, 4)
                stats[f"{param}_mean"] = round(float(np.mean(series)), 3)
    except Exception as e:  # noqa: BLE001
        # 多源缺失或不可用: 不阻塞主统计
        print(f"⚠ LAI/GPP 多源斜率跳过: {e}")
    return stats


def main() -> None:
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    cfg = load_config(cfg_path)
    data = cfg["paths"]["data"]
    out = cfg["paths"]["outputs"]
    do_veg = by_veg_enabled(cfg)
    veg_labels = veg_labels_from_config(cfg)

    cls, _ = load_tif(f"{out}/ndvi_trend/trend_class.tif")
    slope, _ = load_tif(f"{out}/ndvi_trend/sen_slope.tif")
    lc = load_lc_aligned(f"{data}/lc/lc_reclass.tif", cls.shape) if do_veg else None

    print("========== NDVI 趋势 ==========")
    print(f"区域 Sen 斜率均值: {np.nanmean(slope):.6f} /yr")
    valid = cls[cls > 0]
    vals, cnts = np.unique(valid, return_counts=True)
    total = cnts.sum()
    print("5 级面积占比:")
    for v, c in zip(vals, cnts):
        print(f"  {TREND_LEVELS[int(v)]}: {int(c)} px ({c / total * 100:.2f}%)")
    if do_veg:
        print("按植被各级像素:")
        for veg, d in by_veg_stats(cls, lc, TREND_LEVELS, veg_labels).items():
            print(f"  {veg}: {d}")
        print("各植被 Sen 斜率:")
        for v, name in veg_labels.items():
            m = lc == v
            if m.any():
                print(f"  {name}: {np.nanmean(slope[m]):.6f} /yr  (像元{int(m.sum())})")
    else:
        print("by_veg=false: 跳过按植被统计 (不分类模式)")

    print("\n========== 物候多年均值 ==========")
    for k in ["sos", "eos", "peak"]:
        arr, _ = load_tif(f"{out}/phenology/{k}_mean.tif")
        print(f"{k.upper()} 均值DOY={np.nanmean(arr):.1f}  中位数={np.nanmedian(arr):.0f}  std={np.nanstd(arr):.1f}")

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
        if do_veg:
            print(f"{name} 按植被: {by_veg_stats(c, lc, PHENO_LEVELS, veg_labels)}")

    # 写 stats.json 供 handoff/最终报告填真值 (解玉门第2坑: 报告结果不再靠手写)
    stats = collect_stats(cfg)
    stats_path = Path(out) / "report_stats.json"
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n统计已写 -> {stats_path} (供 handoff/最终报告填结果占位)")


if __name__ == "__main__":
    main()
