"""一键 pipeline: 下载 -> 预处理(SG+重分类) -> NDVI趋势 -> 物候提取 -> 物候趋势。

用法:
  python run_all.py                            # 全流程
  python run_all.py -s preprocess ndvi_trend   # 指定步骤
  python run_all.py -c config.yaml             # 指定配置

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
from src.utils import by_veg_enabled, ensure_dirs, load_config, years_in_range

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
    from src import viz
    viz.set_style(cfg.get("viz", {}).get("style", "bw"))
    years = years_in_range(cfg)
    steps = steps or list(ALL_STEPS)
    analysis = cfg.get("analysis") or {}
    tier = analysis.get("tier", 100)

    # ---- P0-1 params/by_veg 一致性防御 ----
    dl = cfg.get("download", {})
    params_list = list(dl.get("params", ["ndvi", "lc"]))
    has_ndvi = "ndvi" in params_list
    if not has_ndvi:
        for skip_step in ("preprocess", "ndvi_trend", "phenology", "phenology_trend"):
            if skip_step in steps:
                steps.remove(skip_step)
        logging.error("params 不含 ndvi, 无法做物候/趋势分析; 已跳过 preprocess/ndvi_trend/phenology/phenology_trend")
    if by_veg_enabled(cfg) and "lc" not in params_list:
        cfg.setdefault("by_veg", False)["by_veg"] = False
        if "by_veg" in cfg:
            cfg["by_veg"] = False
        logging.warning("by_veg=true 但 params 不含 lc, 已自动置 by_veg=false (不分类模式)")

    # ---- P1-1 tier 三档 ----
    if tier <= 50:
        for skip_step in ("phenology", "phenology_trend"):
            if skip_step in steps:
                steps.remove(skip_step)
        logging.info("tier=%s: 仅 NDVI 趋势档, 跳过物候提取/物候趋势", tier)
    elif tier == 100:
        logging.info("tier=100: 默认全流程")
    elif tier >= 200:
        # 全像元无掩膜: 提高 ndvi_min_valid 阈值, 关闭 mask_low_ndvi
        pp = cfg.setdefault("preprocess", {})
        pp["ndvi_min_valid"] = 0.0
        pp["mask_low_ndvi"] = False
        ph = cfg.setdefault("phenology", {})
        ph["mask_low_ndvi"] = False
        logging.warning("tier=%s: 全像元无掩膜模式 (mask_low_ndvi=false, ndvi_min_valid=0)", tier)
    else:
        # 50 < tier < 100 或 100 < tier < 200: 走默认全流程
        logging.info("tier=%s: 默认全流程", tier)
    data = Path(cfg["paths"]["data"])

    if "download" in steps:
        params = tuple(params_list)
        if not by_veg_enabled(cfg) and "lc" in params:
            params = tuple(p for p in params if p != "lc")
            logging.info("by_veg=false: 下载去掉 lc (不分类模式)")
        logging.info("== [1/5] 数据下载 (years=%s, params=%s, tiled=%s) ==",
                     years, params, dl.get("ndvi_tiled", False))
        download_all(cfg,
                     params=params,
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
        if by_veg_enabled(cfg):
            reclassify_landcover(
                str(data / "lc" / f"lc_{years[-1]}.tif"),
                str(data / "lc" / "lc_reclass.tif"),
                cfg["veg_reclass"],
            )
        else:
            logging.info("by_veg=false: 跳过植被重分类 (不分类模式, 不依赖 lc)")

    if "ndvi_trend" in steps:
        logging.info("== [3/5] NDVI 趋势分析 (70%%保底) ==")
        run_ndvi_trend(cfg)

    if "phenology" in steps:
        logging.info("== [4/5] 物候提取 (动态阈值 SOS/EOS/Peak) ==")
        pheno = run_phenology(cfg)
        if "phenology_trend" in steps:
            logging.info("== [5/5] 物候趋势分析 (100%%) ==")
            run_phenology_trend(cfg, pheno)

    # ---- 后处理: report_stats + extra/pheno 补图 (不阻塞主流程, 失败仅 warning) ----
    # 目的: 让 build_handoff 能拿到完整 stats.json + 全套 38 图(原 run_all 只产 ~23 图)。
    try:
        import importlib
        rs = importlib.import_module("report_stats")
        stats = rs.collect_stats(cfg)
        import json as _json
        sp = Path(cfg["paths"]["outputs"]) / "report_stats.json"
        sp.write_text(_json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
        logging.info("== report_stats.json 已写 -> %s (含 lai/gpp 多源斜率) ==", sp)
    except Exception as e:  # noqa: BLE001
        logging.warning("report_stats 跳过: %s", e)

    for mod_name, desc in [("make_pheno_figs", "物候空间/年际/示意补图"),
                           ("make_extra_figs", "植被分类型补图(veg_*_yearly/stacked/lc_reclass)")]:
        try:
            import importlib
            mod = importlib.import_module(mod_name)
            # make_*_figs.main() 从 sys.argv 读 config, 临时改 argv 注入
            old = sys.argv
            sys.argv = [mod_name, cfg_path]
            try:
                mod.main()
            finally:
                sys.argv = old
            logging.info("== %s 完成 (%s) ==", mod_name, desc)
        except Exception as e:  # noqa: BLE001
            logging.warning("%s 跳过 (%s): %s", mod_name, desc, e)

    logging.info("全部完成 ✅  结果见 %s", cfg["paths"]["outputs"])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser(description="遥感植被物候提取一键 pipeline")
    ap.add_argument("-c", "--config", default="config.yaml")
    ap.add_argument("-s", "--steps", nargs="*", default=None, help=f"步骤子集: {ALL_STEPS}")
    args = ap.parse_args()
    main(args.config, args.steps)
