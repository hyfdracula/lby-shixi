# 环境坑(已踩并修, 代码内自动处理)

> 先跑 `python check_env.py -c config.yaml` 一键自检 (Python 包 + pandoc + PROJ + 代理 + GEE 连通), 全绿再继续。

## 1. PROJ/GDAL 被 PostgreSQL 污染(最常见)

**症状**: rasterio 写/读带 CRS(EPSG:4326) 的 GeoTIFF 报
`CRSError: proj.db contains DATABASE.LAYOUT.VERSION.MINOR=N whereas >=5 expected`。

**根因**: 装了 PostgreSQL(+PostGIS) 后, 系统 `PROJ_LIB`/`GDAL_DATA` 被设成 PostgreSQL 旧版
(`C:\Program Files\PostgreSQL\17\share\contrib\postgis-3.6\proj`), 与 rasterio 的 GDAL 不匹配。
注意 pyproj 的 proj.db 版本也可能不匹配, 必须用 **rasterio wheel 自带的 proj_data**。

**修复**(代码入口顶部 `src/utils.py` 已做):
```python
import os
for k in ("PROJ_LIB", "PROJ_DATA", "GDAL_DATA"):
    os.environ.pop(k, None)          # 清 PostgreSQL 污染
import rasterio
rdir = os.path.dirname(rasterio.__file__)
for sub, envk in [("proj_data","PROJ_LIB"),("proj_data","PROJ_DATA"),("gdal_data","GDAL_DATA")]:
    p = os.path.join(rdir, sub)
    if os.path.isdir(p): os.environ[envk] = p
```

## 2. GEE 认证"project not found"

**症状**: `ee.Initialize(credentials, project="xxx")` 报 `Project 'projects/xxx' not found`。

**修复**: **不传 project**, 用 `ee.Initialize(credentials)`(service account 默认 project)。
详见 references/gee-setup.md。

## 3. MODIS 投影 sinusoidal → clip 经纬度 BBox 失败

**症状**: `Image.clip: Unable to transform edge ... from SR-ORG:6974 to EPSG:4326`。

**根因**: MODIS 原始投影 SR-ORG:6974(sinusoidal), 手动 clip 经纬度 BBox 投影转换失败。

**修复**: getDownloadURL 加 `"crs": "EPSG:4326"`, **不手动 img.clip(region)**, 让 GEE 导出时
统一重投影裁剪。

## 4. 大区域 500m 超 50MB 限制 → 分块

**症状**: `Total request size (XX bytes) must be <= 50331648 bytes`。

**根因**: 全省 500m × 23 波段 > 50MB。

**修复**: 分块下载(2×2 仍超则 3×3, 每块 34MB<50MB), rasterio merge 拼接, `force_scale` 强制 500m:
config `download.ndvi_tiles: [3,3]`。`export_image_tiled` + `force_scale` 已实现。

## 5. NDVI 与 LC 分辨率不一致 → 形状不匹配

**症状**: 大区域 NDVI 降采样(1860m)而 LC 未降(500m), `by_veg_stats` 报
`boolean index did not match ... size 329 vs 1221`。

**修复**: 读 LC 时最近邻重采样对齐 NDVI grid: `utils.load_lc_aligned(lc_path, target_shape)`。

## 6. matplotlib 中文方块

**症状**: 图里"森林/草地"等中文变方块。

**修复**: `plt.rcParams["font.sans-serif"]=["Microsoft YaHei","SimHei"]` + `axes.unicode_minus=False`(viz.apply_bw_style 已做)。

## 7. 向日葵跨国(若用远程)

**症状**: 开 WARP → 出口 IP 美国 → 向日葵(Oray)异地登录拦截。

**修复**: `run_with_warp.py` 跑 GEE 前自动 `warp-cli connect`、跑完(含异常)`disconnect`,
向日葵只在 GEE 运行几分钟内可能断。不用向日葵则 WARP 一直开无妨。

## 8. WindowsApps python.exe 占位符

**症状**: `python -c "print('ok')"` 报“指定的登录会话不存在”或 `where python` 指向
`C:\Users\<用户>\AppData\Local\Microsoft\WindowsApps\python.exe` 且文件大小为 0。

**根因**: Windows 商店 Python alias 抢占 PATH, 这不是可用解释器。

**修复**: 安装正式 Python 3.11+ 并重新打开终端, 或在命令中显式使用真实解释器路径。
运行前用 `where python` 和 `python -c "import docx, PIL, yaml"` 验证, 再执行报告生成脚本。
