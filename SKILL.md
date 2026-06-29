---
name: lby-shixi
description: This skill should be used when generating a GEE/MODIS remote-sensing practicum project or report for vegetation phenology extraction, NDVI trend analysis, SOS/EOS/Peak metrics, and Chinese course-style deliverables.
---

# lby-shixi · 遥感植被物候期提取实习生成器

地理大数据实习"基于遥感植被参数的植被物候期提取"的一键生成器。紧扣任务书 5 天流程,
交互式收集参数 → 生成完整项目 → 跑通 → 按选定风格产出报告。

## 触发场景

用户提出"物候提取"、"NDVI趋势"、"SOS/EOS/Peak"、"MODIS 植被物候"、
"GEE 植被参数分析"、"遥感实习报告"或"lby-shixi"时, 使用本 skill。

## 核心理念

- **紧扣任务书**: 围绕"物候提取"主题(NDVI/EVI/LAI/GPP/SIF + 植被类型, >15年, ≤0.5°,
  SG滤波 + 动态阈值 SOS + Sen-MK 趋势), 不发散到无关方向。
- **真数据不伪造**: 全部数值来自 GEE 实际下载与计算, 报告只填真实结果。
- **配置驱动**: 一个 config.yaml 决定研究区/参数/方法, 换区只改 roi。

## ⚠️ 交互规则（intake 分两类，触发后即开始）

**intake 分两类处理，别一刀切**：
- **离散选项项**（数据时段 / 植被参数 / 空间分辨率 / 档位 / 物候方法 / 趋势检验 / SG / 分类口径 / 报告格式 / 出图风格 / 结构风格）→ **必须用 `AskUserQuestion` 按键点选**，不要用文本列选项让用户打字。
- **自由文本项**（姓名 / 学号 / 研究区名 / GEE key 路径）→ **直接用文本让用户打字输入**，**不要**套 AskUserQuestion 的"我现在就给 / 其他(打字补)"伪选项（AskUserQuestion 没有纯文本输入框，套这种选项反而绕弯、多此一举）。

⚠️ `AskUserQuestion` 是 **deferred 工具**（默认不加载 schema，直接调会失败/以为"环境没有"）。触发后先 `ToolSearch`（query 填 `select:AskUserQuestion`）加载它，再对**离散选项项**调 AskUserQuestion；**自由文本项直接文本问**。不要因"调不了 / 没这个工具"误判环境——先 ToolSearch 加载。仅 Codex 或加载后仍确无此工具，全部退回文本分批。

## 依赖检测(启动先做)

**一键自检**: `python check_env.py -c config.yaml` (Python 包 + pandoc + PROJ + 代理 + GEE 连通), 全绿再继续。各项明细与排错见 references/env-pitfalls.md:

1. **Python 库**: `pip install -r templates/requirements.txt`
   (earthengine-api/numpy/scipy/rasterio/pymannkendall/matplotlib/pyproj/pyyaml/tqdm/requests/python-docx)
2. **GEE key**: 让用户提供本地 service-account JSON 路径, `python -m src.gee_auth -c config.yaml` 测连通;
   没有 key 时按 references/gee-setup.md 自注册
3. **代理(国内)**: GEE 是 Google, 国内需 WARP/Clash; 不用向日葵则 WARP 一直开

## GEE key 原则

- 不在 skill 中公开或默认使用任何私人 key。
- intake 时收集 `gee.key_file` 绝对路径; **用户没有 key 时主动提醒"找作者要"**; 若留空, 先生成项目, 但提醒下载步骤无法运行。
- key 文件不得提交 git、截图或写进报告。`.gitignore` 已排除 `*.json`/`*credentials*`。
- 需要注册或排错时, 见 [references/gee-setup.md](references/gee-setup.md)。

## 项目介绍(intake 开始前展示给用户)

```
📋 地理大数据实习报告生成器

帮你一键完成「基于遥感植被参数的植被物候期提取」实习报告全流程。特别鸣谢我儿子程昱翔对制图工作的素材提供。

三阶段:
  阶段一 🔧 数据处理: 14问收集信息 → GEE下载 → 分析物候 → 出图打包
  阶段二 ✍️ 初稿: CC 读 handoff 素材自写 report_draft.md（中间产物，非最终交付）
  阶段三 🎯 终排: report_docx_builder 重排成稳定最终 docx

最终产出: 📄 {roi}植被物候实习报告_{name}.docx（桌面双击即开）

准备好了吗? 开始第一个问题 ⬇️
```

