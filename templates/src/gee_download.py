"""GEE 下载 MODIS 植被参数与土地覆盖, 导出 GeoTIFF 到 data/。

导出: ee.Image.getDownloadURL + requests; 智能 scale; 多级重试; crs=EPSG:4326;
  -9999 哨兵填 nodata。大区域支持分块(tiled)下载 + force_scale 强制保留 500m。

数据约定 (无效像素 = -9999):
  data/ndvi/{year}.tif  一年约23期16天 NDVI (多波段 t00..t22, 已 ×0.0001)
  data/lai/{year}.tif   MOD15A2H LAI 8天→16天合成 (波段 Lai_500m, ×0.1)
  data/gpp/{year}.tif   MOD17A2HGF GPP 8天→16天合成 (波段 Gpp, ×0.1)
  data/lc/lc_{year}.tif MCD12Q1 LC_Type1 (单波段 IGBP 整数)
"""
from __future__ import annotations

import logging
import math
import os
from pathlib import Path
from typing import Any

import ee
import requests

from .gee_auth import init_gee
from .utils import ensure_dirs, years_in_range

logger = logging.getLogger(__name__)

NODATA = -9999
SAFE_BYTES = 35_000_000
BYTES_PER_PIXEL = 4
EXPORT_CRS = "EPSG:4326"


def build_roi(cfg: dict[str, Any]) -> ee.Geometry:
    bb = cfg["roi"]["bbox"]
    return ee.Geometry.BBox(bb[0], bb[1], bb[2], bb[3])


def _band_name(i: int) -> str:
    return f"t{i:02d}"


def _stamp_nodata(path: str) -> None:
    import rasterio
    try:
        with rasterio.open(path, "r+") as ds:
            ds.nodata = NODATA
    except Exception as e:  # noqa: BLE001
        logger.warning("stamp nodata failed %s: %s", path, e)


def _smart_scale(region: ee.Geometry, n_bands: int, base_scale: int) -> int:
    try:
        area_m2 = region.area(maxError=1).getInfo()
    except Exception:  # noqa: BLE001
        area_m2 = 1000 * 1e6
    max_px = SAFE_BYTES // BYTES_PER_PIXEL // max(n_bands, 1)
    opt = max(base_scale, int(math.ceil(math.sqrt(area_m2 / max_px)) / 10) * 10)
    return min(opt, 2000)


def export_image(img: ee.Image, region: ee.Geometry, out_path: str,
                 base_scale: int = 500, force_scale: int | None = None) -> str:
    """getDownloadURL 下载。force_scale 指定时只试该 scale (分块保 500m); 否则智能 scale + 重试。"""
    n_bands = max(img.bandNames().length().getInfo(), 1)
    if force_scale:
        scales = [force_scale]
    else:
        opt = _smart_scale(region, n_bands, base_scale)
        scales = list(dict.fromkeys([opt, opt * 2, opt * 4, 1000, 2000]))
    img_c = img.unmask(NODATA, sameFootprint=False)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    last_err = None
    for scale in scales:
        try:
            url = img_c.getDownloadURL({
                "scale": scale, "region": region, "format": "GEO_TIFF", "crs": EXPORT_CRS,
            })
            r = requests.get(url, timeout=300)
            if r.status_code == 200:
                with open(out_path, "wb") as f:
                    f.write(r.content)
                _stamp_nodata(out_path)
                logger.info("导出 %s @ %dm crs=%s (%d bytes, %d bands)",
                            out_path, scale, EXPORT_CRS, len(r.content), n_bands)
                return out_path
            last_err = f"HTTP {r.status_code}"
        except Exception as e:  # noqa: BLE001
            last_err = str(e)
    raise RuntimeError(f"导出失败 {out_path}: {last_err}")


