"""启动一键环境自检: Python 包 + DOCX/PDF 辅助工具 + PROJ + 代理 + GEE 连通。

/lby-shixi 启动时跑, 一眼看清缺啥、怎么修。复用 gee_auth.check_connection /
run_with_warp 的 WARP 判定口径。

用法:
  python check_env.py                 # 测包 + DOCX/PDF 辅助工具 + 代理 (无 config 跳 GEE)
  python check_env.py -c config.yaml  # 全测 (含 GEE 连通)

退出码: 0 = 硬性项全绿 (PDF 辅助工具缺 / 代理 warn 不算硬失败); 非 0 = 包缺 / PROJ / GEE 连不上。
"""
from __future__ import annotations

import argparse
import importlib
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

# 让 from src.gee_auth import ... 等项目内导入都能找到
sys.path.insert(0, str(Path(__file__).resolve().parent))

# pip 包名 -> import 模块名 (earthengine-api / pyyaml / python-docx 的 import 名不同)
REQUIRED_PACKAGES: dict[str, str] = {
    "earthengine-api": "ee",
    "requests": "requests",
    "numpy": "numpy",
    "scipy": "scipy",
    "rasterio": "rasterio",
    "pymannkendall": "pymannkendall",
    "matplotlib": "matplotlib",
    "pyyaml": "yaml",
    "tqdm": "tqdm",
    "python-docx": "docx",
}

# Windows 下 warp-cli 常见安装位置
_WARP_CANDIDATES = (
    r"C:\Program Files\Cloudflare\Cloudflare WARP\warp-cli.exe",
    r"C:\Program Files (x86)\Cloudflare\Cloudflare WARP\warp-cli.exe",
)


def _ok(msg: str) -> None:
    print(f"  ✅ {msg}")


def _fail(msg: str) -> None:
    print(f"  ❌ {msg}")


def _warn(msg: str) -> None:
    print(f"  ⚠️  {msg}")


def _is_windowsapps_python_stub(path: str | None) -> bool:
    if not path:
        return False
    p = Path(path)
    try:
        size = p.stat().st_size
    except OSError:
        size = -1
    normalized = str(p).lower()
    return "windowsapps" in normalized and p.name.lower() in {"python.exe", "python3.exe"} and size == 0


def check_python_launcher() -> bool:
    print("[0/6] Python 启动器")
    current = Path(sys.executable)
    path_python = shutil.which("python")
    if _is_windowsapps_python_stub(str(current)):
        _fail(f"当前解释器是 WindowsApps 占位符: {current}")
        print("      修: 安装正式 Python 3.11+ 后重新打开终端, 或用真实 python.exe 全路径运行")
        return False
    if _is_windowsapps_python_stub(path_python):
        _warn(f"PATH 中 python 指向 WindowsApps 占位符: {path_python}")
        print(f"      当前可用解释器: {current}")
        print(f"      建议: 用 \"{current}\" check_env.py -c config.yaml, 或修正 PATH 后再用 python")
        return True
    _ok(f"当前解释器: {current}")
    return True


def check_packages() -> bool:
    print("[1/6] Python 包 (pip)")
    missing: list[str] = []
    for pkg, mod in REQUIRED_PACKAGES.items():
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(pkg)
    if missing:
        _fail(f"缺: {', '.join(missing)}")
        print(f"      修: \"{sys.executable}\" -m pip install -r requirements.txt")
        return False
    _ok(f"{len(REQUIRED_PACKAGES)} 个必装包齐全")
    return True


def check_pandoc() -> bool:
    print("[2/6] pandoc (PDF/格式转换可选)")
    if shutil.which("pandoc") is not None:
        _ok("pandoc 已装 (额外格式转换可用)")
        return True
    _warn("pandoc 未装: 最终 DOCX 不受影响; 如需额外 PDF/格式转换可手动安装")
    print("      装: winget install --id JohnMacFarlane.Pandoc -e")
    return True  # 软失败


def check_proj() -> bool:
    print("[3/6] PROJ/GDAL (PostgreSQL 污染检测)")
    # 复制 src/utils.py 的 PROJ 修复: 清 PostgreSQL 污染, 指向 rasterio 自带 proj_data
    for k in ("PROJ_LIB", "PROJ_DATA", "GDAL_DATA"):
        os.environ.pop(k, None)
    try:
        import rasterio  # noqa: F401

        rdir = os.path.dirname(rasterio.__file__)
        for sub, envk in (("proj_data", "PROJ_LIB"), ("proj_data", "PROJ_DATA"), ("gdal_data", "GDAL_DATA")):
            p = os.path.join(rdir, sub)
            if os.path.isdir(p):
                os.environ[envk] = p
        _ok("rasterio 可用, PROJ 链路正常 (PostgreSQL 污染已清)")
        return True
    except Exception as e:  # noqa: BLE001
        _fail(f"rasterio / PROJ 异常: {e}")
        print("      多半 PostgreSQL 污染 PROJ_LIB/GDAL_DATA, 见 references/env-pitfalls.md #1")
        return False


