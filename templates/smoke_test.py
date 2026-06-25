"""Offline smoke test for the generated project template."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT_RUNNER = """
import os
import runpy
import sys
from pathlib import Path

root = Path(sys.argv[1])
packages = root.parent / ".smoke-packages"
if packages.exists():
    sys.path.insert(0, str(packages))
sys.path.insert(0, str(root))
target = sys.argv[2]
os.chdir(root)
sys.argv = [target, *sys.argv[3:]]
runpy.run_path(str(root / target), run_name="__main__")
"""


def run(args: list[str]) -> None:
    root = Path(__file__).resolve().parent
    print("$", " ".join([sys.executable, *args]), flush=True)
    subprocess.run([sys.executable, "-c", SCRIPT_RUNNER, str(root), *args], cwd=root, check=True)


def main() -> None:
    run(["make_fake_data.py"])
    run(["run_all.py", "-c", "config.smoke.yaml", "-s", "preprocess", "ndvi_trend", "phenology", "phenology_trend"])
    run(["make_pheno_figs.py", "config.smoke.yaml"])
    run(["report_stats.py", "config.smoke.yaml"])
    run(["build_handoff.py", "-c", "config.smoke.yaml"])
    print("offline smoke test passed (stage1 + handoff)")


if __name__ == "__main__":
    main()
