# Skill Improvement Plan: lby-shixi

## Priority Summary
- **High Priority**: 6 items
- **Medium Priority**: 5 items
- **Low Priority**: 3 items

## High Priority Improvements

### 1. Remove hard-coded private GEE key defaults from the public skill
**File**: `SKILL.md:24`, `SKILL.md:27-34`, `references/gee-setup.md:19-27`, `templates/config.yaml.example:14-17`
**Dimension**: Structural Integrity / Distribution Safety
**Impact**: +8 points

**Current**:
```yaml
gee:
  project: example-project
  key_file: "C:/path/to/private-service-account.json"
```

**Suggested**:
```yaml
gee:
  key_file: ""  # Ask the user for a local service-account JSON path.
```

**Reason**: Public skills should not advertise reusable private service accounts or machine-specific credential paths. Keep the service-account setup instructions, but make user-provided credentials the default.

### 2. Fix the documented `multi_source` command
**File**: `SKILL.md:85`, `templates/src/multi_source.py:77-80`, `templates/config.yaml.example:4-5`
**Dimension**: Structural Integrity
**Impact**: +5 points

**Current**:
```bash
python -m src.multi_source -c config.yaml
```

`multi_source.py` reads `sys.argv[1]` directly, so `-c` is treated as a filename.

**Suggested**:
```bash
python -m src.multi_source config.yaml
```

Or add `argparse` support to `multi_source.py` so it accepts `-c/--config`, matching `run_all.py`.

**Reason**: This is a direct run failure for users following the skill instructions.

### 3. Add the missing Word dependency
**File**: `SKILL.md:22-23`, `templates/requirements.txt:6-18`, `templates/fix_cover.py:3`
**Dimension**: Structural Integrity
**Impact**: +4 points

**Current**:
`SKILL.md` lists `python-docx`, and `fix_cover.py` imports `docx`, but `requirements.txt` does not install it.

**Suggested**:
```txt
python-docx>=1.1
```

**Reason**: Word output post-processing fails after a clean `pip install -r templates/requirements.txt`.

### 4. Make asset copying explicit or move assets under `templates/`
**File**: `SKILL.md:76-79`, `templates/report/report_template.md:3`
**Dimension**: Structural Integrity
**Impact**: +4 points

**Current**:
`SKILL.md` says to copy `templates/`, but the report template references `../assets/bilin_logo.png`.

**Suggested**:
- Copy both `templates/` and `assets/` into the generated project, or
- Move `bilin_logo.png` to `templates/report/assets/` and update the Markdown path.

**Reason**: The logo breaks in generated reports if only `templates/` is copied.

### 5. Remove machine-specific paths from helper scripts
**File**: `templates/post_process.py:3-10`, `templates/fix_cover.py:47-48`
**Dimension**: Structural Integrity / Reusability
**Impact**: +5 points

**Current**:
```python
os.chdir("C:/path/to/generated-project")
fix_cover(sys.argv[1] if len(sys.argv) > 1 else "C:/path/to/report.docx")
```

**Suggested**:
```python
project_root = Path(__file__).resolve().parent
os.chdir(project_root)
```

For `fix_cover.py`, require an explicit path or default to `paths.report` from config.

**Reason**: These scripts only work on the author machine.

### 6. Complete the report output workflow
**File**: `SKILL.md:57`, `SKILL.md:92-108`, `templates/report/report_template.md`
**Dimension**: Content Organization / Structural Integrity
**Impact**: +6 points

**Current**:
The skill offers Word, PDF, and Markdown, but ships no full report builder, no pandoc command, no PDF conversion path, and no dependency declaration for conversion.

**Suggested**:
Add one of:
- `templates/build_report.py` that fills placeholders and writes Markdown plus optional DOCX.
- A documented pandoc workflow with required dependency checks.
- A narrowed promise: Markdown output only, with optional manual Word conversion.

**Reason**: Output format choices should map to executable artifacts.

## Medium Priority Improvements

### 7. Make `AskUserQuestion` platform-neutral
**File**: `SKILL.md:36`
**Dimension**: Writing Style
**Impact**: +3 points

Replace `AskUserQuestion 分批` with "分批询问用户；在 Codex 中用普通对话或可用的用户输入工具，在 Claude Code 中可用 AskUserQuestion".

### 8. Shorten and rewrite the frontmatter description
**File**: `SKILL.md:3`
**Dimension**: Description Quality
**Impact**: +4 points

Suggested description:
```yaml
description: This skill should be used when generating a GEE/MODIS remote-sensing practicum project or report for vegetation phenology extraction, NDVI trend analysis, SOS/EOS/Peak metrics, and Chinese course-style deliverables.
```

### 9. Move local/course constants into configurable defaults
**File**: `SKILL.md:38-40`, `SKILL.md:102-112`, `templates/fix_cover.py:37`
**Dimension**: Content Organization
**Impact**: +3 points

Keep defaults for this course, but represent class, college, instructor, title, year, and deadline as `config.yaml` fields.

### 10. Replace Hunan-specific example defaults with placeholders
**File**: `templates/config.yaml.example:1-17`, `templates/make_extra_figs.py:3-4`, `templates/make_geo_figs.py:3-4`
**Dimension**: Content Organization
**Impact**: +3 points

Keep a separate regional example config if needed. Make the main example generic.

### 11. Make title formatting robust for non-Hunan regions
**File**: `templates/fix_cover.py:21-23`
**Dimension**: Structural Integrity
**Impact**: +2 points

Current title matching only formats titles containing "湖南" or "研究区". Match on the stable title prefix instead.

## Low Priority Improvements

### 12. Add a README for GitHub users
**File**: repository root
**Dimension**: Content Organization
**Impact**: +2 points

Include installation, expected generated project layout, minimal demo run, and credential setup.

### 13. Add a smoke-test script
**File**: `templates/`
**Dimension**: Structural Integrity
**Impact**: +2 points

Use `make_fake_data.py` to generate small local data and run non-GEE stages. This catches report, plotting, and import regressions without network access.

### 14. Reduce stale-date risk
**File**: `SKILL.md:112`
**Dimension**: Content Organization
**Impact**: +1 point

Make the deadline an intake/config field instead of a permanent instruction.

## Quick Wins
1. Add `python-docx>=1.1` to `templates/requirements.txt`.
2. Change `SKILL.md:85` to `python -m src.multi_source config.yaml`.
3. Remove the default path from `fix_cover.py`.
4. Copy `assets/` during setup or move `bilin_logo.png` into `templates/report/assets/`.
5. Replace private key names with "user-provided service-account JSON".

## Estimated Time to Complete
- High Priority: 2.5-4 hours
- Medium Priority: 1.5-2.5 hours
- Low Priority: 1-2 hours
- **Total**: 5-8.5 hours

## Expected Score Improvement
- Current: 76/100 (C)
- After High Priority: 86/100 (B)
- After All: 91/100 (A-)