## 固定值(不询问, 直接写 config)

**lby 侧固定**: `report.format=docx, viz.style=color`(彩色出图)。**第二阶段已内化**: CC 读 handoff + 深度写作(scene感知/motivation驱动/citation补强), 不依赖外部写作 skill。**两个阶段都要跑**(写作 + report_docx_builder 排版)才算交付。

## intake: 14 问(触发后即开始, 先 ToolSearch 加载 AskUserQuestion)

> 离散选项项用 AskUserQuestion 按键; 自由文本项(姓名/学号/研究区/key/动机)直接文本打字。

**第 1 问** 姓名 **[文本]**(无默认, 必填, 直接打字)
**第 2 问** 学号 **[文本]**(无默认, 必填, 直接打字)
> 班级 `地信23` / 学院 `林学院` / 指导教师 `梁博毅` 固定写入 config。

**第 3 问** 研究区 **[文本]**(省/市名 或 bbox, 如"邵阳市""湖南省""新疆"; 直接打字)
**第 4 问** 数据时段 **[选项]**(2001-2020(推荐,>15年) / 2003-2022 / 自定义)
**第 5 问** 植被参数 **[选项]**(仅 NDVI / NDVI+LAI / NDVI+LAI+GPP(多源推荐) / 全选含EVI/SIF)
**第 6 问** 空间分辨率 **[选项]**(250m(精细) / 500m(推荐) / 1000m(省时))
**第 7 问** 档位 **[选项]**(50% 仅 NDVI 趋势(快) / 100% 含物候(推荐) / 全部像元无掩膜)
**第 8 问** GEE key 路径 **[文本]**(没有 key 提醒"找作者要"; 默认留空下载前补齐)
**第 9 问** 物候提取方法 **[选项]**(动态阈值 α=0.2(推荐) / 双逻辑斯蒂拟合(慢) / 导数法)
**第 10 问** 趋势检验 **[选项]**(Sen+MK 5 级(推荐) / 线性回归 / 两者都做)
**第 11 问** SG 滤波窗口/阶数 **[选项]**(窗口 3 阶 2(保细节) / 窗口 5 阶 2(推荐) / 窗口 7 阶 3(更平滑))
**第 12 问** 植被分类口径 **[选项]**(IGBP 4 类:森林/草地/农田/湿地(推荐) / IGBP 7 类(更细) / 自定义)
**第 13 问** 初始动机 **[文本]**(一句话描述核心论点, 引导 CC 写作; 例"基于 MODIS 数据分析湖南省植被物候时空变化特征"; 留空则 CC 自动推断)
**第 14 问** 降 AI 程度 **[选项]**(无(常规,默认) / 轻度(减AI句式) / 中度(课程作业推荐) / 深度(严格检测场景))

### 联动规则
- 第 5 问选仅 NDVI → 后续只下 NDVI; 选多源 → 对应下 LAI/GPP
- 第 9 问选动态阈值 → 自动 `threshold_ratio=0.2`
- 第 13 问为空 → CC 自动推断动机
- 第 14 问选降AI程度 → CC 按对应 humanize_tier 约束文风(writing_rationale_matrix 体现)

## 预计时间估算(intake 后告知, 用户确认再开始)

粗估公式 (面积万km² × 年数 × 参数权重 × 分辨率系数 ÷ 档位系数 × 1.5 ÷ 下载并行系数 = 分钟):
- 面积: 省 ~10-20万km², 市 ~1-5万, 县 ~0.5-1万
- 参数权重: 仅NDVI=1, +多源×1.5, +EVI/SIF×2
- 分辨率系数: 500m分块=1, 降采样=0.5
- 档位系数: 70%=0.7, 100%=1
- 下载并行系数: 跨年 ThreadPoolExecutor, max_workers=6 实测提速 ~4 倍 → ÷4 (config.download.max_workers 可调, GEE 限流时降到 3-4)
- 参考(并行): 湖南(20×20×1.5×1÷1÷4)≈33min; 玉门(1.8×20×1×1÷0.7÷4)≈19min