def export_image_tiled(img: ee.Image, bbox: list[float], out_path: str,
                       base_scale: int = 500, tiles: tuple[int, int] = (3, 3)) -> str:
    """分块下载: 把 bbox 切 tiles×tiles 块, 每块 force_scale(base_scale) 下载, rasterio merge。

    force 保证保留 500m 精度; 3×3 时每块 23 波段×500m ≈ 34MB < 50MB。
    """
    import rasterio
    from rasterio.merge import merge

    west, south, east, north = bbox
    dx = (east - west) / tiles[0]
    dy = (north - south) / tiles[1]
    tmp_dir = Path(out_path).parent / ("_" + Path(out_path).stem + "_tiles")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    pieces: list[str] = []
    for i in range(tiles[0]):
        for j in range(tiles[1]):
            sub = ee.Geometry.BBox(west + i * dx, south + j * dy,
                                   west + (i + 1) * dx, south + (j + 1) * dy)
            tmp = str(tmp_dir / f"tile_{i}_{j}.tif")
            logger.info("分块 [%d,%d] @ %dm (force) ...", i, j, base_scale)
            export_image(img, sub, tmp, base_scale=base_scale, force_scale=base_scale)  # force_scale 保 500m; 已知局限: GEE 投影变换实际分辨率可能微偏, 严格需核验
            pieces.append(tmp)

    srcs = [rasterio.open(p) for p in pieces]
    try:
        merged, transf = merge(srcs)
    finally:
        for s in srcs:
            s.close()
    prof = srcs[0].profile.copy()
    prof.update(width=merged.shape[2], height=merged.shape[1],
                count=merged.shape[0], transform=transf, nodata=NODATA)
    with rasterio.open(out_path, "w", **prof) as dst:
        dst.write(merged)
    for p in pieces:
        try:
            os.remove(p)
        except OSError:
            pass
    try:
        tmp_dir.rmdir()
    except OSError:
        pass
    logger.info("分块合并完成 -> %s (%d 波段)", out_path, merged.shape[0])
    return out_path


def export_ndvi_year(cfg, year, region, tiled: bool = False) -> str:
    col = (ee.ImageCollection("MODIS/061/MOD13A2")
           .filterDate(f"{year}-01-01", f"{int(year)+1}-01-01").select("NDVI"))
    n = col.size().getInfo()
    img = col.toBands().multiply(0.0001).rename([_band_name(i) for i in range(n)])
    out = str(Path(cfg["paths"]["data"]) / "ndvi" / f"{year}.tif")
    if tiled:
        tiles = tuple(cfg.get("download", {}).get("ndvi_tiles", [3, 3]))
        return export_image_tiled(img, list(cfg["roi"]["bbox"]), out, cfg["data"]["scale"], tiles)
    return export_image(img, region, out, base_scale=cfg["data"]["scale"])


def export_evi_year(cfg, year, region, tiled: bool = False) -> str:
    """MOD13A2 EVI (与 NDVI 同 16 天产品, 波段 EVI, ×0.0001) -> data/evi/{year}.tif。"""
    col = (ee.ImageCollection("MODIS/061/MOD13A2")
           .filterDate(f"{year}-01-01", f"{int(year)+1}-01-01").select("EVI"))
    n = col.size().getInfo()
    img = col.toBands().multiply(0.0001).rename([_band_name(i) for i in range(n)])
    out = str(Path(cfg["paths"]["data"]) / "evi" / f"{year}.tif")
    if tiled:
        tiles = tuple(cfg.get("download", {}).get("ndvi_tiles", [3, 3]))
        return export_image_tiled(img, list(cfg["roi"]["bbox"]), out, cfg["data"]["scale"], tiles)
    return export_image(img, region, out, base_scale=cfg["data"]["scale"])


def export_lai_year(cfg, year, region) -> str:
    """MOD15A2H LAI (8天, 波段 Lai_500m) -> 16天均值合成 (约23期), 已 ×0.1。"""
    start = ee.Date(f"{year}-01-01")
    periods = []
    for k in range(23):
        s = start.advance(k * 16, "day"); e = s.advance(16, "day")
        m = (ee.ImageCollection("MODIS/061/MOD15A2H").filterDate(s, e)
             .select("Lai_500m").mean().multiply(0.1))
        periods.append(m.rename(_band_name(k)))
    img = ee.Image.cat(periods)
    out = str(Path(cfg["paths"]["data"]) / "lai" / f"{year}.tif")
    return export_image(img, region, out, base_scale=cfg["data"]["scale"])


