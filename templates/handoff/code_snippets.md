# 核心代码段落（Code Snippets）

> 供 CC 写报告"核心代码"附录节取用。从 src/ 真实代码摘取，可直接引用。

## (1) GEE service-account 认证（src/gee_auth.py）

```python
def init_gee(cfg):
    key_file = cfg["gee"]["key_file"]
    with open(key_file, "r", encoding="utf-8") as f:
        info = json.load(f)
    email = info["client_email"]
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(key_file)
    import ee
    creds = ee.ServiceAccountCredentials(email, str(key_file))
    ee.Initialize(creds)  # 不传 project: 用 SA 默认 project
```

## (2) GEE 下载 NDVI（src/gee_download.py）

```python
def export_ndvi_year(cfg, year, region, tiled=False):
    col = (ee.ImageCollection("MODIS/061/MOD13A2")
           .filterDate(f"{year}-01-01", f"{int(year)+1}-01-01").select("NDVI"))
    n = col.size().getInfo()
    img = col.toBands().multiply(0.0001).rename([_band_name(i) for i in range(n)])
    out = str(Path(cfg["paths"]["data"]) / "ndvi" / f"{year}.tif")
    return export_image(img, region, out, base_scale=cfg["data"]["scale"])
```

## (3) SG 滤波降噪（src/preprocess.py）

```python
def fill_nan_time(stack):
    """沿时间轴线性插值填补 NaN"""
    T = stack.shape[0]
    out = stack.copy()
    idx = np.arange(T)
    for i in range(stack.shape[1]):
        for j in range(stack.shape[2]):
            col = out[:, i, j]
            bad = np.isnan(col)
            if bad.all() or not bad.any():
                continue
            out[:, i, j] = np.interp(idx, idx[~bad], col[~bad])
    return out

def sg_smooth(stack, window=5, polyorder=2):
    filled = fill_nan_time(stack)
    return savgol_filter(filled, window_length=window,
                         polyorder=polyorder, axis=0).astype(np.float32)
```

## (4) 动态阈值物候提取（src/phenology.py）

```python
def extract_phenology_year(stack, ratio=0.2, evergreen_thr=0.1):
    """向量化提取单年 SOS/EOS/Peak (DOY), 常绿振幅过滤"""
    T, H, W = stack.shape
    mn, mx = np.nanmin(stack, axis=0), np.nanmax(stack, axis=0)
    amplitude = mx - mn
    evergreen = amplitude < evergreen_thr  # 常绿/水体/裸地
    thr = mn + ratio * (mx - mn)
    filled = np.where(np.isnan(stack), -np.inf, stack)
    above = filled >= thr[None]
    peak = (np.argmax(filled, axis=0) * 16).astype(np.float32)
    sos = (np.argmax(above, axis=0).astype(np.float32)) * 16
    last = (T - 1) - np.argmax(above[::-1], axis=0)
    eos = (last.astype(np.float32)) * 16
    invalid = np.isnan(stack).all(axis=0) | ~above.any(axis=0) | evergreen
    sos[invalid] = np.nan; eos[invalid] = np.nan
    return sos, eos, peak
```

## (5) Theil-Sen + Mann-Kendall 趋势（src/utils.py）

```python
def sen_mk_cube(cube):
    """逐像元 Sen 斜率 + MK Z 统计量"""
    import pymannkendall as mk
    Y, H, W = cube.shape
    slope = np.full((H, W), np.nan, dtype=np.float32)
    z = np.full((H, W), np.nan, dtype=np.float32)
    for i in range(H):
        for j in range(W):
            ts = cube[:, i, j].astype(float)
            if np.isnan(ts).all():
                continue
            ts = np.nan_to_num(ts, nan=np.nanmean(ts))
            r = mk.original_test(ts)
            slope[i, j] = r.slope
            z[i, j] = 0.0 if r.z is None else r.z
    return slope, z
```

## (6) 5 级趋势分类（src/ndvi_trend.py）

```python
def classify_ndvi(slope, z, slope_thr, z_crit):
    out = np.zeros(slope.shape, dtype=np.int8)
    sig = np.abs(z) >= z_crit
    deg, imp = slope < -slope_thr, slope > slope_thr
    out[deg & sig] = 1; out[deg & ~sig] = 2; out[~deg & ~imp] = 3
    out[imp & ~sig] = 4; out[imp & sig] = 5
    return out
```

## 核心库对照表（任务书风格）

| 库 | 用途 |
|---|---|
| numpy | 数值处理、多维数组 |
| matplotlib | 可视化 NDVI 曲线及物候点 |
| scipy.signal | Savitzky-Golay 平滑（savgol_filter）|
| earthengine-api | GEE 数据下载（MODIS NDVI/LAI/GPP）|
| pymannkendall | Sen-MK 趋势检验 |
| rasterio | 栅格数据读写 |

开发环境：Spyder 或 VSCode。
