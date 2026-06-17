# 研究区边界获取

intake 第 3 问"研究区"输入后, 按类型获取边界填 config.roi。

## 1. 省/直辖市/县名(行政单元, 最常见)

- **DataV GeoAtlas(阿里云, 国内最准)**: 省/市/县 GeoJSON。API 形如
  `https://geo.datav.aliyun.com/areas_v3/bound/{adcode}_full.json`(adcode 为行政码)。
  下载 GeoJSON → 用 `ee.Geometry(geometry)` 或转 bbox。
- **GEE FAO/GAUL/2015**: `FAO/GAUL/2015/level1`(省) / `level2`(市), 直接 `ee.FeatureCollection`
  `.filter(ee.Filter.eq('name1','湖南'))` 取边界。
- rs-urban-monitor 的 `download_county_geojson` / `COUNTY_ASET_ID` 有县级实现可复用。

## 2. 泛区域(东北/华北/长三角/黄河流域...) — 非行政单元

skill 识别为泛区域后, 提示用户三选一:
1. **给 bbox 经纬度**: 用户直接给 [west,south,east,north], 填 config.roi.bbox。
2. **拆成省合并**: 如"东北"= 黑龙江+吉林+辽宁, 分别取省边界合并(union)。
3. **预设大区 bbox**: skill 内置常见大区 bbox:
   - 东北: [118, 38, 135, 54]
   - 华北: [110, 34, 120, 43]
   - 长三角: [118, 28, 123, 34]
   - 黄河流域: [95, 32, 120, 42]

## 3. 用户手输 bbox

直接填 `roi.bbox: [w, s, e, n]`。

## config 字段

```yaml
roi:
  name: hunan              # 用于命名
  bbox: [108.78, 24.64, 114.26, 30.12]   # [west, south, east, north]
  boundary_shp: null       # 有省界 shapefile/geojson 可填, 优先用
```

## 建议

- 实习任务书"随机选一个研究区", 省/市最合适(边界清晰、数据量适中)。
- 整省 500m 分块下载较慢(湖南 3×3≈2h), 市/县级更快。
- 大区(东北/华北)数据量巨大, 建议 demo 先跑或降采样。
