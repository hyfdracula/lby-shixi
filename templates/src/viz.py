"""出图: 黑白简洁风(默认, 神偏好) / 彩色风。viz.style 控制 (bw/color), 出图脚本调 set_style。"""
from __future__ import annotations

import json
from pathlib import Path

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

# 出图风格: "bw"(黑白, 默认) / "color"(彩色)
_STYLE = "bw"


def set_style(style: str = "bw") -> None:
    """设全局出图风格 (bw/color)。出图脚本读 config viz.style 后调一次。"""
    global _STYLE
    _STYLE = style


def _cmap() -> str:
    """色图名: bw=Greys, color=viridis。"""
    return "Greys" if _STYLE == "bw" else "viridis"


def _discrete_cmap(n: int):
    """离散色图: bw=Greys(n), color=tab10/tab20。"""
    if _STYLE == "color":
        return plt.get_cmap("tab10" if n <= 10 else "tab20", max(n, 1))
    return plt.get_cmap("Greys", max(n, 1))


def _line_color(idx: int = 0):
    """线/点/柱色: bw=黑, color=tab10。"""
    if _STYLE == "color":
        return plt.get_cmap("tab10")(idx % 10)
    return "black"


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
    """在 ax 上叠加研究区边界(GeoJSON) 描边高亮。bw=深灰, color=红色。"""
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
    bc = "#333333" if _STYLE == "bw" else "#E60012"
    for ring in rings:
        if ring and isinstance(ring[0], (list, tuple)) and len(ring[0]) >= 2:
            xs, ys = zip(*ring)
            ax.plot(xs, ys, color=bc, lw=2)  # 省界描边: bw=深灰, color=红


def plot_yearly_trend(years, values, title, out, ylabel="NDVI") -> str:
    apply_bw_style()
    years = np.asarray(years); values = np.asarray(values, dtype=float)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(years, values, "-o", color=_line_color(0), markerfacecolor="white", markersize=5)
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


def plot_phenology_diagram(raw, smooth, sos_idx, peak_idx, eos_idx, ratio, out) -> str:
    """物候提取示意图: 原始NDVI + SG平滑 + 动态阈值线 + SOS/Peak/EOS 标注点。"""
    apply_bw_style()
    fig, ax = plt.subplots(figsize=(8, 5))
    t = np.arange(len(raw))
    ax.plot(t, np.asarray(raw), "o", color="lightgray", markersize=3, alpha=0.6, label="原始 NDVI")
    ax.plot(t, np.asarray(smooth), "-", linewidth=2.5, label="SG 滤波")
    # 动态阈值线
    s = np.asarray(smooth)
    mn, mx = np.nanmin(s), np.nanmax(s)
    thr = mn + ratio * (mx - mn)
    thr_c = "black" if _STYLE == "bw" else "green"
    ax.axhline(y=thr, color=thr_c, linestyle=":", linewidth=1.5, alpha=0.7, label=f"动态阈值 α={ratio}")
    # SOS/Peak/EOS 标注: bw=黑色+形状区分(o/^/v), color=原蓝/红/橙
    if _STYLE == "bw":
        pts = [(sos_idx, "SOS", "o", -15), (peak_idx, "Peak", "^", 5), (eos_idx, "EOS", "v", -15)]
        for idx, label, marker, off in pts:
            if idx is not None and 0 <= idx < len(smooth):
                ax.plot(idx, smooth[idx], marker, color="black", markersize=10, zorder=5)
                ax.annotate(f"{label}\nDOY≈{idx*16}", xy=(idx, smooth[idx]),
                            xytext=(idx+3, smooth[idx]+off*0.001), fontsize=8, color="black",
                            arrowprops=dict(arrowstyle="->", color="black", lw=1))
    else:
        for idx, label, color, off in [(sos_idx, "SOS", "#2196F3", -15), (peak_idx, "Peak", "#F44336", 5), (eos_idx, "EOS", "#FF9800", -15)]:
            if idx is not None and 0 <= idx < len(smooth):
                ax.plot(idx, smooth[idx], "v", color=color, markersize=10, zorder=5)
                ax.annotate(f"{label}\nDOY≈{idx*16}", xy=(idx, smooth[idx]),
                            xytext=(idx+3, smooth[idx]+off*0.001), fontsize=8, color=color,
                            arrowprops=dict(arrowstyle="->", color=color, lw=1))
    ax.set_xlabel("16 天期序号"); ax.set_ylabel("NDVI")
    ax.set_title("物候期提取示意图 (动态阈值法)")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    _save(fig, out); return out


