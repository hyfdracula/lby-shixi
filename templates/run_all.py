"""一键 pipeline: 下载 -> 预处理(SG+重分类) -> NDVI趋势 -> 物候提取 -> 物候趋势。

用法:
  python run_all.py                            # 全流程
  python run_all.py -s preprocess ndvi_trend   # 指定步骤
  python run_all.py -c config_hunan.yaml       # 换研究区

多源/分块: 在 config 的 download 段配置
  download:
    params: [ndvi, lai, gpp, lc]   # 多源
    ndvi_tiled: true                # 分块保 500m (大区域慢但精度高)

demo 模式 (config.date.demo=true): 自动取最近3年。
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.gee_download import download_all
from src.ndvi_trend import run_ndvi_trend
from src.phenology import run_phenology
from src.phenology_trend import run_phenology_trend
from src.preprocess import preprocess_ndvi_year, reclassify_landcover
from src.utils import ensure_dirs, load_config, years_in_range

ALL_STEPS = ["download", "preprocess", "ndvi_trend", "phenology", "phenology_trend"]


def _apply_demo(cfg: dict) -> None:
    if cfg["date"].get("demo"):
        end_year = int(str(cfg["date"]["end"])[:4])
        cfg["date"]["start"] = f"{end_year - 2}-01-01"
        logging.warning("demo 模式: 取最近3年 %s ~ %s", cfg["date"]["start"], cfg["date"]["end"])


def main(cfg_path: str = "config.yaml", steps: list[str] | None = None) -> None:
    cfg = load_config(cfg_path)
    _apply_demo(cfg)
    ensure_dirs(cfg)
    years = years_in_range(cfg)
    steps = steps or list(ALL_STEPS)
    data = Path(cfg["paths"]["data"])

    if "download" in steps:
        dl = cfg.get("download", {})
        logging.info("== [1/5] 数据下载 (years=%s, params=%s, tiled=%s) ==",
                     years, dl.get("params", ["ndvi", "lc"]), dl.get("ndvi_tiled", False))
        download_all(cfg,
                     params=tuple(dl.get("params", ["ndvi", "lc"])),
                     ndvi_tiled=dl.get("ndvi_tiled", False))

    if "preprocess" in steps:
        logging.info("== [2/5] 预处理 (SG滤波 + 植被重分类) ==")
        win = cfg["preprocess"]["sg_window"]
        poly = cfg["preprocess"]["sg_polyorder"]
        thr = cfg["preprocess"]["ndvi_min_valid"]
        for y in years:
            preprocess_ndvi_year(
                str(data / "ndvi" / f"{y}.tif"),
                str(data / "ndvi_smoothed" / f"{y}.tif"),
                win, poly, thr,
            )
        reclassify_landcover(
            str(data / "lc" / f"lc_{years[-1]}.tif"),
            str(data / "lc" / "lc_reclass.tif"),
            cfg["veg_reclass"],
        )

    if "ndvi_trend" in steps:
        logging.info("== [3/5] NDVI 趋势分析 (70%%保底) ==")
        run_ndvi_trend(cfg)

    if "phenology" in steps:
        logging.info("== [4/5] 物候提取 (动态阈值 SOS/EOS/Peak) ==")
        pheno = run_phenology(cfg)
        if "phenology_trend" in steps:
            logging.info("== [5/5] 物候趋势分析 (100%%) ==")
            run_phenology_trend(cfg, pheno)

    logging.info("全部完成 ✅  结果见 %s", cfg["paths"]["outputs"])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser(description="遥感植被物候提取一键 pipeline")
    ap.add_argument("-c", "--config", default="config.yaml")
    ap.add_argument("-s", "--steps", nargs="*", default=None, help=f"步骤子集: {ALL_STEPS}")
    args = ap.parse_args()
    main(args.config, args.steps)
