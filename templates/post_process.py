"""Run optional post-processing steps after the main pipeline."""
from __future__ import annotations

import argparse
import os
import runpy
import sys
import traceback
from pathlib import Path

STEPS = [
    ("make_extra_figs.py", False),
    ("make_geo_figs.py", False),
    ("src.multi_source", True),
    ("report_stats.py", False),
    ("report_stats2.py", False),
    ("build_handoff.py", False),  # 第一阶段数据包产出(图+data+专业文本, 供写作 skill)
]


def main() -> None:
    parser = argparse.ArgumentParser(description="多源分析、补图、地理要素图和统计后处理")
    parser.add_argument("-c", "--config", default="config.yaml", help="配置文件路径")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent
    os.chdir(project_root)
    sys.path.insert(0, str(project_root))

    for target, is_module in STEPS:
        sys.argv = ["x", args.config]
        print(f"\n========== {target} ==========", flush=True)
        try:
            if is_module:
                runpy.run_module(target, run_name="__main__")
            else:
                runpy.run_path(target, run_name="__main__")
        except Exception:  # noqa: BLE001
            print(f"!! {target} FAILED:", flush=True)
            traceback.print_exc()

    print("\n========== POST PROCESS DONE ==========", flush=True)


if __name__ == "__main__":
    main()
