# lby-shixi · 遥感植被物候期提取实习生成器

地理大数据实习"**基于遥感植被参数的植被物候期提取**"一键生成器。紧扣任务书 5 天流程：GEE 下载 MODIS NDVI/EVI/LAI/GPP → SG 滤波 → 动态阈值/双逻辑斯蒂物候（SOS/EOS/Peak）→ Sen+MK/线性趋势（5 级分级）→ 黑白/彩色出图 → 报告。

## 配套需求

**第二阶段写作**：已内化 15 步深度写作流程（CC 自写），不依赖外部写作 skill。
handoff 数据包（图+stats+专业素材）产出后，CC 按 `references/stage2-writing-guide.md` 生成 `paper_rewriting_output/` 全套写作中间件（source/evidence/figure/claim/rationale/audit）并直写 ≥12000 字 `report_draft.md`。

## 快速开始

```bash
# 1. 装依赖 (Python 库 + 可选 pandoc)
pip install -r templates/requirements.txt
#   pandoc (docx/pdf 可选): winget install --id JohnMacFarlane.Pandoc -e

# 2. 自备 GEE service-account JSON (见 references/gee-setup.md)

# 3. 一键自检
python templates/check_env.py -c config.yaml   # Python 包 + pandoc + PROJ + 代理 + GEE 连通

# 4. 生成项目到工作区
python templates/init_project.py ./my_project

# 5. 编辑 config.yaml (填 roi / gee.key_file / course)
cd my_project
python fetch_boundary.py 430000      # 取研究区边界 + bbox (打印写入 config.roi)

# 6. 跑全流程 + handoff + 最终 DOCX
python run_all.py -c config.yaml
python build_handoff.py -c config.yaml
# 第二阶段由 CC 按 references/stage2-writing-guide.md 写 paper_rewriting_output/report_draft.md
python report_docx_builder.py --project-root . --output "report_final.docx" --final
```

## 核心能力

| 维度 | 选项 |
|---|---|
| **数据** | MODIS NDVI/EVI/LAI/GPP/LC (+SIF 需配 GEE asset)；GEE getDownloadURL，分块保 500m |
| **物候** | 动态阈值 α（默认）/ 双逻辑斯蒂 curve_fit；SOS/EOS/Peak DOY |
| **趋势** | Sen+MK（默认）/ 线性回归；5 级分级（显著退化→显著改善）|
| **分类** | IGBP→4 类 / 自定义 / **不分类**（`analysis.by_veg=false`）|
| **档位** | 70%（仅 NDVI 趋势）/ 100%（含物候+物候趋势），`analysis.tier` |
| **出图** | 黑白（默认）/ 彩色（`viz.style`）；地理要素（指北针/比例尺/边界描边）|
| **报告** | 单一课程实习报告风格；第二阶段生成 Markdown 初稿，第三阶段用 python-docx 稳定排版 Word；封面自动精调；结果真值自动填（stats.json）|

## 离线验证 (无需 GEE key)

```bash
python templates/smoke_test.py          # 默认搭配 (bw/by_veg=true/dynamic/sen_mk)
python templates/smoke_all.py           # 全搭配回归 (含 noveg/double_logistic/linear/color)
```

用内置假数据跑非联网分析步骤，输出 Markdown 报告 + stats.json。

## 文档

- `SKILL.md` — 完整流程 + intake 14 问（每选项标 `[文本]`/`[选项]`）
- `references/`
  - `gee-setup.md` — GEE 认证 + key 自注册（用户自备，skill 不内置）
  - `env-pitfalls.md` — PROJ/PostgreSQL、WARP 代理、分块 500m、DataV 县级边界坑
  - `roi-boundary.md` — 研究区边界获取（省/市/泛区域）
  - `report-styles.md` — 单一课程实习报告风格
  - `report-generation.md` — Markdown 初稿与最终 DOCX 生成
- `templates/` — 全套代码（`src/` + `run_all` + `check_env` + `fetch_boundary` + `init_project` + `validate_config` + `build_handoff` + `report_docx_builder` + `smoke_test` + `smoke_all`）
- `templates/scripts/` — 6个第二阶段检查工具: `material_inventory` / `artifact_check` / `citation_verification_zh` / `humanize_check` / `integrity_audit` / `structured_review`

## 设计原则

- **真数据不伪造**：全部数值来自 GEE 实际下载与计算，报告只填真实结果（stats.json）
- **配置驱动**：一个 `config.yaml` 决定研究区/参数/方法/档位/风格，换区只改 `roi`
- **用户自备 key**：公开 skill 不内置任何私有凭据
- **每选项都能跑**：intake 14 问所有选项均有代码实现或诚实标注

## 凭据安全

GEE key 自备，绝不进 git（`.gitignore` 已排除 `*.json`/`*credentials*`/`*.key`）。
