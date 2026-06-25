# Skill Quality Report: lby-shixi

## Executive Summary
- **Overall Score**: 76/100 (C)
- **Evaluated**: 2026-06-18
- **Skill Path**: local clone of `hyfdracula/lby-shixi`
- **Mode**: remediation-backlog

`lby-shixi` has a strong domain shape: it knows the course task, ships a full geospatial processing template, and keeps most operational caveats in `references/`. The main weakness is distribution reliability. The current skill is tightly coupled to one machine, one course deadline, local GEE service-account paths, and several Hunan-specific defaults. It also overpromises Word/PDF report generation without shipping the full dependency and conversion workflow.

## Dimension Scores

### 1. Description Quality (25%)
**Score**: 70/100

**Strengths**:
- Specific trigger domain and user phrases are present: "物候提取", "NDVI趋势", "SOS-EOS-Peak", "植被物候实习", "lby-shixi".
- The description tells the model what concrete workflow the skill supports.

**Weaknesses**:
- `SKILL.md:3` is too dense for a frontmatter trigger and mixes feature list, workflow details, and trigger phrases into one long line.
- It does not use the recommended third-person trigger style.
- The description is course-specific enough that a model may miss adjacent requests such as "遥感实习报告", "MODIS 物候", or "GEE 植被参数分析".

**Recommendations**:
1. Shorten the description to one trigger-oriented sentence.
2. Move product/process details into the body or `references/`.
3. Add broader but still precise trigger phrases.

### 2. Content Organization (30%)
**Score**: 82/100

**Strengths**:
- `references/` is used well for GEE setup, environment pitfalls, ROI handling, and report styles.
- The main workflow is readable and maps clearly to intake -> setup -> run -> report.
- The template package is reasonably organized under `templates/src`.

**Weaknesses**:
- `SKILL.md` still contains operational details that should live in references, especially local key names and paths.
- Report generation is described as a complete Word/PDF/Markdown workflow, but the actual conversion path is incomplete.
- Hunan/default-course assumptions are embedded in the config and helper scripts rather than isolated as examples.

**Recommendations**:
1. Move local credential details out of `SKILL.md`.
2. Add a `references/report-generation.md` or a real `templates/build_report.py`.
3. Split reusable defaults from one-off Hunan examples.

### 3. Writing Style (20%)
**Score**: 72/100

**Strengths**:
- The writing is concrete and task-oriented.
- It avoids vague "do a report" phrasing and gives specific outputs.

**Weaknesses**:
- The body is mostly descriptive rather than imperative, which weakens actionability for agents.
- It references a Claude-specific `AskUserQuestion` interaction pattern without a Codex fallback.
- Several instructions are phrased as personal/local notes rather than reusable skill behavior.

**Recommendations**:
1. Convert workflow sections to imperative steps.
2. Replace tool-specific names with platform-neutral "ask the user in batches", or provide a Codex/Claude mapping.
3. Make local notes examples, not defaults.

### 4. Structural Integrity (25%)
**Score**: 76/100

**Strengths**:
- Required frontmatter fields exist.
- Referenced `references/` files exist.
- `assets/bilin_logo.png` exists.
- A complete Python template skeleton is included.

**Weaknesses**:
- `templates/fix_cover.py` imports `docx`, but `templates/requirements.txt` does not include `python-docx`.
- `SKILL.md` tells users to run `python -m src.multi_source -c config.yaml`, but `templates/src/multi_source.py` expects the first positional argument and does not parse `-c`.
- `templates/report/report_template.md` links to `../assets/bilin_logo.png`, but `SKILL.md` only instructs copying `templates/`, not `assets/`.
- `templates/post_process.py` and `templates/fix_cover.py` contain hard-coded local paths.

**Recommendations**:
1. Fix dependency and CLI mismatches before distribution.
2. Copy `assets/` during setup or place assets inside `templates/`.
3. Remove machine-specific default paths from scripts.

## Grade Breakdown

| Dimension | Score | Weight | Contribution |
|-----------|-------|--------|--------------|
| Description | 70/100 | 25% | 17.5 |
| Organization | 82/100 | 30% | 24.6 |
| Style | 72/100 | 20% | 14.4 |
| Structure | 76/100 | 25% | 19.0 |
| **Overall** | **76/100** | **100%** | **75.5 (C)** |

## Verification Notes

- Local files were reviewed from the cloned repository.
- The GitHub remote was reachable at commit `1db4207b5c0fb672bf23c4886ceea5e861771dea`.
- Python runtime was unavailable in this environment, so the Python templates were not executed or AST-compiled. Findings are based on static inspection.

## Next Steps

See `improvement-plan-lby-shixi.md` for the prioritized remediation backlog.
