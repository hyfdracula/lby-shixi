# v7 标准报告规范(第三阶段 CC 自写参考)

第三阶段目标: **CC 读 handoff 全套素材, 按本规范自写 report_draft.md(≥12000 中文), 再用 report_docx_builder 排版**。无论 stage2(CC 按 stage2-writing-guide.md 初写)产出什么质量, 第三阶段都保证 v7 标准 —— 这是"手工扩写"的固化, 让任何用户跑到第三阶段都直接得 v7 文档。

> v7 范例: `邵阳市植被物候实习报告_胡扬帆_v7.docx`(10172 中文/39图/22表/最多2张图组/单一封面)。CC 自写时对照此标准。

## 1. 结构与字数(目标 ≥12000 中文)

| 章节 | 字数 | 素材来源 | 展开要求 |
|---|---|---|---|
| 摘要+关键词 | 400 | core_claims 主声明 | context→gap→approach→key result→implication |
| 1.绪论 | 1200 | 第13问动机 + core_claims | 背景/意义/现状/目标5条(每条加 rationale) |
| 2.研究区概况 | 1000 | study_area.md | 地理/气候/生态/植被分布/生态工程 |
| 3.研究方法 | 2500 | methods.md | 7库逐一 + SG公式 + 动态阈值公式 + Sen-MK + 多源印证原理 |
| 4.1 NDVI趋势 | 1500 | results_summary + stats | 4.1.1整体(空间/时间/机制) + 4.1.2分类型(排序+石漠化/退耕机制+为何仅N类) |
| 4.2 物候 | 2000 | results_summary + stats | 4.2.1空间格局(海拔/城市热岛/三因子) + 4.2.2趋势按SOS/EOS/Peak三子节 |
| 4.3 多源印证 | 800 | results_summary + stats | NDVI饱和 + LAI/GPP互补 + 三源归一化 + 真值(lai_slope/gpp_slope) |
| 4.4 结论 | 500 | core_claims | 5条编号结论(每条数据+机制) |
| 5.讨论与展望 | 1500 | core_claims 边界 | 常绿SOS偏早 + 500m混合像元 + 动态阈值局限 + 未来EVI/双logistic |
| 6.核心代码 | 附录 | code_snippets.md | 6模块(GEE/SG/物候/Sen-MK/分类/多源) |
| 7.参考文献 | 附录 | web检索 + core_claims | 15-20条(MODIS/SG/Sen/MK/物候/造林) |

## 2. 4.2.2 物候趋势(三子节展开, 字数主要来源, 单独 700-1000 字)

按 SOS / EOS / Peak 三个子小节展开, 每子节依次:
1. **总体趋势面积占比排序**(从 stats.json 的 sos/eos/peak_trend_pct 取, 无显著变化占比/延迟合计/提前合计)
2. **类型差异**(引用 veg_*_yearly / *_veg_bar / veg_*_trend_stacked 三组图, 定性描述各类对比)
3. **可能生态机制**(气候缓冲/城市热岛/生长季延长/退耕还林等)

## 3. 三层解读规则(每张关键图必做)

每张图正文解读必须含:
1. **数值现象**: 斜率/占比/DOY 具体值(从 stats.json 取)
2. **空间/类型差异**: 哪里改善/哪类植被如何
3. **可能机制**: 生态工程/气候/城市化/常绿过滤

## 4. 真值不伪造

- 所有数值必须来自 `handoff/data/stats.json`, 不杜撰
- stats.json 没有的(如分植被物候 DOY)用"见图X"定性引用, **不编数字**
- 占位 `{xxx}` 必须已被 build_handoff 回填(第三阶段前确认 0 残留)

## 5. 图位标记

- 正文 `![图N 图题](handoff/figures/xxx.png)` + Caption 图注(从 captions.md 取)
- report_docx_builder 会按"每行最多2张"重排, 不用担心并排
- **veg_* 图(9张: veg_sos/eos/peak_yearly + SOS/EOS/Peak_veg_bar + veg_SOS/EOS/Peak_trend_stacked)必须进 4.2.2 正文**, 不丢附录

## 6. 字数自检

写完 report_draft.md 后 CC 自检:
```
python -c "t=open('paper_rewriting_output/report_draft.md',encoding='utf-8').read(); print('中文', sum(1 for c in t if 0x4e00<=ord(c)<=0x9fff))"
```
**中文 < 10000 → 回补 4.1.2/4.2.2/4.3/4.4**(按本规范展开), 直到 ≥10000(目标 12000)。

## 7. 完成判定(v7 标准)

report_docx_builder 生成的 docx 需满足:
- 中文 ≥10000(v7 是 10172)
- 图 39 张(veg 图全在正文 4.2.2, 不掉附录)
- 图组每行最多 2 张
- 字体 w:eastAsia 齐全(宋体正文/黑体标题/楷体封面)
- 单一北林封面(校徽+楷体24pt+信息栏+日期)
- 0 空表