def plot_pheno_spatial(arr, title, out, vmin=None, vmax=None) -> str:
    apply_bw_style()
    fig, ax = plt.subplots(figsize=(6, 6))
    im = ax.imshow(np.ma.masked_invalid(arr), cmap=_cmap(), vmin=vmin, vmax=vmax)
    ax.set_title(title); ax.axis("off")
    cbar = fig.colorbar(im, fraction=0.046); cbar.set_label("DOY")
    _save(fig, out); return out


def plot_pheno_yearly_lines(years, series, title, out, ylabel="DOY") -> str:
    apply_bw_style()
    fig, ax = plt.subplots(figsize=(6, 4))
    cmap = _discrete_cmap(len(series))
    markers = ["o", "s", "^", "D"]
    for i, (label, vals) in enumerate(series.items()):
        ax.plot(years, vals, "-" + markers[i % len(markers)], color=cmap(i),
                markerfacecolor="white", markersize=5, label=label)
    ax.set_title(title); ax.set_xlabel("Year"); ax.set_ylabel(ylabel)
    ax.legend(frameon=False)
    _save(fig, out); return out


def plot_spatial_class(arr, levels_labels, title, out) -> str:
    apply_bw_style()
    fig, ax = plt.subplots(figsize=(6, 6))
    n = max(levels_labels)
    cmap = plt.get_cmap(_cmap(), n)
    im = ax.imshow(np.ma.masked_equal(arr, 0), cmap=cmap, vmin=1, vmax=n)
    ax.set_title(title); ax.axis("off")
    cbar = fig.colorbar(im, ticks=list(levels_labels.keys()), fraction=0.046)
    cbar.ax.set_yticklabels(list(levels_labels.values()))
    _save(fig, out); return out


def plot_spatial_geo(arr, transform, title, out, levels=None, cmap=None,
                     boundary: str | None = None) -> str:
    """地理参考空间图: 经纬度轴 + 研究区边界高亮 + 指北针 + 比例尺。"""
    apply_bw_style()
    cmap = cmap or _cmap()
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
    cmap = _discrete_cmap(len(ratios))
    ax.pie(ratios, labels=labels, autopct="%1.1f%%",
           colors=[cmap(i) for i in range(len(ratios))],
           wedgeprops=dict(edgecolor="white"))
    ax.set_title(title)
    _save(fig, out); return out


def plot_veg_bar(veg_names, stacked_values, title, out, ylabel="占比 (%)") -> str:
    apply_bw_style()
    fig, ax = plt.subplots(figsize=(7, 4))
    x = np.arange(len(veg_names))
    cmap = _discrete_cmap(len(stacked_values))
    bottom = np.zeros(len(veg_names))
    for i, (cat, vals) in enumerate(stacked_values.items()):
        ax.bar(x, vals, bottom=bottom, color=cmap(i), edgecolor="black", label=cat)
        bottom += np.asarray(vals, dtype=float)
    ax.set_xticks(x); ax.set_xticklabels(veg_names)
    ax.set_title(title); ax.set_ylabel(ylabel)
    # legend 移到图外右侧, 避免遮挡堆叠柱 (bw 模式 frameon=False 仍清晰)
    ax.legend(frameon=False, fontsize=8, bbox_to_anchor=(1.02, 1), loc="upper left", borderaxespad=0)
    fig.tight_layout()
    _save(fig, out); return out


