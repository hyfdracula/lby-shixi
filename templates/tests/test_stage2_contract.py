import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _rationale_matrix() -> str:
    header = (
        "| Row ID | Manuscript Unit | Planned Function | Motivation Link | "
        "Reference/SOTA Pattern Learned | Target Scene or Venue Norm | "
        "User Evidence or Citation Anchor | Planned Text Move | Final Text Check |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
    )
    rows = []
    base = (
        "本行围绕动机主线展开，明确 reference/SOTA pattern 如何迁移到课程实习报告 scene，"
        "并绑定 handoff/data/stats.json、handoff/figures 与 citation evidence，"
        "计划用 claim-evidence-explanation 写法收束到可检查的 final text。"
    )
    for index in range(1, 9):
        unit = "全文框架" if index == 1 else f"第{index - 1}节写作单元"
        rows.append(
            f"| {index} | {unit} | framework structure and report writing unit | "
            f"{base} | {base} | {base} | {base} | {base} | {base} |"
        )
    return header + "\n".join(rows) + "\n"


def _citation_bank() -> str:
    return (
        "| Citation | Claim | Support Sentence |\n"
        "|---|---|---|\n"
        "| MODIS Vegetation Index 2025 DOI:10.0000/example1 | MODIS NDVI supports long-term vegetation monitoring | This 2025 reference sentence gives a usable support statement for the report background. |\n"
        "| Savitzky Golay Phenology 2024 DOI:10.0000/example2 | SG smoothing reduces time-series noise | This 2024 reference sentence gives a usable support statement for the method section. |\n"
        "| Sen Mann Kendall 2023 DOI:10.0000/example3 | Sen-MK supports robust trend detection | This 2023 reference sentence gives a usable support statement for trend interpretation. |\n"
    )


def _stage2_output(root: Path) -> Path:
    out = root / "paper_rewriting_output"
    config = {
        "workflow": "build_from_materials",
        "tier": "pro",
        "scene": "report_review",
        "output_language": "zh",
        "target_name": "测试区植被物候实习报告",
        "materials_dir": "handoff",
        "word_output": "docx",
        "translation_package": "none",
        "citation_target_count": 1,
        "min_chinese_chars": 100,
    }
    _write(out / "lby_config.json", json.dumps(config, ensure_ascii=False, indent=2))
    required = {
        "lby_config.md": "# LBY Stage2 Config\n",
        "source_map.md": "# Source Map\nhandoff materials indexed.\n",
        "reference_materials/source_index.md": "# Source Index\nlocal and web references.\n",
        "research_dossier.md": "# Research Dossier\nremote sensing phenology research.\n",
        "exemplar_learning_dossier.md": "# Exemplar Learning\nstrong report patterns.\n",
        "style_profile.md": "# Style Profile\ncourse report style.\n",
        "sota_gap_map.md": "# SOTA Gap Map\nmethod and region gap.\n",
        "motivation_options_after_research.md": "# Motivation Options\n1. confirmed candidate.\n",
        "citation_support_bank.md": _citation_bank(),
        "confirmed_motivation.md": "# Confirmed Motivation\n基于真实 MODIS 结果解释测试区植被物候变化。\n",
        "section_blueprints.md": "# Section Blueprints\nall sections planned.\n",
        "writing_rationale_matrix.md": _rationale_matrix(),
        "source_inventory.md": "# Source Inventory\nhandoff files.\n",
        "evidence_bank.md": "# Evidence Bank\nstats.json and figures support claims.\n",
        "figure_asset_map.md": "# Figure Asset Map\nall handoff figures mapped.\n",
        "claim_register.md": "# Claim Register\nclaims tied to evidence.\n",
        "integrity_check.md": "# Integrity Check\nPASS\n",
        "report_draft.md": "# 测试区植被物候实习报告\n\n" + "真实统计结果支撑报告。" * 500,
    }
    for name, text in required.items():
        _write(out / name, text)
    return out


class Stage2ContractTest(unittest.TestCase):
    def run_script(self, script: str, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        existing = env.get("PYTHONPATH")
        env["PYTHONPATH"] = str(SCRIPTS) if not existing else str(SCRIPTS) + os.pathsep + existing
        return subprocess.run(
            [sys.executable, str(SCRIPTS / script), *args],
            cwd=str(ROOT),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

    def test_artifact_check_accepts_lby_stage2_without_latex(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = _stage2_output(Path(tmp))
            result = self.run_script(
                "artifact_check.py",
                str(out),
                "--workflow",
                "build_from_materials",
                "--pdf-policy",
                "never",
                "--word-policy",
                "never",
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertNotIn("final_paper/main.tex", result.stdout)
            self.assertNotIn("latex_report.md", result.stdout)

    def test_integrity_audit_reads_report_draft_not_final_paper_tex(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = _stage2_output(Path(tmp))
            result = self.run_script("integrity_audit.py", str(out), "--markdown")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertNotIn("final_paper", result.stdout)

    def test_structured_review_defaults_to_report_draft_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = _stage2_output(Path(tmp))
            result = self.run_script("structured_review.py", str(out), "--write")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertTrue((out / "structured_review.md").exists())


if __name__ == "__main__":
    unittest.main()