```
📊 预计耗时: 约 X 小时 (按上面公式算; GEE 下载是大头, 实际看配额/网络)
  · 下载(500m分块+多源N年): ~X分钟
  · 预处理(SG): ~X分钟
  · 趋势+物候: ~X分钟
  · 报告: ~10分钟
确认开始? (回车继续 / 改参数重填)
```

## setup: 生成项目(intake 确认后)

1. 复制 `templates/` 内文件到用户工作区; 报告 logo 已随 `templates/report/assets/` 一起复制
2. 生成 `config.yaml`(填研究区/时段/参数/分辨率/key/档位/方法/课程封面字段/报告格式)
3. 研究区边界: 省/市→DataV GeoAtlas 或 GEE FAO/GAUL; 泛区域→预设 bbox/拆省(见 references/roi-boundary.md)
4. 边界: `fetch_boundary.py <adcode>` 取研究区 geojson+bbox; logo 在 `report/assets/bilin_logo.png`(build_handoff 自动嵌封面 cover.docx)

## 维护: 同步 skill 副本

D 盘 `lby-shixi` 目录作为主副本维护。改完后运行:

```powershell
.\sync_lby_shixi.ps1 -Mirror
```

脚本会同步到 `~\.claude\skills\lby-shixi`; 若桌面存在 `Desktop\lby-shixi`, 也会同步。避免只改备份目录而 Claude Code 继续加载旧版。

## run: 5 天流程(对应任务书)

⚠️ **Bash cwd 不持久**(坑5): Claude Code 每次 `cd X && cmd` 的 cd 只在当次有效, 下次重置到 session 默认(C:\Users\19161)。所有涉及相对路径(./data ./outputs ./handoff)的脚本, **每个命令前都要 cd 到项目工作区绝对路径**: `cd "C:/Users/19161/Desktop/项目目录" && python ...`。

```
python -m src.gee_auth -c config.yaml       # 下载前先测 GEE 连通
python run_all.py -c config.yaml            # D1下载预处理→D2 NDVI趋势→D3物候SOS→D4物候趋势
python -m src.multi_source -c config.yaml   # 多源 LAI/GPP(若选)
python make_geo_figs.py config.yaml         # 地理要素空间图(若选)
```

环境坑(PROJ/PostgreSQL 冲突、GEE 认证不传 project、WARP 代理、分块保 500m)
代码内已自动处理, 详见 references/env-pitfalls.md。

## handoff: 第一阶段产出数据包(供 CC 第二阶段自写)

第一阶段**不出 PDF/Word**, 产出 `handoff/` 数据包(图+数据+专业文本), 由 CC 第二阶段自写专业论文(不调用外部"写作 skill"):

```
python build_handoff.py -c config.yaml   # run_all 跑完后执行
```

产出 `handoff/`:
- `figures/` — 全套图(趋势/物候/多源/地理, 从 outputs/ 复制; 物候空间图叠加研究区边界红色高亮)
- `data/stats.json` — 真实统计
- `methods.md` — **专业方法素材**(SG/Theil-Sen+MK/动态阈值/多源, 含公式+参数+定量归因+核心库表+复现性)
- `study_area.md` — 研究区(地理/气候/生态, 含【CC填】)
- `results_summary.md` — 结果摘要(NDVI趋势/物候/多源, 真值从 stats.json 填)
- `core_claims.md` — 核心声明+证据+边界
- `captions.md` — 图号+图题+解读
- `code_snippets.md` — 核心代码段落(GEE/SG/物候/Sen+MK, 供附录)
- `cover.docx` — 封面(北林校徽+24pt标题+信息栏+日期, 按老师模板)
- `handoff_meta.json` — 元信息

⚠️ build_handoff 末尾检查【CC填】残留(study_area), CC 手填后再进入第二阶段。

## 第二阶段: 写作(CC 读 handoff 自写 report_draft.md, 已内化 深度写作流程)

**handoff/ 素材已足够 CC 写出完整 12000 字报告**(公式/真值/claim/图注齐备), 不依赖任何外部 skill:

1. **先读全套 handoff 素材**(项目工作区下):
   - `handoff/methods.md` — 专业方法素材(SG/Theil-Sen+MK/动态阈值/多源, 含公式+参数+定量归因+核心库表) → 写第 3 章"研究方法"
   - `handoff/study_area.md` — 研究区(地理/气候/生态, 已含【CC填】补完) → 写第 2 章"研究区概况"
   - `handoff/results_summary.md` — 结果摘要(NDVI趋势/物候/多源, 真值从 stats.json 填好) → 写第 4 章"结果与分析"
   - `handoff/core_claims.md` — 核心声明+证据+边界 → 写第 5 章"讨论"和第 6 章"结论"
   - `handoff/captions.md` — 图号+图题+解读 → 正文插图时直接引用
   - `handoff/code_snippets.md` — 核心代码段落(GEE/SG/物候/Sen+MK) → 写附录"核心代码"
   - `handoff/data/stats.json` — 真实数值, 正文表格/对比从这取
2. **深度写作流程**(内化15步)——详见 [`references/stage2-writing-guide.md`](references/stage2-writing-guide.md)（config镜像→source_map→source_inventory/evidence_bank/figure_asset_map/claim_register→research→citation→motivation确认→section_blueprints→writing_rationale_matrix→build→integrity_check）:

   - **motivation 写作驱动**: 按第13问动机作为核心论点主轴，引导全文论证方向（植被改善驱动、物候变化机制等；第13问只管动机，不管 scene）
   - **citation 补强**: 正文引用 15-20 条关键文献（MODIS/SG/Sen-MK/动态阈值/北京植被等），可结合 web 检索补充
   - **writing rationale**: 每段有"论点→证据→解释"三层，关键数值必须有像元级统计支撑（不伪造）
3. **第二阶段必须落盘的中间产物**(全部在 `paper_rewriting_output/`, 不调用外部写作 skill):
   - `lby_config.json` / `lby_config.md`
   - `source_map.md`, `source_inventory.md`, `reference_materials/source_index.md`
   - `research_dossier.md`, `sota_gap_map.md`, `exemplar_learning_dossier.md`, `style_profile.md`
   - `motivation_options_after_research.md`, `confirmed_motivation.md`
   - `citation_support_bank.md`
   - `evidence_bank.md`, `figure_asset_map.md`, `claim_register.md`
   - `section_blueprints.md`, `writing_rationale_matrix.md`
   - `integrity_check.md`
   - `report_draft.md`
4. **按课程实习报告结构落 report_draft.md**(目标 ≥12000 字, ⛔禁止 journal/IMRaD 风格):

**⛔ report_draft.md 第一行必须是 `## 一、项目简介`，不是 `## 摘要`。禁止"摘要+关键词"开头、"第1章 绪论"、"Abstract"、"Introduction"、IMRaD 结构。**

章节结构(唯一固定, 禁止变体):
   - **一、项目简介**(约 1200 字): 1.1 背景与意义 + 1.2 目标与内容
   - **二、数据与方法**(约 2500 字): 2.1 技术说明(核心库) + 2.2 数据来源(表格) + 2.3 研究方法(2.3.1-2.3.5) + 2.4 多源印证策略
   - **三、实验步骤**(约 600 字): ①数据下载 ②预处理(SG) ③NDVI趋势 ④物候提取 ⑤物候趋势
   - **四、结果与分析**(约 4500 字): 4.1 NDVI趋势(4.1.1整体/4.1.2分植被) + 4.2 物候(4.2.1空间格局/4.2.2趋势+按植被类型) + 4.3 多源LAI/GPP + 4.4 结论
   - **五、讨论与展望**(约 1500 字): 驱动机制 + Peak延迟 + 多源意义 + 方法局限 + 未来工作
   - **六、核心代码**: GEE下载/SG/物候/Sen-MK/分类 + 核心库对照表
   - **七、参考文献**(约 15-20 条, 可结合 web 检索补)
   - 附录: 图件汇总
5. **写真值不伪造**: 所有数值/趋势方向/物候日期必须来自 `handoff/data/stats.json`, 不杜撰。
6. **图位标记**: 正文 `![](handoff/figures/xxx.png)` + Caption 图注(图号+题+解读, 从 captions.md 取), 第三阶段 report_docx_builder 会按栅格重排。
7. **Stage2 自检**(进入第三阶段前, 人工查 `paper_rewriting_output/integrity_check.md`, 不跑论文级脚本):
   - 字数 ≥ 12000 中文(去代码块); 第一行 = `## 一、项目简介`(非摘要/journal)
   - 所有数值有 `stats.json` 锚定; 无 `{xxx}`/【CC填】占位残留
   - 4.1/4.2/4.3/4.4 每节 ≥ 500 字; 4.2.2 重点节 ≥ 800 字
   - 18 产物齐(`paper_rewriting_output/` 下)
