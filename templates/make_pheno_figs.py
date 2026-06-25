"""补物候图: SOS/EOS/Peak 均值空间图(3张) + 年际折线(1张)。

读 outputs/phenology/*.tif (已由 run_all 生成), 不联网、不依赖 GEE。
用法:
  python make_pheno_figs.py                 # 默认 config.yaml
  python make_pheno_figs.py config.yaml
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from src import viz
from src.preprocess import load_stack
from src.utils import load_config, load_tif, years_in_range

LABELS = {"sos": "SOS 绿返期", "eos": "EOS 枯黄期", "peak": "Peak 峰值期"}


def main() -> None:
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    cfg = load_config(cfg_path)
    if cfg["date"].get("demo"):
        end_year = int(str(cfg["date"]["end"])[:4])
        cfg["date"]["start"] = f"{end_year - 2}-01-01"
    years = years_in_range(cfg)
    from src import viz
    viz.set_style(cfg.get("viz", {}).get("style", "bw"))
    ph = Path(cfg["paths"]["outputs"]) / "phenology"

    # 1) 均值空间图 (范本图7: 物候空间格局, 叠加研究区边界红色高亮)
    boundary = cfg.get("roi", {}).get("boundary_geojson")
    for key, label in LABELS.items():
        arr, prof = load_tif(str(ph / f"{key}_mean.tif"))
        viz.plot_spatial_geo(arr, prof["transform"], f"{label} 多年平均 (DOY)",
                             str(ph / f"{key}_mean.png"), boundary=boundary)
        print(f"出 {key}_mean.png   区域均值DOY={np.nanmean(arr):.0f}")

    # 2) 年际折线 (范本图8: 物候年际变化)
    series: dict[str, list[float]] = {}
    for key, label in LABELS.items():
        vals = []
        for y in years:
            arr, _ = load_tif(str(ph / f"{key}_{y}.tif"))
            vals.append(float(np.nanmean(arr)))
        series[label.split()[0]] = vals  # "SOS"/"EOS"/"Peak"
    viz.plot_pheno_yearly_lines(
        years, series, "物候期年际变化 (区域均值 DOY)", str(ph / "pheno_yearly.png")
    )
    print(f"出 pheno_yearly.png   years={years[0]}-{years[-1]} ({len(years)}年)")

    # 3) 物候提取示意图(范本图1: 原始NDVI + SG平滑 + 动态阈值线 + SOS/Peak/EOS标注)
    data = Path(cfg["paths"]["data"])
    ratio = cfg.get("phenology", {}).get("threshold_ratio", 0.2)
    y = years[-1]
    try:
        raw_stack, _ = load_stack(str(data / "ndvi" / f"{y}.tif"))
        sm_stack, _ = load_stack(str(data / "ndvi_smoothed" / f"{y}.tif"))
        H, W = sm_stack.shape[1:]
        ci, cj = H // 2, W // 2
        raw_ts = raw_stack[:, ci, cj]
        sm_ts = sm_stack[:, ci, cj]
        mn, mx = np.nanmin(sm_ts), np.nanmax(sm_ts)
        thr = mn + ratio * (mx - mn)
        above = sm_ts >= thr
        sos_idx = int(np.argmax(above)) if above.any() else None
        peak_idx = int(np.argmax(sm_ts))
        last = (len(sm_ts) - 1) - int(np.argmax(above[::-1])) if above.any() else None
        eos_idx = int(last) if last is not None else None
        viz.plot_phenology_diagram(raw_ts, sm_ts, sos_idx, peak_idx, eos_idx,
                                   ratio, str(ph / "phenology_diagram.png"))
        print(f"出 phenology_diagram.png (SOS≈{sos_idx*16 if sos_idx else '?'}DOY)")
    except Exception as e:  # noqa: BLE001
        print(f"⚠ phenology_diagram.png 跳过: {e}")


if __name__ == "__main__":
    main()
