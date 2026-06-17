"""预处理: -9999 转 NaN、Savitzky-Golay 滤波、低值掩膜、植被重分类。"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from scipy.signal import savgol_filter

from .utils import reclass_lc

logger = logging.getLogger(__name__)

NODATA = -9999  # 与 gee_download 一致


def load_stack(path: str) -> tuple[np.ndarray, dict[str, Any]]:
    """读多波段 GeoTIFF -> (bands, H, W) float32; -9999 哨兵转 NaN。"""
    with rasterio.open(path) as src:
        arr = src.read().astype(np.float32)
        prof = src.profile
    arr[arr == NODATA] = np.nan
    return arr, prof


def fill_nan_time(stack: np.ndarray) -> np.ndarray:
    """沿时间轴(轴0)线性插值填补 NaN, 全 NaN 像元保持不变。带进度条。"""
    from tqdm import tqdm

    T = stack.shape[0]
    out = stack.copy()
    idx = np.arange(T)
    H, W = stack.shape[1], stack.shape[2]
    for i in tqdm(range(H), desc="SG 滤波填值", unit="row"):
        for j in range(W):
            col = out[:, i, j]
            bad = np.isnan(col)
            if bad.all() or not bad.any():
                continue
            out[:, i, j] = np.interp(idx, idx[~bad], col[~bad])
    return out


def sg_smooth(stack: np.ndarray, window: int = 5, polyorder: int = 2) -> np.ndarray:
    """Savitzky-Golay 滤波, 沿时间轴。先填 NaN 再滤波。"""
    if window % 2 == 0:
        raise ValueError("SG 窗口必须为奇数")
    filled = fill_nan_time(stack)
    return savgol_filter(
        filled, window_length=window, polyorder=polyorder, axis=0
    ).astype(np.float32)


def yearly_mean(stack: np.ndarray) -> np.ndarray:
    """年内各期均值 -> 单帧 (H, W)。"""
    with np.errstate(invalid="ignore"):
        return np.nanmean(stack, axis=0)


def mask_low_ndvi(stack: np.ndarray, ndvi_mean: np.ndarray, threshold: float = 0.05) -> np.ndarray:
    """年均 NDVI < threshold 的像元全期置 NaN。"""
    out = stack.copy()
    out[:, ndvi_mean < threshold] = np.nan
    return out


def save_stack(stack: np.ndarray, path: str, profile: dict[str, Any]) -> None:
    """3D (T,H,W) 写多波段 GeoTIFF (float32, NaN)。"""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    prof = profile.copy()
    prof.update(dtype="float32", count=stack.shape[0], nodata=np.nan)
    with rasterio.open(path, "w", **prof) as dst:
        for b in range(stack.shape[0]):
            dst.write(np.asarray(stack[b], dtype=np.float32), b + 1)


def preprocess_ndvi_year(
    in_tif: str, out_tif: str, window: int, polyorder: int, thr: float
) -> dict[str, Any]:
    """对一年 NDVI 多波段 tif: SG 滤波 + 低值掩膜, 输出滤波后多波段 tif。"""
    arr, prof = load_stack(in_tif)
    smoothed = sg_smooth(arr, window, polyorder)
    ymean = yearly_mean(smoothed)
    cleaned = mask_low_ndvi(smoothed, ymean, thr)
    save_stack(cleaned, out_tif, prof)
    return {
        "n_valid_pixels": int(np.sum(~np.isnan(ymean))),
        "mean_ndvi": float(np.nanmean(ymean)) if np.isfinite(ymean).any() else float("nan"),
    }


def reclassify_landcover(lc_tif: str, out_tif: str, veg_map: dict[str, list[int]]) -> str:
    """IGBP 土地覆盖 -> 4大类标签 tif (1森林/2草地/3农田/4湿地, 0其他)。"""
    with rasterio.open(lc_tif) as src:
        lc = src.read(1)
        prof = src.profile
    lc = lc.astype(np.int32)
    lc[lc == NODATA] = 0  # 边界外归 "其他"
    labels = reclass_lc(lc, veg_map)
    Path(out_tif).parent.mkdir(parents=True, exist_ok=True)
    prof.update(dtype="int8", count=1, nodata=0)
    with rasterio.open(out_tif, "w", **prof) as dst:
        dst.write(labels.astype(np.int8), 1)
    logger.info("植被重分类 -> %s", out_tif)
    return out_tif
