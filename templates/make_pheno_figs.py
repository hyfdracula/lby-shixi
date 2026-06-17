"""补物候图: SOS/EOS/Peak 均值空间图(3张) + 年际折线(1张)。

读 outputs[_hunan]/phenology/*.tif (已由 run_all 生成), 不联网、不依赖 GEE。
用法:
  python make_pheno_figs.py                 # 默认 config.yaml (北京)
  python make_pheno_figs.py config_hunan.yaml   # 湖南
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from src import viz
from src.utils import load_config, load_tif, years_in_range

LABELS = {"sos": "SOS 绿返期", "eos": "EOS 枯黄期", "peak": "Peak 峰值期"}


def main() -> None:
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    cfg = load_config(cfg_path)
    if cfg["date"].get("demo"):
        end_year = int(str(cfg["date"]["end"])[:4])
        cfg["date"]["start"] = f"{end_year - 2}-01-01"
    years = years_in_range(cfg)
    ph = Path(cfg["paths"]["outputs"]) / "phenology"

    # 1) 均值空间图 (范本图7: 物候空间格局)
    for key, label in LABELS.items():
        arr, _ = load_tif(str(ph / f"{key}_mean.tif"))
        viz.plot_pheno_spatial(arr, f"{label} 多年平均 (DOY)", str(ph / f"{key}_mean.png"))
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


if __name__ == "__main__":
    main()
