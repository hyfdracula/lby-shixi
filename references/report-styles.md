# 报告风格(单一)

本 skill 只产出**一种**报告风格: 课程实习报告。正文由第二阶段 CC 按 stage2-writing-guide.md 深度写作产出, 封面固定北林实习格式。不再支持 nature/学报等多风格分支。

## 封面(固定, 不随风格变)

北林 logo(`report/assets/bilin_logo.png`) 居中 + 楷体 24pt 标题"基于遥感植被参数的植被物候期提取" + 副标"——以{roi}为例" + 信息栏(学院/班级/学号/姓名/指导教师) + 日期"YYYY 年 M 月 D 日"。
python-docx 精确居中 + `w:eastAsia` 字体设置(楷体标题/宋体信息栏), 避免中文回落默认字体。

## 正文

- **来源**: 第二阶段 CC 按 stage2-writing-guide.md 从 `handoff/` 数据包(methods/study_area/results_summary/core_claims/captions/code_snippets)产出的 `report_draft.md`
- **排版**: `report_docx_builder.py` 把 md 转成 docx —— 表格原样、图组最多 2 张一排、图注 Caption 样式、`##/###/####` 映射 Heading 1/2/3、核心代码节读 code_snippets.md
- **数值**: 全部来自 GEE 真实下载与计算(`outputs/report_stats.json`), 报告不伪造

## 输出格式

- `docx`(默认, `report_docx_builder.py`)
- `md`(copy `report_draft.md`)
- `pdf`: **不支持**(如需 PDF, 用户自行用 Word/WPS/LibreOffice 打开 docx 导出)

## 字数规范

正文总字数目标 12000 中文字(Word 字数口径)。`build_handoff.py` 将目标 + 4.2.2 按 SOS/EOS/Peak 三子节展开等 special_requirements 写入 handoff/handoff_meta.json, CC 据此产足够厚度的初稿。
