# Stage2 深度写作指南（自包含）

## ⛔ 第一规则：章节结构唯一固定（CC 必须遵守）

**report_draft.md 的章节结构永远用以下中文格式，禁止任何变体：**

```
## 一、项目简介
## 二、数据与方法
## 三、实验步骤
## 四、结果与分析
## 五、讨论与展望
## 六、核心代码
## 七、参考文献
```

**绝对禁止**：摘要+关键词开头、"第1章 绪论"、"Abstract"、"Introduction"、IMRaD、journal/conference/competition 风格。CC 写 report_draft.md 第一行必须是 `## 一、项目简介`，不是 `## 摘要`。

**禁止读 scene 配置**：CC 不得从 handoff/paperspine_config.json 或任何 scene/config 文件读取 scene 值来决定写作风格。即使旧 handoff 产物里残留了 scene=journal，CC 也**必须忽略**，永远按上面的课程报告章节结构写。scene 字段已被废弃，唯一风格是课程报告。

---

本指南完全内化 `build_from_materials` 深度写作工作流，CC 在第二阶段严格执行。**不依赖外部写作 skill**。

## 核心理念

第二阶段是研究写作工作流，不是改文字的补丁。它的职责：先学习目标场景和强范例，强制用户确认核心论点，逐行设计报告，然后才写或重建报告。

**写真值不伪造**——所有数值/数据/声明必须来自用户提供的 handoff 材料（handoff/data/stats.json 等）。外部范例只教结构和修辞。

## Non-Negotiable Route（15步，CC 内化执行）

### 1. 确认配置
读 `handoff/handoff_meta.json` 和项目根目录 `config.yaml`，确认场景(scene)、目标字数、研究区、姓名学号、humanize_tier、citation_target_count 等信息。缺失或残缺则回退到 intake 补充。不跳过配置检查直接写。

创建 lby Stage2 配置镜像，使用 lby 自有命名，不读取外部写作 skill：

- `paper_rewriting_output/lby_config.json`
- `paper_rewriting_output/lby_config.md`

`lby_config.json` 至少包含：

```json
{
  "workflow": "build_from_materials",
  "scene": "report_review",
  "tier": "pro",
  "output_language": "zh",
  "target_name": "研究区植被物候实习报告",
  "materials_dir": "handoff",
  "draft_path": "",
  "user_motivation": "intake 第13问或自动推断",
  "word_output": "docx",
  "translation_package": "none",
  "reference_mode": "local_first",
  "reference_paths": ["handoff", "."],
  "citation_target_count": 20,
  "humanize_tier": "none|low|medium|high",
  "min_chinese_chars": 12000
}
```

### 2. 建立 source_map 与 build-from-materials 证据底座
创建 `paper_rewriting_output/source_map.md`：列出 handoff/ 中每个素材文件的内容摘要 + 用途 + 关键数据点，供后续引用。

同时执行/等价执行：

```bash
python scripts/material_inventory.py handoff --output-dir paper_rewriting_output
```

并创建以下 build-from-materials 核心产物：

- `source_inventory.md` — handoff 文件清单
- `evidence_bank.md` — stats.json、figures、captions、methods、core_claims 中可支撑声明的证据台账
- `figure_asset_map.md` — 每张图的文件名、图号、正文插入位置、支撑声明
- `claim_register.md` — 每个核心声明、证据来源、边界条件、写入章节

这四项是 build_from_materials 的核心代码块，lby 第二阶段必须自有生成，不能依赖外部 skill。

### 3. 研究调研(research)
在写核心论点前，必须先做研究：
- **本地引用索引**：读 handoff/ 中已有的文献引用（core_claims.md/results_summary.md 中的参考文献）
- **Web 检索补充**：按研究区+方法+场景需求，检索相关文献补强 citation target（默认 15-30 篇）
- 创建 `paper_rewriting_output/reference_materials/source_index.md`，记录本地材料、检索来源、范例论文来源与用途。

### 4. 建立研究产物 + Exemplar 学习
创建以下研究产物，**Exemplar 学习是独立必须步骤，不可跳过**：

**a. 研究调研**
- `paper_rewriting_output/research_dossier.md`：研究背景、关键文献摘要、场景对标
- `paper_rewriting_output/sota_gap_map.md`：前沿差距分析——当前研究和已有 work 的区别与贡献

**b. Exemplar 学习（向强范例学习结构模式与修辞模板）**
- 从用户 handoff 素材或 Web 检索中找 **2-3 篇强范例论文**（同 scene 同方法领域的高被引/高分论文）
- **范例分析维度**：
  - 结构模式：摘要/引言/方法/结果/讨论的篇幅比例、段落组织节奏
  - 修辞模板：论点陈述方式（direct claim / evidence-first / gap-then-fill）、段落内部论证链条（claim→evidence→explanation 三层）
  - 数据呈现：图表密度、表格格式、数值引用风格
  - 语言特征：句式多样性、时态使用、动词选择（show/demonstrate/suggest/indicate/may/could 梯度）
