"""全搭配离线回归: default/noveg/linear/color 四套 config 跑通。

double_logistic 逐像元 curve_fit 慢, 不纳入自动回归 (单独跑: 改 config phenology.method 后 python run_all.py -s phenology)。
用法: python smoke_all.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent

VARIANTS = {
    "default": {},
    "noveg": {"analysis": {"by_veg": False}, "download": {"params": ["ndvi"]}},
    "linear": {"trend": {"method": "linear"}},
    "color": {"viz": {"style": "color"}},
}


def main() -> None:
    base = yaml.safe_load((ROOT / "config.smoke.yaml").read_text(encoding="utf-8"))
    subprocess.run([sys.executable, "make_fake_data.py"], cwd=str(ROOT), check=True)
    for name, overrides in VARIANTS.items():
        cfg = {**base, **{k: {**base.get(k, {}), **v} for k, v in overrides.items()}}
        cfg["paths"]["outputs"] = f"./outputs_{name}"
        cfg["report"]["output_basename"] = f"smoke_{name}"
        p = ROOT / f"config.smoke_{name}.yaml"
        p.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
        print(f"\n========== variant: {name} ==========")
        subprocess.run([sys.executable, "run_all.py", "-c", str(p),
                        "-s", "preprocess", "ndvi_trend", "phenology", "phenology_trend"],
                       cwd=str(ROOT), check=True)
        # 报告由第二阶段 CC 自写(report_draft.md, 按 stage2-writing-guide.md) + report_docx_builder 产出,
        # smoke 只验证 stage1 数据流(run_all 四步); handoff/docx 单独验证
        p.unlink()
    print("\n✅ 全搭配 smoke 通过 (default / noveg / linear / color)")


if __name__ == "__main__":
    main()
