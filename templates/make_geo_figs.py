"""用地理要素(经纬度轴+指北针+比例尺+研究区边界高亮)重出关键空间图。

读 outputs 的 tif (含 transform), 不联网。
用法: python make_geo_figs.py config.yaml
"""
from __future__ import annotations

import sys
from pathlib import Path

from src import viz
from src.ndvi_trend import TREND_LEVELS
from src.phenology_trend import PHENO_LEVELS
from src.utils import load_config, load_tif


def main() -> None:
    cfg = load_config(sys.argv[1] if len(sys.argv) > 1 else "config.yaml")
    out = Path(cfg["paths"]["outputs"])
    geo = out / "geo"
    geo.mkdir(parents=True, exist_ok=True)
    from src import viz
    viz.set_style(cfg.get("viz", {}).get("style", "color"))
    boundary = cfg.get("roi", {}).get("boundary_geojson")  # 研究区边界 GeoJSON

    # NDVI 趋势空间 (分类)
    arr, prof = load_tif(str(out / "ndvi_trend" / "trend_class.tif"))
    viz.plot_spatial_geo(arr, prof["transform"], "NDVI 趋势空间分布",
                         str(geo / "trend_spatial_geo.png"), levels=TREND_LEVELS, boundary=boundary)
    print("出 trend_spatial_geo.png")

    # 物候均值 (连续 DOY)
    for k, label in [("sos", "SOS 绿返期"), ("peak", "Peak 峰值期"), ("eos", "EOS 枯黄期")]:
        a, p = load_tif(str(out / "phenology" / f"{k}_mean.tif"))
        viz.plot_spatial_geo(a, p["transform"], f"{label} 多年平均 (DOY)",
                             str(geo / f"{k}_mean_geo.png"), boundary=boundary)
        print(f"出 {k}_mean_geo.png")

    # 物候趋势空间 (分类)
    for name in ["SOS", "EOS", "Peak"]:
        a, p = load_tif(str(out / "phenology_trend" / f"{name}_trend_class.tif"))
        viz.plot_spatial_geo(a, p["transform"], f"{name} 趋势空间分布",
                             str(geo / f"{name}_spatial_geo.png"), levels=PHENO_LEVELS, boundary=boundary, kind="pheno_trend")
        print(f"出 {name}_spatial_geo.png")

    print(f"地理要素图(含边界高亮)完成 -> {geo}")


if __name__ == "__main__":
    main()