- 创建 `paper_rewriting_output/exemplar_learning_dossier.md`：记录每篇范例的结构拆解 + 可迁移的写作模式 + 对应的 scene 规范对比
- 输出融入 `style_profile.md` 和 `writing_rationale_matrix` 的 "Reference Pattern Learned" 列
- **必须这一步的原因是**：没有强范例参照的写作容易滑入公式化 AI 句式，有范例锚定的写作能自然降低 AI 痕迹且结构更紧凑

**c. 写作风格分析** — 在 exemplar_learning_dossier 完成后，创建 `paper_rewriting_output/style_profile.md`：将 exemplar 的语言模式与 scene 规范合并，以表格呈现：

| Style Dimension | Target Venue Expectation | Exemplar Pattern | Applied To This Paper |
|---|---|---|---|
| 句长与节奏 | 课程实习报告：15-25字/句 | 范例展示的中文句式 | 按此控制句长 |
| 段落结构 | Claim→Evidence→Explanation | 范例的论证链条 | 每段三层 |
| 术语密度 | 学术可读，不过度专业 | 范例的技术术语穿插 | 术语后跟解释 |
| 时态/语态 | 中文：无时态；减少被动 | 范例的主动语态 | ≤30%被动 |
| 数值引用 | 真值 + 单位 + 比较参照 | 范例的数据呈现方式 | 每数值配解释 |

### 5. 生成动机选项 + 用户确认
创建 `paper_rewriting_output/motivation_options_after_research.md`：基于研究结果生成 2-3 个核心论点选项（每个一句话 + 证据简述），等待用户确认。**不跳过确认步骤直接写报告**。

### 6. 确认动机
用户选定动机后，创建 `paper_rewriting_output/confirmed_motivation.md` 记录最终选择。核心论点必须**简明具体**——不把一项小贡献夸大成多项声明。

### 7. 建立文献支撑库
创建 `paper_rewriting_output/citation_support_bank.md`：为 Introduction、Methods、Discussion、结论等各章准备引用。候选量 ≥ citation_target × 3（如目标 20 条，候选 ≥ 60）。约 80% 应为近 3 年内文献。

### 8. 章节蓝图
创建 `paper_rewriting_output/section_blueprints.md`：逐章/逐节定义：
- 该节的核心论点
- 关键证据/图表列表（从 handoff 的 stats.json 和 handoff/figures/ 取）
- 预期字数

章节结构**固定为课程实习报告**（唯一风格，不选 scene）：

```
## 一、项目简介
### 1.1 背景与意义
### 1.2 目标与内容
## 二、数据与方法
### 2.1 技术说明（核心库）
### 2.2 数据来源（表格）
### 2.3 研究方法（2.3.1 GEE下载 / 2.3.2 SG滤波 / 2.3.3 动态阈值物候 / 2.3.4 Sen-MK趋势 / 2.3.5 多源印证）
### 2.4 多源印证策略
## 三、实验步骤（①下载 ②预处理 ③NDVI趋势 ④物候提取 ⑤物候趋势）
## 四、结果与分析
### 4.1 NDVI趋势分析（4.1.1 整体 / 4.1.2 分植被类型）
### 4.2 物候空间格局及趋势（4.2.1 空间格局 / 4.2.2 年际趋势+按植被类型）
### 4.3 多源LAI/GPP印证
### 4.4 结论
## 五、讨论与展望
## 六、核心代码
## 七、参考文献
## 附录
```

**禁止写 journal/conference/competition 风格**（不要 Abstract/Introduction/IMRaD）。永远用上面这个中文章节结构。

### 9. 写作论证矩阵 (writing_rationale_matrix.md)
**创建 `paper_rewriting_output/writing_rationale_matrix.md`**——这是写作前的执行计划，不是事后总结。表格格式：

| Row ID | Manuscript Unit | Current/Planned Function | Motivation Link | Reference Pattern Learned | Scene Norm | Evidence Anchor | Planned Change | Final Check |
|---|---|---|---|---|---|---|---|---|
| 1 | 全文框架 | 控制结构 | 对应确认动机 | SOTA/范例教的结构 | 课程实习报告标准 | stats.json | 选择XXX结构 | 全文章节对齐 |

- 第一行必须深度论证全文框架：为什么选这个结构、怎么受 SOTA/范例启发、怎么跟随确认动机、用户证据锚定哪里、最后怎么检查
- 后续行按章节拆分到最小可用写作单元：段落级论证(paragraph-level moves)、方法步骤、假设、结果/声明单元、标题、图注等
- 每个单元必须有**具体的跨维度论证**：推进动机、迁移 SOTA 模式、对目标场景规范、引用用户证据、前后段呼应、限制声明在可用证据内
- **浅薄矩阵是失败**：如果大多数行只写"提高清晰度"或"润色表述"，停笔，重做研究/蓝图阶段

### 10. 撰写 report_draft.md
按 section_blueprints + writing_rationale_matrix 执行：
- 逐单元按计划写，不跳过任何行
- 每段写真值（从 stats.json），不伪造
- 图引用 `![图N](handoff/figures/xxx.png)` 按 planning 插入
- 目标 ≥ 12000 中文

