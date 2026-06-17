"""黑白简洁风出图 (神偏好: 白底黑字灰阶, 适合放进 Word 报告)。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

_BW = {
    "figure.facecolor": "white", "axes.facecolor": "white", "axes.edgecolor": "black",
    "axes.labelcolor": "black", "xtick.color": "black", "ytick.color": "black",
    "text.color": "black", "axes.grid": False, "font.family": "sans-serif",
    "axes.spines.top": False, "axes.spines.right": False,
}
_CN_FONTS = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]


def apply_bw_style() -> None:
    plt.rcParams.update(_BW)
    plt.rcParams["font.sans-serif"] = _CN_FONTS
    plt.rcParams["axes.unicode_minus"] = False


def _save(fig, out: str) -> None:
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)


def _plot_boundary(ax, boundary: str) -> None:
    """在 ax 上叠加研究区边界(GeoJSON) 高亮。"""
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
    for ring in rings:
        if ring and isinstance(ring[0], (list, tuple)) and len(ring[0]) >= 2:
            xs, ys = zip(*ring)
            ax.plot(xs, ys, color="#E60012", lw=2)  # 黑色粗线高亮省界


def plot_yearly_trend(years, values, title, out, ylabel="NDVI") -> str:
    apply_bw_style()
    years = np.asarray(years); values = np.asarray(values, dtype=float)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(years, values, "-o", color="black", markerfacecolor="white", markersize=5)
    z = np.polyfit(years, values, 1)
    ax.plot(years, np.polyval(z, years), "--", color="gray", label=f"slope={z[0]:.4f}/yr")
    ax.set_title(title); ax.set_xlabel("Year"); ax.set_ylabel(ylabel)
    ax.legend(frameon=False)
    _save(fig, out); return out


def plot_raw_vs_smooth(raw, smooth, title, out, ylabel="NDVI") -> str:
    apply_bw_style()
    fig, ax = plt.subplots(figsize=(6, 4))
    t = np.arange(len(raw))
    ax.plot(t, np.asarray(raw), "o-", color="lightgray", markersize=4, label="原始")
    ax.plot(t, np.asarray(smooth), "k-", linewidth=2, label="SG 滤波")
    ax.set_title(title); ax.set_xlabel("16 天期序号"); ax.set_ylabel(ylabel)
    ax.legend(frameon=False)
    _save(fig, out); return out


def plot_pheno_spatial(arr, title, out, vmin=None, vmax=None) -> str:
    apply_bw_style()
    fig, ax = plt.subplots(figsize=(6, 6))
    im = ax.imshow(np.ma.masked_invalid(arr), cmap="Greys", vmin=vmin, vmax=vmax)
    ax.set_title(title); ax.axis("off")
    cbar = fig.colorbar(im, fraction=0.046); cbar.set_label("DOY")
    _save(fig, out); return out


def plot_pheno_yearly_lines(years, series, title, out, ylabel="DOY") -> str:
    apply_bw_style()
    fig, ax = plt.subplots(figsize=(6, 4))
    greys = plt.get_cmap("Greys", max(len(series), 1))
    markers = ["o", "s", "^", "D"]
    for i, (label, vals) in enumerate(series.items()):
        ax.plot(years, vals, "-" + markers[i % len(markers)], color=greys(i),
                markerfacecolor="white", markersize=5, label=label)
    ax.set_title(title); ax.set_xlabel("Year"); ax.set_ylabel(ylabel)
    ax.legend(frameon=False)
    _save(fig, out); return out


def plot_spatial_class(arr, levels_labels, title, out) -> str:
    apply_bw_style()
    fig, ax = plt.subplots(figsize=(6, 6))
    n = max(levels_labels)
    cmap = plt.get_cmap("Greys", n)
    im = ax.imshow(np.ma.masked_equal(arr, 0), cmap=cmap, vmin=1, vmax=n)
    ax.set_title(title); ax.axis("off")
    cbar = fig.colorbar(im, ticks=list(levels_labels.keys()), fraction=0.046)
    cbar.ax.set_yticklabels(list(levels_labels.values()))
    _save(fig, out); return out


def plot_spatial_geo(arr, transform, title, out, levels=None, cmap="Greys",
                     boundary: str | None = None) -> str:
    """地理参考空间图: 经纬度轴 + 研究区边界高亮 + 指北针 + 比例尺。"""
    apply_bw_style()
    h, w = arr.shape
    west, north = transform * (0, 0)
    east, south = transform * (w, h)
    extent = [west, east, south, north]
    fig, ax = plt.subplots(figsize=(7, 7))
    if levels:
        n = max(levels)
        cm = plt.get_cmap(cmap, n)
        im = ax.imshow(np.ma.masked_equal(arr, 0), extent=extent, cmap=cm, vmin=1, vmax=n, aspect="auto")
        cbar = fig.colorbar(im, ticks=list(levels.keys()), fraction=0.035, pad=0.02)
        cbar.ax.set_yticklabels(list(levels.values()))
    else:
        im = ax.imshow(np.ma.masked_invalid(arr), extent=extent, cmap=cmap, aspect="auto")
        cbar = fig.colorbar(im, fraction=0.035, pad=0.02)
        cbar.set_label("DOY")
    if boundary:
        _plot_boundary(ax, boundary)
    ax.set_xlabel("经度 (°E)")
    ax.set_ylabel("纬度 (°N)")
    ax.set_title(title)
    ax.annotate("N", xy=(0.93, 0.93), xycoords="axes fraction", ha="center",
                fontsize=13, fontweight="bold", color="black")
    ax.annotate("", xy=(0.93, 0.93), xytext=(0.93, 0.86), xycoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.5))
    bar_y = south + (north - south) * 0.06
    bar_x0 = west + (east - west) * 0.07
    ax.plot([bar_x0, bar_x0 + 1.0], [bar_y, bar_y], "k-", lw=2.5)
    ax.plot([bar_x0, bar_x0], [bar_y - (north - south) * 0.01, bar_y + (north - south) * 0.01], "k-", lw=1)
    ax.plot([bar_x0 + 1.0, bar_x0 + 1.0], [bar_y - (north - south) * 0.01, bar_y + (north - south) * 0.01], "k-", lw=1)
    ax.text(bar_x0 + 0.5, bar_y + (north - south) * 0.02, "≈111 km", ha="center", fontsize=8)
    _save(fig, out); return out


def plot_pie_ratios(ratios, labels, title, out) -> str:
    apply_bw_style()
    fig, ax = plt.subplots(figsize=(5, 5))
    greys = plt.get_cmap("Greys", len(ratios))
    ax.pie(ratios, labels=labels, autopct="%1.1f%%",
           colors=[greys(i) for i in range(len(ratios))],
           wedgeprops=dict(edgecolor="white"))
    ax.set_title(title)
    _save(fig, out); return out


def plot_veg_bar(veg_names, stacked_values, title, out, ylabel="占比 (%)") -> str:
    apply_bw_style()
    fig, ax = plt.subplots(figsize=(6, 4))
    x = np.arange(len(veg_names))
    greys = plt.get_cmap("Greys", max(len(stacked_values), 1))
    bottom = np.zeros(len(veg_names))
    for i, (cat, vals) in enumerate(stacked_values.items()):
        ax.bar(x, vals, bottom=bottom, color=greys(i), edgecolor="black", label=cat)
        bottom += np.asarray(vals, dtype=float)
    ax.set_xticks(x); ax.set_xticklabels(veg_names)
    ax.set_title(title); ax.set_ylabel(ylabel)
    ax.legend(frameon=False, fontsize=8)
    _save(fig, out); return out


def plot_sen_slopes(veg_names, slopes, title, out, ylabel="Sen 斜率") -> str:
    apply_bw_style()
    fig, ax = plt.subplots(figsize=(6, 4))
    x = np.arange(len(veg_names))
    ax.bar(x, slopes, color="black", edgecolor="black")
    ax.set_xticks(x); ax.set_xticklabels(veg_names)
    ax.set_title(title); ax.set_ylabel(ylabel)
    _save(fig, out); return out
