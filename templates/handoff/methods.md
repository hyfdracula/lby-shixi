# Methods（方法）

> 本文件是 lby-shixi 第一阶段产出的**方法素材**，供第二阶段 CC 撰写论文 Methods 节直接取用。数值/参数由 build_handoff 从 config 填入。

## 数据来源

研究使用 {时段} MODIS 系列遥感产品（Google Earth Engine 云平台获取），统一为 EPSG:4326（WGS84）坐标参考，空间分辨率 {500m/降采样}，无效像元以 -9999 哨兵填充后转 NaN：

| 参数 | 产品（GEE Asset） | 原始时间分辨率 | 比例因子 | 用途 |
|---|---|---|---|---|
| NDVI/EVI | MODIS/061/MOD13A2 | 16 天 | ×0.0001 | 绿度/物候主参数 |
| LAI | MODIS/061/MOD15A2H | 8 天→16 天合成 | ×0.1 | 叶面积（印证） |
| GPP | MODIS/061/MOD17A2HGF | 8 天→16 天合成 | ×0.1 | 光合生产力（印证） |
| 土地覆盖 | MODIS/061/MCD12Q1 | 年（2020） | — | IGBP 植被分类 |

LAI/GPP 原始 8 天合成按 16 天窗口均值重采样，与 NDVI 时相对齐。

## 预处理：Savitzky-Golay 滤波降噪

遥感时序受云、气溶胶、观测几何影响含噪声，采用 Savitzky-Golay（S-G）滤波沿时间轴平滑重构。S-G 在局部窗口内以最小二乘拟合多项式，相较滑动平均能更好保留物候特征点（峰值、拐点）。本研究窗口长度 {w}、多项式阶数 {p}，并先沿时间轴线性插值填补缺失期。进一步以年均 NDVI < 0.05 阈值掩膜水体/建筑/裸地等无效像元。

## 趋势分析：Theil-Sen + Mann-Kendall

逐像元采用 Theil-Sen 中位斜率（抗异常值）结合 Mann-Kendall 显著性检验（双边，α=0.05，|Z|≥1.96）。Sen 斜率定义为所有点对斜率的中位数：Slope = Median((x_j − x_i)/(j − i))，∀ j > i。

按斜率方向 × 显著性划分 5 级。**NDVI 趋势**用 `slope_threshold={ndvi_slope_thr}`（NDVI/yr）；**物候趋势**用独立 `pheno_slope_threshold={pheno_slope_thr}` DOY/yr（物候斜率量级 0.1–2 DOY/yr，与 NDVI 不同，混用会导致近全"无变化"误判）。

## 物候提取：动态阈值法 + 常绿过滤

基于 NDVI 时间序列，用动态阈值提取春季绿返期（SOS）、秋季枯黄期（EOS）、生长峰值期（Peak）：
NDVI_threshold = NDVI_min + α × (NDVI_max − NDVI_min)，α = {threshold_ratio}。
SOS = 年内首次达阈值期，EOS = 末次达阈值期，Peak = 年内最大值期。向量化实现（np.argmax），效率远超逐像元循环。

**常绿过滤**：年内 NDVI 振幅（max−min）< `evergreen_thr={evergreen_thr}` 的像元（常绿林/水体/裸地）SOS/EOS 置 NaN——动态阈值在常绿区失效（全年高 NDVI→阈值≈min→首达/末达误判为期首/期末，典型误判 SOS≈DOY 16、EOS≈DOY 348、生长季≈336 天）。Peak 保留。

## 多源印证

NDVI 反映绿度但在高生物量区饱和，LAI（叶面积指数）与 GPP（总初级生产力）分别从冠层结构与光合固碳角度刻画植被状态。三源趋势方向一致时，可区分"变绿"（NDVI 上升）与"增产生理活性"（GPP 上升），结论更稳健。

## 定量归因建议（供 Discussion 撰写）

- **偏相关分析**：以 NDVI 为因变量，气温/降水为自变量，计算偏相关系数，分离气候驱动的 NDVI 变化分量。
- **残差趋势法**：建立 NDVI 与气候因子的多元回归模型，预测值代表气候驱动部分，观察值减预测值的残差趋势即人为贡献（生态工程/土地利用）。

## 复现性

- **参数**：SG 窗口 {w}/阶 {p}，物候 α={threshold_ratio}，常绿阈值 {evergreen_thr}，NDVI 斜率阈值 {ndvi_slope_thr}，物候斜率阈值 {pheno_slope_thr} DOY/yr，显著性 |Z|≥1.96。
- **数据源**：GEE MOD13A2 / MOD15A2H / MOD17A2HGF / MCD12Q1（V061）。
- **代码**：`src/`（gee_download / preprocess / phenology / ndvi_trend / phenology_trend / multi_source），`run_all.py` 五阶段编排，全部开源可复现。
