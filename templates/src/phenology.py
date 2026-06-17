"""动态阈值法物候提取: SOS(春季绿返)/EOS(秋季枯黄)/Peak(峰值) DOY。

向量化实现 (numpy 批量), 适合大区域; NaN 像元自动跳过。比逐像元循环快数十倍。
阈值: NDVI_threshold = NDVI_min + ratio*(NDVI_max-NDVI_min)
SOS = 年内首次 >= 阈值 的期; EOS = 年内最后一次 >= 阈值 的期; Peak = argmax。
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

from .preprocess import load_stack
from .utils import write_single_band, years_in_range

logger = logging.getLogger(__name__)


def extract_phenology_year(stack: np.ndarray, ratio: float = 0.2):
    """向量化提取单年 (T,H,W) -> (sos, eos, peak), 单位 DOY (期序号×16)。"""
    T, H, W = stack.shape
    allnan = np.isnan(stack).all(axis=0)  # (H,W) 全 NaN 像元
    filled = np.where(np.isnan(stack), -np.inf, stack)

    mn = np.nanmin(stack, axis=0)
    mx = np.nanmax(stack, axis=0)
    with np.errstate(invalid="ignore"):
        thr = mn + ratio * (mx - mn)  # (H,W)
    above = filled >= thr[None, :, :]  # (T,H,W)
    any_above = above.any(axis=0)

    # Peak: 年内最大值期
    peak = (np.argmax(filled, axis=0) * 16).astype(np.float32)
    # SOS: 首次 >= 阈值 (春季绿返)
    sos = (np.argmax(above, axis=0).astype(np.float32)) * 16
    # EOS: 最后一次 >= 阈值 (秋季枯黄, 下降段离开阈值)
    last = (T - 1) - np.argmax(above[::-1], axis=0)
    eos = (last.astype(np.float32)) * 16

    invalid = allnan | ~any_above
    sos[invalid] = np.nan
    eos[invalid] = np.nan
    peak[allnan] = np.nan
    return sos, eos, peak


def run_phenology(cfg: dict[str, Any]) -> dict[str, Any]:
    years = years_in_range(cfg)
    base = Path(cfg["paths"]["data"]) / "ndvi_smoothed"
    out = Path(cfg["paths"]["outputs"]) / "phenology"
    out.mkdir(parents=True, exist_ok=True)
    ratio = cfg["phenology"]["threshold_ratio"]

    sos_list, eos_list, peak_list, prof = [], [], [], None
    for y in years:
        arr, prof = load_stack(str(base / f"{y}.tif"))
        s, e, p = extract_phenology_year(arr, ratio)
        write_single_band(s, str(out / f"sos_{y}.tif"), prof)
        write_single_band(e, str(out / f"eos_{y}.tif"), prof)
        write_single_band(p, str(out / f"peak_{y}.tif"), prof)
        sos_list.append(s)
        eos_list.append(e)
        peak_list.append(p)

    sos_stack = np.stack(sos_list)
    eos_stack = np.stack(eos_list)
    peak_stack = np.stack(peak_list)
    write_single_band(np.nanmean(sos_stack, axis=0), str(out / "sos_mean.tif"), prof)
    write_single_band(np.nanmean(eos_stack, axis=0), str(out / "eos_mean.tif"), prof)
    write_single_band(np.nanmean(peak_stack, axis=0), str(out / "peak_mean.tif"), prof)
    logger.info("物候提取完成: %d年, SOS均值DOY=%.1f, Peak=%.1f, EOS=%.1f",
                len(years), np.nanmean(sos_stack), np.nanmean(peak_stack), np.nanmean(eos_stack))
    return {
        "years": years,
        "sos_stack": sos_stack,
        "eos_stack": eos_stack,
        "peak_stack": peak_stack,
        "profile": prof,
    }
