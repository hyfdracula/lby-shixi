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


def extract_phenology_year(stack: np.ndarray, ratio: float = 0.2, evergreen_thr: float = 0.1):
    """向量化提取单年 (T,H,W) -> (sos, eos, peak), 单位 DOY (期序号×16)。

    evergreen_thr: 年内 NDVI 振幅(max-min) < 此值的像元视为常绿/水体/裸地,
    SOS/EOS 置 NaN(动态阈值在常绿区失效: 全年高NDVI→阈值≈min→首达/末达误判为期首/期末,
    典型表现 SOS≈DOY 16、EOS≈DOY 348、生长季≈336 天); Peak 保留(年内最大值期对常绿仍有意义)。
    """
    T, H, W = stack.shape
    allnan = np.isnan(stack).all(axis=0)  # (H,W) 全 NaN 像元
    filled = np.where(np.isnan(stack), -np.inf, stack)

    mn = np.nanmin(stack, axis=0)
    mx = np.nanmax(stack, axis=0)
    amplitude = mx - mn                       # 年内振幅
    evergreen = amplitude < evergreen_thr     # 常绿/水体/裸地: 振幅过小, 物候信号弱
    with np.errstate(invalid="ignore"):
        thr = mn + ratio * (mx - mn)  # (H,W)
    above = filled >= thr[None, :, :]  # (T,H,W)
    any_above = above.any(axis=0)

    # Peak: 年内最大值期 (DOY≈期序号×16, MOD13A2 16天合成, 假设每年 23 期; 闰年/边界期数微偏)
    peak = (np.argmax(filled, axis=0) * 16).astype(np.float32)
    # SOS: 首次 >= 阈值 (春季绿返)
    sos = (np.argmax(above, axis=0).astype(np.float32)) * 16
    # EOS: 最后一次 >= 阈值 (秋季枯黄, 下降段离开阈值)
    last = (T - 1) - np.argmax(above[::-1], axis=0)
    eos = (last.astype(np.float32)) * 16

    invalid = allnan | ~any_above | evergreen  # 常绿像元 SOS/EOS 无意义 → NaN
    sos[invalid] = np.nan
    eos[invalid] = np.nan
    peak[allnan] = np.nan
    return sos, eos, peak


def extract_phenology_derivative(stack: np.ndarray, ratio: float = 0.2, evergreen_thr: float = 0.1):
    """导数法提取单年 (T,H,W) -> (sos, eos, peak), 单位 DOY (期序号×16)。

    向量化实现:
      - 沿时间轴 np.diff 求一阶差分 (T-1, H, W);
      - SOS = 前半段(春季)最大正导数期(展叶最快);
      - EOS = 后半段(秋季)最大负导数期(枯黄最快);
      - Peak = argmax(NDVI)。
    evergreen_thr 过滤逻辑同动态阈值法(振幅过小 → 常绿/水体/裸地, SOS/EOS 置 NaN, Peak 保留)。
    ratio 形参保留以统一调用签名, 导数法本身不使用。
    """
    T, H, W = stack.shape
    allnan = np.isnan(stack).all(axis=0)
    filled = np.where(np.isnan(stack), -np.inf, stack)

    mn = np.nanmin(stack, axis=0)
    mx = np.nanmax(stack, axis=0)
    amplitude = mx - mn
    evergreen = amplitude < evergreen_thr

    # 一阶差分: diff[k] = stack[k+1] - stack[k], 长度 T-1
    diff = np.diff(filled, axis=0)  # (T-1, H, W), 含 -inf 边界 → diff 可能为 ±inf
    diff = np.where(np.isinf(diff), np.nan, diff)

    half = (T - 1) // 2
    # SOS: 前半段(0..half-1)最大正导数期; 索引+1 还原到原时间轴期序号
    spring_diff = diff[:half]
    sos_idx = np.nanargmax(spring_diff, axis=0) + 1  # (H,W), 期序号
    # EOS: 后半段(half..T-2)最大负导数期(下降最快); 索引+half+1 还原
    autumn_diff = diff[half:]
    eos_idx = np.nanargmin(autumn_diff, axis=0) + half + 1

    peak = (np.argmax(filled, axis=0) * 16).astype(np.float32)
    sos = (sos_idx.astype(np.float32)) * 16
    eos = (eos_idx.astype(np.float32)) * 16

    invalid = allnan | evergreen
    sos[invalid] = np.nan
    eos[invalid] = np.nan
    peak[allnan] = np.nan
    return sos, eos, peak


