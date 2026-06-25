# 报告生成

## 推荐入口

在生成项目根目录运行:

```bash
python report_docx_builder.py --output report_final.docx
```

兼容旧命令:

```bash
python optimize_report.py handoff/report_draft.docx -o report_final.docx
```

`optimize_report.py` 只是兼容入口, 实际调用 `report_docx_builder.py`。

## 输入

- `paper_rewriting_output/report_draft.md`: CC 按 stage2-writing-guide.md 生成的正文 Markdown, 作为最终排版的文本源。
- `config.yaml`: 研究区、课程封面字段、输出格式和基本参数。
- `handoff/figures/*.png`: 全套图件。
- `handoff/captions.md`: 图注优先来源; 未覆盖的图件由生成器按文件名生成稳妥图注。
- `report/assets/bilin_logo.png`: 封面 logo。

## 输出

- `report_final.docx` 或用户通过 `--output/-o` 指定的路径。

## DOCX 排版约束

最终 DOCX 生成器必须满足以下约束:

1. 保留 Markdown 表格, 并使用固定 Word 表格宽度、表头底色和单元格内边距。
2. `##/###/####` 分别映射到 Word `Heading 1/2/3`。
3. 连续图组按紧凑栅格排版: 2张=一排2张, 3张=一排3张, 4张=2+2, 5张=3+2, 6张=3+3, 7张=3+2+2, 8张=3+3+2, 依此类推; 单张图才单图居中。
4. 每张图生成 `Caption` 样式图注; 图组用无边框表格排版, 图片与图注必须同格, 单元格不得为空。
5. `按植被类型统计` 图件优先进入 `4.2.2 整体植被物候期年际时空变化趋势` 正文, 包括 `veg_sos_yearly`、`veg_eos_yearly`、`veg_peak_yearly`、`SOS_veg_bar`、`EOS_veg_bar`、`Peak_veg_bar`、`veg_SOS_trend_stacked`、`veg_EOS_trend_stacked`、`veg_Peak_trend_stacked`; 不得只作为附录兜底图件。
6. 正文未出现的 `handoff/figures/*.png` 才进入“附录A 输出图件汇总”。
7. 封面字段从 `config.yaml` 读取, 不硬编码姓名、学号、研究区或教师。封面视觉对齐优秀样板: A4 页面、北林 logo 约 8.8 cm、标题/副标题 24 pt 楷体加粗、信息栏 15 pt 楷体、日期写作“YYYY 年 M 月 D 日”; 但不要复制样板中姓名/指导教师被挤到第二页的分页问题。
8. “核心代码”节优先读取 `handoff/code_snippets.md`, 按优秀示例课件的模块化代码展示方式输出 6 个核心代码模块和核心库对照表; 代码块使用等宽字体和浅灰底, 避免与正文混排。

## 依赖矩阵

| 格式 | Python 包 | 系统依赖 |
|---|---|---|
| DOCX | pyyaml, pillow, python-docx | 无 |
| 视觉 QA | PyMuPDF 或 LibreOffice+Poppler | Word/LibreOffice/Poppler 视本机环境而定 |

`pandoc` 不再是最终 DOCX 的必需依赖。若用户额外需要 PDF, 可在 Word/LibreOffice 中由最终 DOCX 导出。
