---
name: lby-shixi
description: 地理大数据实习-遥感植被物候期提取一键生成器。紧扣《物候期提取任务书》流程(GEE下载NDVI/LAI/GPP→SG滤波→动态阈值SOS/EOS/Peak→Sen-MK趋势→黑白出图→报告)。交互式问15题(封面/研究区/数据/方法/风格), 自动生成完整项目+跑通+按选定风格出报告。触发"物候提取/NDVI趋势/SOS-EOS-Peak/植被物候实习/lby-shixi"。
---

# lby-shixi · 遥感植被物候期提取实习生成器

地理大数据实习"基于遥感植被参数的植被物候期提取"的一键生成器。紧扣任务书 5 天流程,
交互式收集参数 → 生成完整项目 → 跑通 → 按选定风格产出报告。

## 核心理念

- **紧扣任务书**: 围绕"物候提取"主题(NDVI/EVI/LAI/GPP/SIF + 植被类型, >15年, ≤0.5°,
  SG滤波 + 动态阈值 SOS + Sen-MK 趋势), 不发散到无关方向。
- **真数据不伪造**: 全部数值来自 GEE 实际下载与计算, 报告只填真实结果。
- **配置驱动**: 一个 config.yaml 决定研究区/参数/方法, 换区只改 roi。

## 依赖检测(启动先做)

跑前必须全绿, 否则引导修复(详见 references/env-pitfalls.md):

1. **Python 库**: `pip install -r templates/requirements.txt`
   (earthengine-api/numpy/scipy/rasterio/pymannkendall/matplotlib/pyproj/pyyaml/tqdm/requests/python-docx)
2. **GEE key**: 内置 2 个(见下), `python -m src.gee_auth` 测连通; 失效看 references/gee-setup.md 自注册
3. **代理(国内)**: GEE 是 Google, 国内需 WARP/Clash; 不用向日葵则 WARP 一直开

## 内置 GEE key(2 个, 用户选; 失效自注册)

| key 文件名 | project | 默认路径 |
|---|---|---|
| feisty-gateway-498706-m2-1b9cc04e520c.json | feisty-gateway-498706 | C:/Users/19161/Desktop/长征/ |
| zeta-turbine-498806-j3-e99120f8bd27.json | zeta-turbine-498806 | C:/Users/19161/Desktop/长征/ |

> ⚠️ 若 key 失效/配额耗尽, 自己注册: 见 [references/gee-setup.md](references/gee-setup.md)

## intake: 15 问(AskUserQuestion 分批, 每题给默认可跳过)

### 批 1 · 封面(2 问 + 3 固定)
1. 姓名　2. 学号
> 班级 `地信23` / 学院 `林学院` / 指导教师 `梁博毅` 固定自动填

### 批 2 · 研究区与数据(5 问)
3. **研究区**(省/市名 或 bbox; 泛区域如"东北"看 references/roi-boundary.md 处理)
4. 数据时段(默认 2001–2020, >15 年)
5. 植被参数(NDVI/EVI/LAI/GPP/SIF 全选 / 仅 NDVI / 自选)
6. 空间分辨率(500m 分块保精度 / 自动降采样省时)
7. GEE key(2 选 1 / 自填路径)

### 批 3 · 方法(5 问)
8. 档位(任务书 70% 仅 NDVI 趋势 / 100% 含物候 SOS+物候趋势)
9. 物候提取方法(动态阈值 α=0.2 / 双逻辑斯蒂 / 可调 α)
10. 趋势检验(Sen+MK 5 级 / 线性回归)
11. SG 滤波窗口/阶数(默认 5/2)
12. 植被分类口径(IGBP→森林/草地/农田/湿地 / 自定义)

### 批 4 · 输出(3 问)
13. 报告格式(Word .docx / PDF / Markdown)
14. 出图风格(黑白学术 / 彩色 + 是否地理要素指北针比例尺)
15. **报告结构风格**(A nature 期刊风 / B PaperSpine 学术编排 / C 中文学报风 / D 课程实习报告 / E 自由)

## 预计时间估算(intake 后告知, 用户确认再开始)

按研究区面积/年数/参数/分辨率/档位估算(参考湖南 500m+多源+20年+100%≈2–2.5h):

```
📊 预计耗时: 约 X 小时
  · 下载(500m分块+多源N年): ~X分钟
  · 预处理(SG): ~X分钟
  · 趋势+物候: ~X分钟
  · 报告: ~10分钟
确认开始? (回车继续 / 改参数重填)
```

## setup: 生成项目(intake 确认后)

1. 复制 `templates/`(src/ + run_all.py + multi_source.py + make_*.py + requirements.txt) 到用户工作区
2. 生成 `config.yaml`(填研究区/时段/参数/分辨率/key/档位/方法)
3. 研究区边界: 省/市→DataV GeoAtlas 或 GEE FAO/GAUL; 泛区域→预设 bbox/拆省(见 references/roi-boundary.md)
4. 生成报告骨架 `report_template.md`(封面北林 logo + 居中信息, 见 assets/bilin_logo.png)

## run: 5 天流程(对应任务书)

```
python run_all.py -c config.yaml            # D1下载预处理→D2 NDVI趋势→D3物候SOS→D4物候趋势
python -m src.multi_source -c config.yaml   # 多源 LAI/GPP(若选)
python make_geo_figs.py config.yaml         # 地理要素空间图(若选)
```

环境坑(PROJ/PostgreSQL 冲突、GEE 认证不传 project、WARP 代理、分块保 500m)
代码内已自动处理, 详见 references/env-pitfalls.md。

## report: 按选定风格生成

按 intake 第 15 问的风格, 套对应结构生成报告(数值来自真实结果, 不伪造):

- **A nature 风**: context→gap→approach→result→implication, 结论前置, 参考 nature-writing skill
- **B PaperSpine**: 完整 IMRaD + motivation/rationale, 参考 paper-spine skill
- **C 中文学报**: 引言→材料方法→结果→讨论→结论, 重数据表格
- **D 课程实习**: 流程为主, 图文并茂, 贴合任务书 5 天
- **E 自由**: 按用户描述定制

封面规范(必须遵循, templates/fix_cover.py 自动处理):
- 单标题"基于遥感植被参数的植被物候期提取——以{研究区}为例"(黑体·加粗·居中·18pt)
- 北林校徽居中(md 用 ![](path) 无 alt 避免 caption)
- 学院/班级/学号/姓名/指导教师 居中(地信23/林学院/梁博毅 固定)
- "一、项目简介"前分页(封面后正文起新页)
- 研究区边界: 空间图叠加省界**红色描边**(#E60012, lw=2), viz._plot_boundary 默认红
转换后跑 `python fix_cover.py output.docx` 精调封面字体/居中/分页。

## 提交

报告 Word/PDF + 全套图 + 代码。任务书截止 2026-07-10。

## references 子文档

- [gee-setup.md](references/gee-setup.md) — GEE 认证 + key 失效自注册步骤
- [env-pitfalls.md](references/env-pitfalls.md) — PROJ/PostgreSQL、WARP 代理、分块 500m 坑
- [roi-boundary.md](references/roi-boundary.md) — 研究区边界获取(省/市/泛区域)
- [report-styles.md](references/report-styles.md) — 4 种报告风格结构细则
