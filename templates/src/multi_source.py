"""多源(LAI/GPP)分析: 区域年均年际趋势折线 + Sen 斜率 + 多源归一化对比。

LAI/GPP 多源只看区域年均年际趋势(不做逐像元物候), 故跳过 SG 平滑
(LAI/GPP 数据空洞多, sg_smooth 遇全 NaN 像元报错; 区域年均用 nanmean 忽略)。
用法(独立跑): python -m src.multi_source -c config.yaml
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import numpy as np

from . import viz
from src.preprocess import load_stack, yearly_mean
from src.utils import load_config, years_in_range

logger = logging.getLogger(__name__)


def run_multi_source(cfg: dict[str, Any], params: tuple[str, ...] = ("lai", "gpp")) -> dict:
    years = years_in_range(cfg)
    viz.set_style(cfg.get("viz", {}).get("style", "color"))
    data = Path(cfg["paths"]["data"])
    out = Path(cfg["paths"]["outputs"]) / "multi"
    out.mkdir(parents=True, exist_ok=True)
    summary: dict[str, Any] = {}

    for param in params:
        # 直接读原始(已 -9999→NaN), 区域年均(nanmean 忽略空洞), 跳过 SG
        series: list[float] = []
        for y in years:
            arr, _ = load_stack(str(data / param / f"{y}.tif"))
            series.append(float(np.nanmean(yearly_mean(arr))))
        ylabel = {"lai": "LAI (m²/m²)", "gpp": "GPP (gC/m²/16d)", "evi": "EVI", "sif": "SIF (mW/m²/sr/nm)"}.get(param, param.upper())
        viz.plot_yearly_trend(years, series, f"{param.upper()} 区域年均年际变化",
                              str(out / f"{param}_yearly.png"), ylabel=ylabel)
        slope = float(np.polyfit(years, series, 1)[0])
        summary[param] = {"yearly": series, "slope_per_yr": slope,
                          "mean": float(np.mean(series))}
        logger.info("%s: 年均%s slope=%.4f/yr 均值=%.3f",
                    param.upper(), [f"{v:.3f}" for v in series], slope, np.mean(series))

    # 多源对比图 (NDVI/LAI/GPP 归一化)
    try:
        ndvi_series = []
        for y in years:
            arr, _ = load_stack(str(data / "ndvi_smoothed" / f"{y}.tif"))
            ndvi_series.append(float(np.nanmean(yearly_mean(arr))))
        _plot_multi_compare(years, {"NDVI": ndvi_series, **{k.upper(): v["yearly"] for k, v in summary.items()}},
                            str(out / "multi_compare.png"))
    except Exception as e:  # noqa: BLE001
        logger.warning("多源对比图跳过: %s", e)

    logger.info("多源分析完成 -> %s", out)
    return summary


def _plot_multi_compare(years, series_dict, out):
    viz.apply_bw_style()
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 4.5))
    greys = plt.get_cmap("Greys", max(len(series_dict), 1))
    markers = ["o", "s", "^", "D"]
    for i, (label, vals) in enumerate(series_dict.items()):
        vals = np.asarray(vals, dtype=float)
        v = (vals - vals.min()) / (vals.max() - vals.min() + 1e-9)
        ax.plot(years, v, "-" + markers[i % len(markers)], color=greys(i),
                markerfacecolor="white", markersize=5, label=label)
    ax.set_title("多源植被参数年际变化对比 (min-max 归一化)")
    ax.set_xlabel("Year"); ax.set_ylabel("归一化值")
    ax.legend(frameon=False)
    viz._save(fig, out)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="多源 LAI/GPP 区域年际趋势分析")
    parser.add_argument("config_pos", nargs="?", help="配置文件路径")
    parser.add_argument("-c", "--config", default=None, help="配置文件路径")
    parser.add_argument("--params", nargs="*", default=["lai", "gpp"], help="要分析的参数, 默认 lai gpp")
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _parse_args()
    cfg = load_config(args.config or args.config_pos or "config.yaml")
    if cfg["date"].get("demo"):
        end_year = int(str(cfg["date"]["end"])[:4])
        cfg["date"]["start"] = f"{end_year - 2}-01-01"
    run_multi_source(cfg, params=tuple(args.params))
