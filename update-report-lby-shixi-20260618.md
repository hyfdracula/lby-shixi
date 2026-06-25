# Skill Update Report: lby-shixi

## Summary

- **Updated**: 2026-06-18
- **Backup**: sibling directory `lby-shixi-backup-20260618`
- **Plan Source**: `improvement-plan-lby-shixi.md`
- **Scope**: High-priority fixes plus low-risk medium/low improvements

## Changes Applied

### Skill Documentation

- Rewrote the frontmatter description into a concise third-person trigger.
- Removed public/default GEE service-account key names and machine-specific key paths.
- Replaced fixed deadline behavior with `config.course.deadline`.
- Made intake wording platform-neutral for Codex and Claude Code.
- Added report generation commands and the new `references/report-generation.md`.

### Template Configuration

- Replaced Hunan/local defaults in `templates/config.yaml.example` with generic placeholders.
- Added `course` and `report` config sections.
- Added `templates/config.smoke.yaml` for offline validation.
- Changed helper defaults from regional config names to `config.yaml`.

### Runtime Scripts

- Added `-c/--config` support to `python -m src.gee_auth`.
- Added `-c/--config` and `--params` support to `python -m src.multi_source`.
- Rewrote `templates/fix_cover.py` to require an explicit DOCX path and remove local defaults.
- Rewrote `templates/post_process.py` to run relative to its own project directory.

### Report Workflow

- Added `templates/build_report.py` for Markdown, DOCX, and PDF output.
- Added `templates/report/assets/bilin_logo.png` so copying `templates/` preserves the cover logo.
- Updated `templates/report/report_template.md` to use config-driven cover fields.
- Added `python-docx>=1.1` to `templates/requirements.txt`.

### Project Usability

- Added `README.md` with setup, GEE test, full-run, and smoke-test commands.
- Added `templates/smoke_test.py` for non-GEE validation using fake data.

## Verification Results

- `git diff --check`: passed; no whitespace errors.
- Sensitive/local-path scan over `SKILL.md`, `README.md`, `references`, and `templates`: passed; no local user paths, private key names, Hunan config defaults, or old local project paths remain.
- Required reference/template files exist: passed.
- Logo copy check: passed; root logo and `templates/report/assets/bilin_logo.png` have matching SHA-256 hashes.
- `pandoc` availability: found `pandoc-3.9.0.2`.
- Python 3 availability: found PostgreSQL/pgAdmin bundled Python `3.13.12`.
- Python syntax check: passed via `python -m py_compile` for modified template files.
- Offline smoke test: passed via `templates/smoke_test.py`; fake data generation, preprocess, NDVI trend, phenology extraction, phenology trend, phenology figure generation, report statistics, and Markdown report generation all completed.

## Notes

- `python` and `py -3` still resolve to Windows app aliases / no registered runtime in PATH. Verification used the explicit pgAdmin Python path.
- pgAdmin Python runs in isolated mode, so the smoke test runner now explicitly supports a local `.smoke-packages` dependency directory for this environment.
- Rasterio emitted `BLOCKXSIZE can only be used with TILED=YES` warnings on the first smoke run. `clean_raster_profile()` now removes block-size keys from non-tiled output profiles, and the rerun completed without those warnings.

## Expected Quality Change

- Before: 76/100 (C)
- After applied fixes: approximately 90-92/100 (A-), with offline smoke-test verification completed.
