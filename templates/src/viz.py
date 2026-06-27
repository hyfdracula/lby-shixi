"""出图 v5: 彩色专业 + 图干净(图例/比例尺不覆盖) + 专业配色 + 高分辨率。

v5 改进(对比 v4):
  - dpi 400 (印刷级)
  - 图例全移图外右侧 (bbox_to_anchor, 不覆盖数据区)
  - plot_spatial_geo 去掉指北针+比例尺 (学 image19 纯地图+colorbar, 不覆盖)
  - 专业 PALETTE 配色 (自然色调, 替换 tab10)
色图语义: NDVI 趋势 RdYlGn / 物候趋势 RdYlGn_r(绿延迟红提前) / DOY viridis
viz.style 控制 (color 默认 / bw)。
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

_BW = {
    "figure.facecolor": "white", "axes.facecolor": "white", "axes.edgecolor": "black",
    "axes.labelcolor": "black", "xtick.color": "black", "ytick.color": "black",
    "text.color": "black", "axes.grid": False, "font.family": "sans-serif",
    "axes.spines.top": False, "axes.spines.right": False,
}
_CN_FONTS = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]

# 专业配色 PALETTE (自然色调, 替换 tab10, 色盲友好)
_PALETTE = ["#264653", "#2A9D8F", "#E9C46A", "#F4A261", "#E76F51",
            "#606C38", "#283618", "#DDA15E", "#BC6C25", "#003049"]

_STYLE = "color"

_TREND_CMAP = "RdYlGn"
_PHENO_TREND_CMAP = "RdYlGn_r"
_DOY_CMAP = "viridis"
_BW_CMAP = "Greys"


def set_style(style: str = "color") -> None:
    global _STYLE
    _STYLE = style


def _cmap() -> str:
    return _BW_CMAP if _STYLE == "bw" else _DOY_CMAP


def _trend_cmap() -> str:
    return _BW_CMAP if _STYLE == "bw" else _TREND_CMAP


def _pheno_trend_cmap() -> str:
    return _BW_CMAP if _STYLE == "bw" else _PHENO_TREND_CMAP


def _discrete_cmap(n: int):
    """离散色图(折线/柱/饼): bw=Greys(n), color=专业 PALETTE。"""
    if _STYLE == "color":
        return ListedColormap(_PALETTE[:max(n, 1)] * (n // 10 + 1))
    return plt.get_cmap("Greys", max(n, 1))


def _line_color(idx: int = 0):
    """线/点/柱色: bw=黑, color=PALETTE。"""
    if _STYLE == "color":
        return _PALETTE[idx % len(_PALETTE)]
    return "black"


def apply_bw_style() -> None:
    plt.rcParams.update(_BW)
    plt.rcParams["font.sans-serif"] = _CN_FONTS
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 400


def _title(ax, text: str) -> None:
    ax.set_title(text, fontsize=15, fontweight="bold", pad=12)


def _legend_outside(ax, fontsize: int = 10) -> None:
    """图例统一移到图外右侧, 不覆盖数据区。"""
    ax.legend(frameon=False, fontsize=fontsize, bbox_to_anchor=(1.02, 1),
              loc="upper left", borderaxespad=0)


def _save(fig, out: str) -> None:
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, dpi=400, bbox_inches="tight")
    plt.close(fig)


def _plot_boundary(ax, boundary: str) -> None:
    """研究区边界: bw=深灰, color=浅灰 #555(学 image19, 不抢眼)。"""
    try:
        gj = json.load(open(boundary, encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return
    feats = gj.get("features", [gj] if gj.get("type") == "Feature" else [])
    rings: list = []
    for f in feats:
        geom = f.get("geometry", f)
        if not geom:
            continue
        gt = geom.get("type")
        coords = geom.get("coordinates", [])
        if gt == "Polygon":
            rings.extend(coords)
        elif gt == "MultiPolygon":
            for poly in coords:
                rings.extend(poly)
    bc = "#333333" if _STYLE == "bw" else "#555555"
    for ring in rings:
        if ring and isinstance(ring[0], (list, tuple)) and len(ring[0]) >= 2:
            xs, ys = zip(*ring)
            ax.plot(xs, ys, color=bc, lw=1.8)


def plot_yearly_trend(years, values, title, out, ylabel="NDVI") -> str:
    apply_bw_style()
    years = np.asarray(years); values = np.asarray(values, dtype=float)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(years, values, "-o", color=_line_color(0), markerfacecolor="white", markersize=6, lw=2)
    z = np.polyfit(years, values, 1)
    fit_c = "gray" if _STYLE == "bw" else _PALETTE[4]
    ax.plot(years, np.polyval(z, years), "--", color=fit_c, lw=1.5, label=f"slope={z[0]:.4f}/yr")
    _title(ax, title); ax.set_xlabel("Year", fontsize=11); ax.set_ylabel(ylabel, fontsize=11)
    _legend_outside(ax)
    _save(fig, out); return out


def plot_raw_vs_smooth(raw, smooth, title, out, ylabel="NDVI") -> str:
    apply_bw_style()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    t = np.arange(len(raw))
    raw_c = "lightgray" if _STYLE == "bw" else "#999999"
    sm_c = "black" if _STYLE == "bw" else _PALETTE[0]
    ax.plot(t, np.asarray(raw), "o-", color=raw_c, markersize=4, label="原始")
    ax.plot(t, np.asarray(smooth), "-", color=sm_c, linewidth=2.2, label="SG 滤波")
    _title(ax, title); ax.set_xlabel("16 天期序号", fontsize=11); ax.set_ylabel(ylabel, fontsize=11)
    _legend_outside(ax)
    _save(fig, out); return out


def plot_phenology_diagram(raw, smooth, sos_idx, peak_idx, eos_idx, ratio, out, daily_interp=True) -> str:
    """物候提取示意图: 原始NDVI点 + SG平滑曲线 + 动态阈值线 + SOS/Peak/EOS 标注。

    daily_interp=True: SG平滑 PCHIP 插值到逐日(DOY 0-364), 平滑美观; x 轴 DOY;
        SOS/Peak/EOS 标在 DOY (期idx×16)。
    """
    apply_bw_style()
    fig, ax = plt.subplots(figsize=(9, 5))
    raw = np.asarray(raw); smooth = np.asarray(smooth)
    T = len(smooth)
    raw_c = "lightgray" if _STYLE == "bw" else "#999999"
    sm_c = "black" if _STYLE == "bw" else _PALETTE[0]
    if daily_interp and T < 365:
        from scipy.interpolate import PchipInterpolator
        x = np.arange(T, dtype=float) * 16  # 期 DOY (0,16,...,352)
        x_new = np.arange(365, dtype=float)  # 逐日 DOY 0-364
        sm_d = PchipInterpolator(x, np.nan_to_num(smooth))(x_new)
        ax.plot(x, np.nan_to_num(raw), "o", color=raw_c, markersize=3, alpha=0.5, label="原始 NDVI (16天合成)")
        ax.plot(x_new, sm_d, "-", color=sm_c, linewidth=2.5, label="SG + PCHIP 逐日")
        s_disp, t_disp = sm_d, x_new
    else:
        t_disp = np.arange(T); s_disp = smooth
        ax.plot(t_disp, raw, "o", color=raw_c, markersize=3, alpha=0.6, label="原始 NDVI")
        ax.plot(t_disp, smooth, "-", color=sm_c, linewidth=2.5, label="SG 滤波")
    mn, mx = np.nanmin(smooth), np.nanmax(smooth)
    thr = mn + ratio * (mx - mn)
    thr_c = "black" if _STYLE == "bw" else _PALETTE[1]
    ax.axhline(y=thr, color=thr_c, linestyle=":", linewidth=1.8, alpha=0.8, label=f"动态阈值 α={ratio}")
    def _doy(i):
        return i * 16 if i is not None else None
    if _STYLE == "bw":
        pts = [(_doy(sos_idx), "SOS", "o", -15), (_doy(peak_idx), "Peak", "^", 5), (_doy(eos_idx), "EOS", "v", -15)]
        for idx, label, marker, off in pts:
            if idx is not None and 0 <= int(idx) < len(s_disp):
                ax.plot(idx, s_disp[int(idx)], marker, color="black", markersize=11, zorder=5)
                ax.annotate(f"{label}\nDOY≈{idx:.0f}", xy=(idx, s_disp[int(idx)]),
                            xytext=(idx + 12, s_disp[int(idx)] + off * 0.001), fontsize=9, color="black",
                            arrowprops=dict(arrowstyle="->", color="black", lw=1))
    else:
        for idx, label, color, off in [(_doy(sos_idx), "SOS", _PALETTE[0], -15), (_doy(peak_idx), "Peak", _PALETTE[4], 5), (_doy(eos_idx), "EOS", _PALETTE[3], -15)]:
            if idx is not None and 0 <= int(idx) < len(s_disp):
                ax.plot(idx, s_disp[int(idx)], "o", color=color, markersize=11, zorder=5)
                ax.annotate(f"{label}\nDOY≈{idx:.0f}", xy=(idx, s_disp[int(idx)]),
                            xytext=(idx + 12, s_disp[int(idx)] + off * 0.001), fontsize=9, color=color,
                            arrowprops=dict(arrowstyle="->", color=color, lw=1.2))
    ax.set_xlabel("DOY (天)", fontsize=11); ax.set_ylabel("NDVI", fontsize=11)
    _title(ax, "物候期提取示意图 (动态阈值法 + PCHIP 逐日)")
    _legend_outside(ax, fontsize=9)
    _save(fig, out); return out


def plot_pheno_spatial(arr, title, out, vmin=None, vmax=None) -> str:
    apply_bw_style()
    fig, ax = plt.subplots(figsize=(9, 6))
    im = ax.imshow(np.ma.masked_invalid(arr), cmap=_cmap(), vmin=vmin, vmax=vmax)
    _title(ax, title); ax.axis("off")
    cbar = fig.colorbar(im, fraction=0.046, shrink=0.85); cbar.set_label("DOY", fontsize=11)
    _save(fig, out); return out


def plot_pheno_yearly_lines(years, series, title, out, ylabel="DOY") -> str:
    apply_bw_style()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    cmap = _discrete_cmap(len(series))
    markers = ["o", "s", "^", "D"]
    for i, (label, vals) in enumerate(series.items()):
        ax.plot(years, vals, "-" + markers[i % len(markers)], color=cmap(i),
                markerfacecolor="white", markersize=6, lw=2, label=label)
    _title(ax, title); ax.set_xlabel("Year", fontsize=11); ax.set_ylabel(ylabel, fontsize=11)
    _legend_outside(ax)
    _save(fig, out); return out


def plot_spatial_class(arr, levels_labels, title, out) -> str:
    apply_bw_style()
    fig, ax = plt.subplots(figsize=(9, 6))
    n = max(levels_labels)
    cmap = plt.get_cmap(_trend_cmap(), n)
    im = ax.imshow(np.ma.masked_equal(arr, 0), cmap=cmap, vmin=1, vmax=n)
    _title(ax, title); ax.axis("off")
    cbar = fig.colorbar(im, ticks=list(levels_labels.keys()), fraction=0.046, shrink=0.85, pad=0.02)
    cbar.ax.set_yticklabels(list(levels_labels.values()), fontsize=10)
    _save(fig, out); return out


def plot_spatial_geo(arr, transform, title, out, levels=None, cmap=None,
                     boundary: str | None = None, kind: str = "ndvi") -> str:
    """地理参考空间图 v5: 纯地图+colorbar(无指北针/比例尺覆盖), aspect=equal 保地理比例。"""
    apply_bw_style()
    if cmap is None:
        if kind == "pheno_trend":
            cmap = _pheno_trend_cmap()
        elif kind == "ndvi" or levels:
            cmap = _trend_cmap()
        else:
            cmap = _cmap()
    h, w = arr.shape
    west, north = transform * (0, 0)
    east, south = transform * (w, h)
    extent = [west, east, south, north]
    geo_w = max(east - west, 1e-6)
    geo_h = max(north - south, 1e-6)
    fig_h = max(4.0, 12.0 * geo_h / geo_w * 0.82)
    fig, ax = plt.subplots(figsize=(12, fig_h))
    if levels:
        n = max(levels)
        cm = plt.get_cmap(cmap, n)
        im = ax.imshow(np.ma.masked_equal(arr, 0), extent=extent, cmap=cm, vmin=1, vmax=n, aspect="equal")
        cbar = fig.colorbar(im, ticks=list(levels.keys()), fraction=0.035, pad=0.02, shrink=0.85)
        cbar.ax.set_yticklabels(list(levels.values()), fontsize=10)
    else:
        im = ax.imshow(np.ma.masked_invalid(arr), extent=extent, cmap=cmap, aspect="equal")
        cbar = fig.colorbar(im, fraction=0.035, pad=0.02, shrink=0.85)
        cbar.set_label("DOY", fontsize=11)
    if boundary:
        _plot_boundary(ax, boundary)
    ax.set_xticks([]); ax.set_yticks([])  # 纯地图(学 image19), 无指北针/比例尺覆盖
    for spine in ax.spines.values():
        spine.set_visible(False)
    _title(ax, title)
    _save(fig, out); return out


def plot_pie_ratios(ratios, labels, title, out) -> str:
    apply_bw_style()
    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    cmap = _discrete_cmap(len(ratios))
    ax.pie(ratios, labels=labels, autopct="%1.1f%%",
           colors=[cmap(i) for i in range(len(ratios))],
           wedgeprops=dict(edgecolor="white", linewidth=1.5),
           textprops={"fontsize": 10})
    _title(ax, title)
    _save(fig, out); return out


def plot_veg_bar(veg_names, stacked_values, title, out, ylabel="占比 (%)") -> str:
    apply_bw_style()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(veg_names))
    cmap = _discrete_cmap(len(stacked_values))
    bottom = np.zeros(len(veg_names))
    for i, (cat, vals) in enumerate(stacked_values.items()):
        ax.bar(x, vals, bottom=bottom, color=cmap(i), edgecolor="black", label=cat)
        bottom += np.asarray(vals, dtype=float)
    ax.set_xticks(x); ax.set_xticklabels(veg_names, fontsize=11)
    _title(ax, title); ax.set_ylabel(ylabel, fontsize=11)
    _legend_outside(ax, fontsize=9)
    _save(fig, out); return out


def plot_sen_slopes(veg_names, slopes, title, out, ylabel="Sen 斜率",
                    sample_notes: dict[str, str] | None = None) -> str:
    apply_bw_style()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(veg_names))
    slopes_arr = np.asarray(slopes, dtype=float)
    has_nan = np.isnan(slopes_arr)
    plot_vals = slopes_arr.copy()
    placeholder = float(np.nanmax(np.abs(slopes_arr))) / 3 if np.isfinite(slopes_arr).any() else 0.001
    bar_hatch = []
    for v in slopes_arr:
        bar_hatch.append("//" if np.isnan(v) else None)
    if np.isfinite(slopes_arr).any():
        plot_vals = np.where(has_nan, placeholder, plot_vals)
    bar_color = _line_color(0) if _STYLE == "color" else "#333333"
    bars = ax.bar(x, plot_vals, color=bar_color, edgecolor="black")
    for i, (bar, h) in enumerate(zip(bars, bar_hatch)):
        if h:
            bar.set_hatch(h); bar.set_facecolor("white"); bar.set_alpha(0.6)
    ax.set_xticks(x); ax.set_xticklabels(veg_names, fontsize=11)
    _title(ax, title); ax.set_ylabel(ylabel, fontsize=11)
    ymax = float(np.nanmax(np.abs(plot_vals))) if np.isfinite(plot_vals).any() else 1.0
    for i, v in enumerate(slopes_arr):
        name = veg_names[i]
        if np.isnan(v):
            note = (sample_notes or {}).get(name, "样本不足")
            ax.text(i, placeholder + ymax * 0.04, note, ha="center", va="bottom",
                    fontsize=9, color="gray", style="italic")
        else:
            ax.text(i, v + ymax * 0.04 * (1 if v >= 0 else -1), f"{v:.4f}",
                    ha="center", va="bottom" if v >= 0 else "top", fontsize=10)
    if has_nan.any():
        from matplotlib.patches import Patch
        ax.legend(handles=[Patch(facecolor="white", edgecolor="black", hatch="//", label="样本不足 (slope 全 NaN)")],
                  frameon=False, fontsize=9, loc="upper right")
    _save(fig, out); return out