def _find_warp_cli() -> str | None:
    exe = shutil.which("warp-cli")
    if exe:
        return exe
    for p in _WARP_CANDIDATES:
        if Path(p).exists():
            return p
    return None


def _warp_connected(warp: str) -> bool:
    r = subprocess.run([warp, "status"], capture_output=True, text=True)
    lines = [ln.strip() for ln in (r.stdout + r.stderr).splitlines() if ln.strip()]
    return bool(lines) and lines[-1].endswith(("Connected", "已连接"))


def check_proxy() -> bool:
    print("[4/6] 代理 (WARP / 系统代理; 国内连 GEE 必须)")
    warp = _find_warp_cli()
    if warp:
        if _warp_connected(warp):
            _ok("Cloudflare WARP 已连接")
            return True
        _warn("warp-cli 已装但未连接")
        print("      开: warp-cli connect  (或 python run_with_warp.py ...)")
        return True
    proxy = (os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
             or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy"))
    if proxy:
        _ok(f"系统代理 env 已设: {proxy}")
        return True
    _warn("未检测到 WARP 或系统代理; 国内直连 GEE 多半失败")
    print("      装 WARP: winget install --id Cloudflare.WARP  或开 Clash, 再 python check_env.py 复测")
    return True  # 代理 WARN 不算硬失败


def check_gee(cfg: dict[str, Any] | None) -> bool:
    print("[5/6] GEE 连通 (实跑 ee.Number 计算)")
    if not cfg:
        _warn("未传 config, 跳过 GEE 连通 (下载前补 config 再测)")
        return True
    key_file = (cfg.get("gee") or {}).get("key_file")
    if not key_file:
        _warn("config.gee.key_file 为空, 跳过 GEE 连通")
        print("      填 service-account JSON 路径到 config.gee.key_file 再测; 注册见 references/gee-setup.md")
        return True
    try:
        from src.gee_auth import check_connection
    except ImportError:
        _warn("无法导入 src.gee_auth.check_connection, 跳过")
        return True
    if check_connection(cfg):
        _ok("GEE 连通 PASS (认证 + 授权 + 网络 + 代理 全通)")
        return True
    _fail("GEE 连通失败")
    print("      排查: 1) 代理开了吗(WARP/Clash) 2) key 路径对吗 3) key 失效/配额耗尽 (references/gee-setup.md)")
    return False


def check_writing_skills() -> None:
    """第二阶段(写作)已内化: CC 直接读 handoff 写 report_draft.md + 第三阶段 report_docx_builder --final 满版, 不依赖外部写作 skill。"""
    _ok("报告生成已内置(CC 读 handoff 自写 + report_docx_builder --final 排版), 不依赖外部写作 skill")

def main() -> int:
    parser = argparse.ArgumentParser(description="lby-shixi 启动环境自检")
    parser.add_argument("-c", "--config", default=None, help="config.yaml 路径 (提供则测 GEE 连通)")
    args = parser.parse_args()

    cfg: dict[str, Any] | None = None
    if args.config:
        from src.gee_auth import load_config
        cfg = load_config(args.config)

    print("=== lby-shixi 环境自检 ===\n")

    results = {
        "Python 启动器": check_python_launcher(),
        "Python 包": check_packages(),
        "pandoc": check_pandoc(),
        "PROJ": check_proj(),
        "代理": check_proxy(),
        "GEE": check_gee(cfg),
    }
    check_writing_skills()  # [6/6] 写作 skill (软WARN, 不在 hard_fail)
    print("\n=== 汇总 ===")
    hard_fail = [k for k in ("Python 启动器", "Python 包", "PROJ", "GEE") if not results[k]]
    if not hard_fail:
        print("✅ 硬性项全绿 (pandoc / 代理 仅 WARN 不阻塞)")
        return 0
    print(f"❌ 硬失败: {', '.join(hard_fail)} —— 按上面提示修后重测")
    return 1


if __name__ == "__main__":
    sys.exit(main())