def plot_sen_slopes(veg_names, slopes, title, out, ylabel="Sen 斜率",
                    sample_notes: dict[str, str] | None = None) -> str:
    """按植被类型画 Sen 斜率柱状图。

    Args:
        sample_notes: 植被名 -> 备注 (如 "有效 slope=0" / "lc 无此类")。有备注的柱在柱顶标注,
                      不伪造 0 值。NaN 斜率画透明短虚线柱 (hatch) 以示"该类样本不足"。
    """
    apply_bw_style()
    fig, ax = plt.subplots(figsize=(6.5, 4))
    x = np.arange(len(veg_names))
    slopes_arr = np.asarray(slopes, dtype=float)
    has_nan = np.isnan(slopes_arr)
    # 有效柱: 实心黑柱; NaN 柱: 透明 + 斜线 hatch, 柱高取当前有效柱的 1/3 (仅占位, 不代表数值)
    plot_vals = slopes_arr.copy()
    placeholder = float(np.nanmax(np.abs(slopes_arr))) / 3 if np.isfinite(slopes_arr).any() else 0.001
    bar_hatch = []
    for v in slopes_arr:
        bar_hatch.append("//" if np.isnan(v) else None)
    if np.isfinite(slopes_arr).any():
        plot_vals = np.where(has_nan, placeholder, plot_vals)
    bars = ax.bar(x, plot_vals, color=_line_color(0), edgecolor="black")
    for i, (bar, h) in enumerate(zip(bars, bar_hatch)):
        if h:
            bar.set_hatch(h); bar.set_facecolor("white"); bar.set_alpha(0.6)
    ax.set_xticks(x); ax.set_xticklabels(veg_names)
    ax.set_title(title); ax.set_ylabel(ylabel)
    # 柱顶标注: 有效柱标数值; NaN 柱标 "样本不足" 或 sample_notes 提供的原因
    ymax = float(np.nanmax(np.abs(plot_vals))) if np.isfinite(plot_vals).any() else 1.0
    for i, v in enumerate(slopes_arr):
        name = veg_names[i]
        if np.isnan(v):
            note = (sample_notes or {}).get(name, "样本不足")
            ax.text(i, placeholder + ymax * 0.04, note, ha="center", va="bottom",
                    fontsize=8, color="gray", style="italic")
        else:
            ax.text(i, v + ymax * 0.04 * (1 if v >= 0 else -1), f"{v:.4f}",
                    ha="center", va="bottom" if v >= 0 else "top", fontsize=9)
    # 说明性 legend (bw 模式也要清晰)
    if has_nan.any():
        from matplotlib.patches import Patch
        ax.legend(handles=[Patch(facecolor="white", edgecolor="black", hatch="//", label="样本不足 (slope 全 NaN)")],
                  frameon=False, fontsize=8, loc="upper right")
    _save(fig, out); return out


def plot_slope_compare(slope_mk, slope_lin, title, out,
                       xlabel="Sen-MK 斜率", ylabel="线性回归斜率") -> str:
    """散点对比 Sen-MK vs 线性回归逐像元斜率 + 1:1 参考线 + Pearson 相关系数。

    用于 trend.method=both 时论证两法一致性 (点越贴近 1:1 线、r 越接近 1, 结论越稳健)。
    NaN 自动剔除; 空/全 NaN 时返回 out 但只画参考线并标注 "no valid pixels"。
    """
    apply_bw_style()
    a = np.asarray(slope_mk, dtype=float).ravel()
    b = np.asarray(slope_lin, dtype=float).ravel()
    mask = np.isfinite(a) & np.isfinite(b)
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    if mask.sum() > 1:
        aa, bb = a[mask], b[mask]
        # 散点: bw=黑+alpha, color=蓝
        sc = "black" if _STYLE == "bw" else "#2196F3"
        ax.scatter(aa, bb, s=6, c=sc, alpha=0.35, edgecolors="none")
        # 1:1 参考线
        lo = float(min(aa.min(), bb.min()))
        hi = float(max(aa.max(), bb.max()))
        ax.plot([lo, hi], [lo, hi], "--", color="gray", lw=1.2, label="1:1 参考线")
        # 线性拟合线 (两法整体关系)
        try:
            z = np.polyfit(aa, bb, 1)
            xs = np.linspace(lo, hi, 50)
            ax.plot(xs, np.polyval(z, xs), "-", color="black", lw=1.0,
                    label=f"拟合 y={z[0]:.3f}x{z[1]:+.4f}")
        except Exception:  # noqa: BLE001
            pass
        r = float(np.corrcoef(aa, bb)[0, 1])
        ax.set_title(f"{title}\nPearson r = {r:.4f}  (n={mask.sum()})")
    else:
        ax.plot([0, 1], [0, 1], "--", color="gray", lw=1.0)
        ax.set_title(f"{title}\n(no valid pixels)")
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    _save(fig, out); return out