### 11. 拆分写代码段
参考 `handoff/code_snippets.md`，在正文中嵌入 5-6 个核心代码块（GEE下载/SG滤波/动态阈值/Sen-MK/分类），完整函数不带删节。

### 12. 参考文献补强
使用 citation_support_bank 取候选引用，精选 15-20 条写入参考文献节，确保涵盖：MODIS 产品、SG 滤波、动态阈值、Theil-Sen+MK、研究区相关研究。

### 13. 完整性自查
创建 `paper_rewriting_output/integrity_check.md`：逐节检查
- 字数达标（4.1/4.2/4.3 每节 ≥ 500 字，全文 ≥ 12000 中文）
- 所有数值有 stats.json 锚定
- 所有主要图有正文 `![]()` 标记
- 讨论节包含方法局限诚实标注
- 【CC填】残留为 0

**自检全靠 `integrity_check.md` 人工**（PaperSpine 论文级脚本 integrity_audit/structured_review/artifact_check 已移除——门槛错配，对课程实习报告过度要求）。`integrity_check.md` 检查通过即可进入第三阶段。

### 14. Markdown 输出
最终输出 `paper_rewriting_output/report_draft.md`，供第三阶段 `report_docx_builder` 排版。

### 15. 事后审计
检查最终 docx 产物：字体、封面、图位、字数、附录图件清单完整性。

## 报告风格（唯一：课程实习报告）

**本 skill 只产出一种风格：课程实习报告**。不写 journal（IMRaD）、不写 conference、不写 competition。章节固定为"一、项目简介 / 二、数据与方法 / 三、实验步骤 / 四、结果与分析 / 五、讨论与展望 / 六、核心代码 / 七、参考文献"。

## 标准产物（paper_rewriting_output/ 下）

- `lby_config.json` — lby 自有 Stage2 配置镜像
- `lby_config.md` — 配置可读版
- `source_map.md` — 素材索引
- `source_inventory.md` — handoff 文件清单
- `reference_materials/source_index.md` — 本地/外部引用与范例来源索引
- `research_dossier.md` — 研究调研
- `sota_gap_map.md` — 前沿差距分析
- `exemplar_learning_dossier.md` — Exemplar 学习（强范例结构拆解+修辞模板）
- `style_profile.md` — 写作风格分析
- `motivation_options_after_research.md` — 动机选项
- `citation_support_bank.md` — 文献支撑库
- `confirmed_motivation.md` — 确认动机
- `evidence_bank.md` — 证据台账
- `figure_asset_map.md` — 图件与正文位置映射
- `claim_register.md` — 声明、证据、边界登记
- `section_blueprints.md` — 章节蓝图
- `writing_rationale_matrix.md` — 写作论证矩阵
- `integrity_check.md` — 完整性自查（人工，不跑论文级脚本）
- `report_draft.md` — 最终草稿（第三阶段输入）

## 精简原则

- **跳过 LaTeX 和 PDF**：lby-shixi 用 report_docx_builder 产出 Word 最终版，不需要 LaTeX 编译
- **跳过翻译包**：lby-shixi 默认中文写作，不需要 translation package
- **跳过外部 UI wizard**：lby-shixi 有 intake 14 问，不需要外部 TUI
- **保留核心写作工作流**：research → citation → motivation → blueprints → rationale matrix → build → integrity_check → docx
- **保留 build_from_materials 核心代码块**：`source_inventory.md`、`evidence_bank.md`、`figure_asset_map.md`、`claim_register.md` 必须存在，第三阶段只负责排版，不能补写这些推理产物。

## Humanize（降 AI 写作约束）

内化降 AI 写作约束分级体系（由 intake 第 14 问决定），CC 在 stage2 写作时直接按选定 tier 执行：

| humanize_tier | 约束强度 | CC 写作规则 |
|---|---|---|
| `none`(默认) | 无 | 学术常规写作，不刻意降 AI |
| `low`(轻度) | ★ | 避免"值得注意的是""综上所述""不仅……而且……"等 AI 高频句式；减少 3 个以上并列长句 |
| `medium`(中度) | ★★☆ | 低度约束 + 每段至少 1 处个人语气（"本研究发现""我们注意到"）；避免连续 3 句以上相同句式；技术术语穿插解释而非堆砌 |
| `high`(深度) | ★★★ | 中度约束 + 减少被动语态（≤30%）；每 500 字至少 1 处数据驱动的具体判断（"SOS 提前 3.2 天/年，远低于温带 5-8 天/年"优于"SOS 呈提前趋势"）；避免全段纯描述无分析 |

**执行**：CC 写 report_draft.md 时实时应用约束，writing_rationale_matrix 中每个 unit 的"Planned Change"列标注对应的 humanize 措施。**不在最后单独跑 humanize，一遍到位**。

**课程作业默认**：中度（`medium`）— 降 AI 同时保学术性。
