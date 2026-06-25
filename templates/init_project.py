"""一键 setup: 复制 templates/ 到目标工作区 + 生成 config.yaml。

用法:
  python init_project.py ./my_project            # 生成 ./my_project/ (含全套代码 + config.yaml)
  python init_project.py D:/work/yumen --name yumen
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

SKIP = {".git", "__pycache__", ".gitignore", ".smoke-packages", "outputs", "data"}


def main() -> None:
    ap = argparse.ArgumentParser(description="lby-shixi 一键生成项目到目标工作区")
    ap.add_argument("target_dir", help="目标父目录 (项目生成在其下)")
    ap.add_argument("--name", default="phenology_project", help="项目目录名 (默认 phenology_project)")
    args = ap.parse_args()

    target = Path(args.target_dir) / args.name
    target.mkdir(parents=True, exist_ok=True)
    src = Path(__file__).resolve().parent

    for item in src.iterdir():
        if item.name in SKIP or item.name.startswith("."):
            continue
        dst = target / item.name
        if item.is_dir():
            shutil.copytree(item, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dst)

    # 显式保证 templates/scripts/ -> 工作区 scripts/（含6+脚本）
    scripts_src = src / "scripts"
    scripts_dst = target / "scripts"
    if scripts_src.is_dir():
        shutil.copytree(scripts_src, scripts_dst, dirs_exist_ok=True)

    # config.yaml.example -> config.yaml (用户填)
    cfg_ex = target / "config.yaml.example"
    if cfg_ex.exists():
        shutil.copy2(cfg_ex, target / "config.yaml")

    print(f"✅ 项目已生成 -> {target}")
    print("下一步:")
    print(f"  cd {target}")
    print("  python fetch_boundary.py <adcode>    # 取研究区边界+bbox (写入 config.roi)")
    print("  编辑 config.yaml                      # 填 gee.key_file / course / roi")
    print("  python check_env.py -c config.yaml    # 自检")
    print("  python run_all.py -c config.yaml      # 跑全流程")


if __name__ == "__main__":
    main()