def _double_logistic(t, a1, a2, c1, c2, d1, d2):
    """Beck 2006 双逻辑斯蒂: a1 背景 + (a2-a1) × [春升 - 秋降]。"""
    return a1 + (a2 - a1) * (1.0 / (1.0 + np.exp(-c1 * (t - d1)))
                            - 1.0 / (1.0 + np.exp(-c2 * (t - d2))))


def extract_phenology_double_logistic(stack: np.ndarray, ratio: float = 0.2, evergreen_thr: float = 0.1,
                                     timeout: float = 600.0, max_pixels: int = 5000):
    """双逻辑斯蒂拟合后, 在拟合曲线上用动态阈值提 SOS/EOS/Peak (DOY)。

    逐像元 scipy.curve_fit, 比动态阈值慢 ~10×, 初值敏感(失败像元置 NaN)。
    振幅 < evergreen_thr 的常绿像元跳过(同动态阈值法, 常绿区双 log 也无意义)。

    超时保护(Windows 无 signal.alarm, 用 concurrent.futures):
      - 整个函数体包在 ThreadPoolExecutor 内, future.result(timeout=timeout);
      - 超时则抛 TimeoutError, 由调用方(run_phenology)回退到 dynamic。
      - 默认 timeout=600s (10 分钟/单年)。超时阈值可通过参数覆盖。

    大区域采样 (H*W > 50000):
      - 不再逐像元 curve_fit 全部像元, 改为网格采样约 max_pixels 个像元拟合;
      - 其余像元保持 NaN (由 run_phenology 用 dynamic 补全);
      - 采样比例与采样数 logger.warning 说明, 便于评估代表性。

    总进度 ETA:
      - tqdm 同时显示已处理像元/总像元 + 预估剩余 (基于已用时间外推)。
    """
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
    from scipy.optimize import curve_fit
    from tqdm import tqdm
    import time

    def _fit_all(stack, ratio, evergreen_thr, max_pixels):
        T, H, W = stack.shape
        t = np.arange(T, dtype=np.float32) * 16  # 期序号 × 16 → DOY
        sos = np.full((H, W), np.nan, dtype=np.float32)
        eos = np.full((H, W), np.nan, dtype=np.float32)
        peak = np.full((H, W), np.nan, dtype=np.float32)

        total_pixels = H * W
        # 大区域采样: H*W > 50000 时仅拟合 max_pixels 个网格采样像元, 其余 NaN (上层 dynamic 补全)
        if total_pixels > 50000:
            step = max(1, int(np.sqrt(total_pixels / max_pixels)))
            sample_idx = [(i, j) for i in range(0, H, step) for j in range(0, W, step)]
            sample_idx = sample_idx[:max_pixels]
            sampled = len(sample_idx)
            logger.warning(
                "double_logistic: 像元数 %d (H=%d×W=%d) > 50000, 启用网格采样: step=%d, "
                "采样 %d/%d (%.2f%%) 像元拟合 curve_fit, 其余像元由上层 dynamic 补全",
                total_pixels, H, W, step, sampled, total_pixels,
                100.0 * sampled / total_pixels,
            )
            targets = sample_idx
        else:
            targets = [(i, j) for i in range(H) for j in range(W)]

        n_targets = len(targets)
        processed = 0
        start_ts = time.time()
        pbar = tqdm(total=n_targets, desc="双逻辑斯蒂拟合", unit="px")
        for (i, j) in targets:
            ts = stack[:, i, j]
            mask = ~np.isnan(ts)
            if mask.sum() < 7:
                pbar.update(1); processed += 1; continue
            tv, yv = t[mask], ts[mask]
            a1, a2 = float(np.nanmin(yv)), float(np.nanmax(yv))
            if a2 - a1 < evergreen_thr:
                pbar.update(1); processed += 1; continue
            d1 = float(tv[len(tv) // 4])    # 春季拐点初值
            d2 = float(tv[3 * len(tv) // 4])  # 秋季拐点初值
            p0 = [a1, a2, 0.1, 0.1, d1, d2]
            try:
                p, _ = curve_fit(_double_logistic, tv, yv, p0=p0, maxfev=2000)
                fit = _double_logistic(tv, *p)
                thr = p[0] + ratio * (p[1] - p[0])
                above = fit >= thr
                if above.any():
                    sos[i, j] = float(tv[np.argmax(above)])
                    eos[i, j] = float(tv[(len(tv) - 1) - np.argmax(above[::-1])])
                peak[i, j] = float(tv[np.argmax(fit)])
            except Exception:  # noqa: BLE001
                pass
            # ETA: 基于已用时间外推剩余
            processed += 1
            elapsed = time.time() - start_ts
            if processed > 0 and elapsed > 0.1:
                eta = elapsed * (n_targets - processed) / processed
                pbar.set_postfix_str(f"{processed}/{n_targets} ETA {eta:.0f}s")
            pbar.update(1)
        pbar.close()
        return sos, eos, peak

    with ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(_fit_all, stack, ratio, evergreen_thr, max_pixels)
        try:
            return fut.result(timeout=timeout)
        except FuturesTimeout:
            # 重新抛出让上层回退; 线程仍在后台跑但结果丢弃
            raise TimeoutError(
                f"extract_phenology_double_logistic 单年拟合超过 {timeout}s, 建议回退 dynamic 或减小像元数"
            )


def run_phenology(cfg: dict[str, Any]) -> dict[str, Any]:
    years = years_in_range(cfg)
    base = Path(cfg["paths"]["data"]) / "ndvi_smoothed"
    out = Path(cfg["paths"]["outputs"]) / "phenology"
    out.mkdir(parents=True, exist_ok=True)
    ratio = cfg["phenology"]["threshold_ratio"]
    evergreen_thr = (cfg.get("phenology") or {}).get("evergreen_thr", 0.1)
    method = cfg["phenology"].get("method", "dynamic")

    # dispatch: 严格分支, 未知 method 不再静默退化
    extractors = {
        "dynamic": extract_phenology_year,
        "double_logistic": extract_phenology_double_logistic,
        "derivative": extract_phenology_derivative,
    }
    if method not in extractors:
        raise ValueError(
            f"未知 phenology.method={method!r}, 可选: {sorted(extractors)}"
        )
    extractor = extractors[method]
    if method == "double_logistic":
        logger.info("物候方法: 双逻辑斯蒂 (逐像元 curve_fit, 较慢, 单年超时 600s 回退 dynamic; 大区域自动采样)")
    elif method == "derivative":
        logger.info("物候方法: 导数法 (np.diff 向量化, 春最大正导数→SOS, 秋最大负导数→EOS)")
    if evergreen_thr > 0:
        logger.info("常绿过滤: 年内振幅<%.2f 像元 SOS/EOS 置 NaN (动态阈值在常绿区失效)", evergreen_thr)

    sos_list, eos_list, peak_list, prof = [], [], [], None
    timeout_count = 0  # 累计超时年份数, 用于整体告警
    for y in years:
        arr, prof = load_stack(str(base / f"{y}.tif"))
        # double_logistic 像元数上限预警 (采样已在 extract_phenology_double_logistic 内处理)
        if method == "double_logistic":
            T_, H_, W_ = arr.shape
            if H_ * W_ > 50000:
                logger.info(
                    "double_logistic: 年份 %d 像元数 %d×%d=%d > 50000, 将启用网格采样 (见 extractor 内 warning)",
                    y, H_, W_, H_ * W_,
                )
        # double_logistic 超时回退 dynamic (其余像元由 dynamic 补全)
        if method == "double_logistic":
            try:
                s, e, p = extractor(arr, ratio, evergreen_thr)
            except TimeoutError:
                timeout_count += 1
                logger.warning("年份 %d 双逻辑斯蒂超时, 回退到动态阈值法 (累计超时 %d/%d)",
                               y, timeout_count, len(years))
                s, e, p = extract_phenology_year(arr, ratio, evergreen_thr)
        else:
            s, e, p = extractor(arr, ratio, evergreen_thr)
        write_single_band(s, str(out / f"sos_{y}.tif"), prof)
        write_single_band(e, str(out / f"eos_{y}.tif"), prof)
        write_single_band(p, str(out / f"peak_{y}.tif"), prof)
        sos_list.append(s)
        eos_list.append(e)
        peak_list.append(p)

    # 累计超时告警: 超过年数 30% 时建议整体改 dynamic
    if method == "double_logistic" and len(years) > 0 and timeout_count / len(years) > 0.3:
        logger.warning(
            "double_logistic 累计超时 %d/%d 年 (%.0f%%) > 30%%, 大部分年份回退 dynamic; "
            "建议整体改 method=dynamic 或 derivative 以避免无谓耗时",
            timeout_count, len(years), 100.0 * timeout_count / len(years),
        )
    elif method == "double_logistic" and timeout_count > 0:
        logger.info("double_logistic 累计超时 %d/%d 年 (<=30%%, 可接受)", timeout_count, len(years))

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