def export_gpp_year(cfg, year, region) -> str:
    """MOD17A2HGF GPP (8天, 波段 Gpp) -> 16天均值合成 (约23期), 已 ×0.1。"""
    start = ee.Date(f"{year}-01-01")
    periods = []
    for k in range(23):
        s = start.advance(k * 16, "day"); e = s.advance(16, "day")
        m = (ee.ImageCollection("MODIS/061/MOD17A2HGF").filterDate(s, e)
             .select("Gpp").mean().multiply(0.1))
        periods.append(m.rename(_band_name(k)))
    img = ee.Image.cat(periods)
    out = str(Path(cfg["paths"]["data"]) / "gpp" / f"{year}.tif")
    return export_image(img, region, out, base_scale=cfg["data"]["scale"])


def export_sif_year(cfg, year, region) -> str | None:
    """SIF (日光荧光) 导出。MODIS 体系无 SIF, 用 config.data.products.sif 指定的 GEE asset
    (如 TROPOMI SIF / CSIF Tao2025)。asset 未配置或不可访问时跳过 + 提示。"""
    sif_asset = (cfg.get("data", {}).get("products", {}) or {}).get("sif")
    if not sif_asset:
        logger.warning("SIF 未配置 asset (config.data.products.sif, 如 TROPOMI/CSIF); 跳过 SIF 导出")
        return None
    col = (ee.ImageCollection(sif_asset)
           .filterDate(f"{year}-01-01", f"{int(year)+1}-01-01"))
    n = col.size().getInfo()
    if not n:
        logger.warning("SIF asset %s 在 %d 年无数据; 跳过", sif_asset, year)
        return None
    img = col.mean()
    out = str(Path(cfg["paths"]["data"]) / "sif" / f"{year}.tif")
    return export_image(img, region, out, base_scale=cfg["data"]["scale"])


def export_landcover(cfg, year, region) -> str:
    img = (ee.ImageCollection("MODIS/061/MCD12Q1").filterDate(f"{year}-01-01", f"{int(year)+1}-01-01")
           .first().select("LC_Type1"))
    out = str(Path(cfg["paths"]["data"]) / "lc" / f"lc_{year}.tif")
    return export_image(img, region, out, base_scale=cfg["data"]["scale"])


def download_all(cfg, params=("ndvi", "lc"), ndvi_tiled: bool = False) -> None:
    """主下载入口。params: 子集 ('ndvi','lai','gpp','lc'); ndvi_tiled=True 大区域保500m。"""
    ensure_dirs(cfg)
    init_gee(cfg)
    region = build_roi(cfg)
    years = years_in_range(cfg)
    for y in years:
        if "ndvi" in params:
            export_ndvi_year(cfg, y, region, tiled=ndvi_tiled)
        if "evi" in params:
            export_evi_year(cfg, y, region, tiled=ndvi_tiled)
        if "lai" in params:
            export_lai_year(cfg, y, region)
        if "gpp" in params:
            export_gpp_year(cfg, y, region)
        if "sif" in params:
            export_sif_year(cfg, y, region)
    if "lc" in params:
        export_landcover(cfg, years[-1], region)
    logger.info("下载完成: years=%s params=%s ndvi_tiled=%s", years, params, ndvi_tiled)


if __name__ == "__main__":
    import sys
    from .utils import load_config
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    cfg = load_config(sys.argv[1] if len(sys.argv) > 1 else "config.yaml")
    if cfg["date"].get("demo"):
        cfg["date"]["end"] = cfg["date"]["start"]
    download_all(cfg, params=("ndvi", "lc"))
