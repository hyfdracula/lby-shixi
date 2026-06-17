"""生成假 NDVI + 植被类型 GeoTIFF, 离线验证全链路 (preprocess→趋势→物候→出图)。

不联网、不依赖 GEE。用高斯季节曲线 + 年际趋势 + 噪声合成 NDVI,
不同植被类型赋予不同物候参数 (峰值期/振幅/趋势), 用于验证代码无 bug、
出图样式、SOS 提取与 Sen-MK 5 级分类逻辑。

用法:  python make_fake_data.py
然后:  python run_all.py -s preprocess ndvi_trend phenology phenology_trend
"""
from __future__ import annotations

import os

# PROJ/GDAL 数据库冲突修复 (同 src/utils.py): 清 PostgreSQL 污染, 用 rasterio 自带 proj_data
for _k in ("PROJ_LIB", "PROJ_DATA", "GDAL_DATA"):
    os.environ.pop(_k, None)
try:
    import rasterio as _rio

    _rdir = os.path.dirname(_rio.__file__)
    _pd = os.path.join(_rdir, "proj_data")
    if os.path.isdir(_pd):
        os.environ["PROJ_LIB"] = _pd
        os.environ["PROJ_DATA"] = _pd
    _gd = os.path.join(_rdir, "gdal_data")
    if os.path.isdir(_gd):
        os.environ["GDAL_DATA"] = _gd
except Exception:  # noqa: BLE001
    pass

from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_bounds

np.random.seed(42)

YEARS = [2018, 2019, 2020]  # 与 config demo (最近3年) 一致
NPERIOD = 23  # 16天一期
H, W = 120, 100
BBOX = (115.42, 39.45, 117.50, 41.07)  # 北京

# 每种植被: (冬季base, 振幅amp, 峰值期tpeak, 年际趋势/yr)
# IGBP: 2=常绿阔叶林 10=草地 12=农田 11=湿地
VEG_PARAMS: dict[int, tuple[float, float, int, float]] = {
    2: (0.15, 0.55, 11, +0.010),   # 森林: 早峰, 缓慢改善
    10: (0.12, 0.45, 12, +0.006),  # 草地
    12: (0.10, 0.50, 13, +0.012),  # 农田: 改善明显
    11: (0.18, 0.35, 14, -0.004),  # 湿地: 晚峰, 略退化
}


def make_veg_grid() -> np.ndarray:
    g = np.zeros((H, W), dtype=np.int32)
    g[: H // 2, : W // 2] = 2     # 左上 森林
    g[: H // 2, W // 2:] = 10     # 右上 草地
    g[H // 2:, : W // 2] = 12     # 左下 农田
    g[H // 2:, W // 2:] = 11      # 右下 湿地
    return g


def gen_ndvi_year(veg_grid: np.ndarray, year: int) -> np.ndarray:
    """生成 (NPERIOD, H, W) NDVI 立方体。"""
    t = np.arange(NPERIOD)
    sigma = 4.0
    cube = np.full((NPERIOD, H, W), 0.1, dtype=np.float32)
    for igbp, (base, amp, tpeak, trend) in VEG_PARAMS.items():
        mask = veg_grid == igbp
        if not mask.any():
            continue
        peak_year = base + amp + trend * (year - YEARS[0])  # 年际趋势加在峰值
        curve = base + (peak_year - base) * np.exp(-((t - tpeak) ** 2) / (2 * sigma ** 2))
        cube[:, mask] = curve[:, None]
    cube += np.random.normal(0, 0.02, cube.shape).astype(np.float32)
    return np.clip(cube, -0.1, 1.0).astype(np.float32)


def profile(n_bands: int, dtype: str, nodata):
    transform = from_bounds(*BBOX, W, H)
    return {
        "driver": "GTiff", "height": H, "width": W,
        "count": n_bands, "dtype": dtype,
        "crs": "EPSG:4326", "transform": transform, "nodata": nodata,
    }


def main() -> None:
    data = Path("data")
    (data / "ndvi").mkdir(parents=True, exist_ok=True)
    (data / "lc").mkdir(parents=True, exist_ok=True)
    veg_grid = make_veg_grid()

    for y in YEARS:
        cube = gen_ndvi_year(veg_grid, y)
        p = profile(NPERIOD, "float32", None)
        with rasterio.open(data / "ndvi" / f"{y}.tif", "w", **p) as dst:
            for b in range(NPERIOD):
                dst.write(cube[b], b + 1)
        print(f"生成 ndvi/{y}.tif  shape={cube.shape}  均值={cube.mean():.3f}")

    lp = profile(1, "int32", -9999)
    with rasterio.open(data / "lc" / f"lc_{YEARS[-1]}.tif", "w", **lp) as dst:
        dst.write(veg_grid, 1)
    print(f"生成 lc/lc_{YEARS[-1]}.tif  类别={sorted(set(veg_grid.ravel().tolist()))}")
    print("假数据就绪 ✅  接着跑: python run_all.py -s preprocess ndvi_trend phenology phenology_trend")


if __name__ == "__main__":
    main()