8. **输出**: `paper_rewriting_output/report_draft.md`(Markdown) — 供第三阶段 report_docx_builder 重新排版。

📝 **第二阶段产出是初稿, 不是最终成品。必须跑第三阶段才能交付。**

### ⚠️ 第二阶段完成 ≠ 最终成品(必读)

第二阶段(CC 自写)产出 `paper_rewriting_output/report_draft.md` / `handoff/report_draft.docx` 后,
**这只是初稿, 格式不稳定**(表格可能错位 / 图位漂移 / 字体不齐 / 封面缺)。

**还有第三阶段(可选但强烈建议)**: 用 `report_docx_builder.py` 把 report_draft.md + handoff/figures/ 重新排版成稳定最终 docx,
保证交付质量:单一北林封面 + 标题层级正确 + 每行最多 2 张图的图组 + 图注 Caption + Heading 1/2/3 正确映射。

```
python report_docx_builder.py --project-root . --output "桌面/{roi}植被物候实习报告_{name}.docx"
```

**别停在第二阶段**, 看到初稿就接着跑第三阶段(下方)。

## 第三阶段: 最终 DOCX 稳定排版(report_docx_builder.py)

第二阶段产出初稿 Markdown 后, **固定用 `report_docx_builder.py`** 从 `paper_rewriting_output/report_draft.md` + `handoff/` 重新构建最终 Word 文档, 不再用逐行硬拼或空表格拼图。

**默认命令：**
```
python report_docx_builder.py --project-root . --output "桌面/{roi}植被物候实习报告_{name}.docx"
```

**行为说明：** 直接用 CC 第二阶段写的 report_draft.md 排版。不存在则报错（无模板填充捷径，CC 必须先完整跑第二阶段）。

生成器必须保证:
- Markdown 表格原样进入 DOCX, 不得 `continue` 跳过真实数据表;
- 连续图组按紧凑栅格排版: **每行最多 2 张**(2张=一排2, 3张=2+1, 4张=2+2, 5张=2+2+1, 6张=2+2+2, 依此类推); 单张图才单图居中;
- 每张图都有 `Caption` 样式图注, 图和图注同格/相邻, 图组使用无边框表格, 单元格不得为空;
- `##/###/####` 分别映射 Word `Heading 1/2/3`, 不压扁标题层级;
- 按植被类型统计图（`veg_sos_yearly`、`veg_eos_yearly`、`veg_peak_yearly`、`SOS_veg_bar`、`EOS_veg_bar`、`Peak_veg_bar`、`veg_SOS_trend_stacked`、`veg_EOS_trend_stacked`、`veg_Peak_trend_stacked`）优先插入 `4.2.2 整体植被物候期年际时空变化趋势` 正文, 不得只丢进附录;
- 未在正文出现的 `handoff/figures/*.png` 进入“附录A 输出图件汇总”, 保证全套图保留;
- 封面对齐优秀样板: A4 页面、北林 logo 约 8.8 cm、标题/副标题 24 pt 楷体加粗、信息栏 15 pt 楷体、日期写作“YYYY 年 M 月 D 日”; 封面信息从 `config.yaml` 读取, 不硬编码姓名、学号或研究区; 不照搬样板里姓名/指导教师跑到第二页的分页缺陷;
- “核心代码”节优先读取 `handoff/code_snippets.md`, 按优秀示例课件的模块化代码展示方式输出 6 个核心代码模块和核心库对照表。

输出: `report_final.docx` 或用户指定的最终 DOCX 路径。

## 提交

最终 DOCX 报告 + `paper_rewriting_output/` 第二阶段写作中间件 + handoff 数据包 + 全套图 + 代码。截止日期写入 `config.course.deadline`。

## references 子文档

- [gee-setup.md](references/gee-setup.md) — GEE 认证 + key 失效自注册步骤
- [env-pitfalls.md](references/env-pitfalls.md) — PROJ/PostgreSQL、WARP 代理、分块 500m 坑
- [roi-boundary.md](references/roi-boundary.md) — 研究区边界获取(省/市/泛区域)
- [report-styles.md](references/report-styles.md) — 报告风格(单一课程实习, 正文由第二阶段 CC 产出)
- [report-generation.md](references/report-generation.md) — Markdown/DOCX 生成与依赖