def plot_slope_compare(slope_mk, slope_lin, title, out,
                       xlabel="Sen-MK 斜率", ylabel="线性回归斜率") -> str:
    apply_bw_style()
    a = np.asarray(slope_mk, dtype=float).ravel()
    b = np.asarray(slope_lin, dtype=float).ravel()
    mask = np.isfinite(a) & np.isfinite(b)
    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    if mask.sum() > 1:
        aa, bb = a[mask], b[mask]
        sc = "black" if _STYLE == "bw" else _PALETTE[0]
        ax.scatter(aa, bb, s=8, c=sc, alpha=0.4, edgecolors="none")
        lo = float(min(aa.min(), bb.min()))
        hi = float(max(aa.max(), bb.max()))
        ax.plot([lo, hi], [lo, hi], "--", color="gray", lw=1.2, label="1:1 参考线")
        try:
            z = np.polyfit(aa, bb, 1)
            xs = np.linspace(lo, hi, 50)
            fit_c = "black" if _STYLE == "bw" else _PALETTE[4]
            ax.plot(xs, np.polyval(z, xs), "-", color=fit_c, lw=1.2,
                    label=f"拟合 y={z[0]:.3f}x{z[1]:+.4f}")
        except Exception:  # noqa: BLE001
            pass
        r = float(np.corrcoef(aa, bb)[0, 1])
        ax.set_title(f"{title}\nPearson r = {r:.4f}  (n={mask.sum()})", fontsize=14, fontweight="bold", pad=10)
    else:
        ax.plot([0, 1], [0, 1], "--", color="gray", lw=1.0)
        ax.set_title(f"{title}\n(no valid pixels)", fontsize=14, fontweight="bold", pad=10)
    ax.set_xlabel(xlabel, fontsize=11); ax.set_ylabel(ylabel, fontsize=11)
    _legend_outside(ax, fontsize=9)
    _save(fig, out); return out
