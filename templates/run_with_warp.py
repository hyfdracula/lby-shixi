"""包裹 run_all.py: 跑前开 WARP, 跑完(含异常/中断)自动关 WARP。

目的: 平时关 WARP 保证向日葵(Oray)不跨国可远程; 跑 GEE 时自动开, 跑完立刻关,
向日葵恢复。即使 GEE 中途出错或被 Ctrl+C, finally 也会关掉 WARP, 不会被锁外面。

用法 (代替 run_all.py):
  python run_with_warp.py                       # 全流程
  python run_with_warp.py -s download preprocess
  python run_with_warp.py -c config.yaml

注意: WARP 连接期间向日葵可能短暂中断; 脚本结束会自动 disconnect, 重连即可。
"""
from __future__ import annotations

import logging
import shutil
import subprocess
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("warp_runner")

CONNECT_WAIT = 30  # 开启后最长等待隧道建立秒数


def _find_warp_cli() -> str:
    """定位 warp-cli 可执行文件。"""
    exe = shutil.which("warp-cli")
    if exe:
        return exe
    for p in (
        r"C:\Program Files\Cloudflare\Cloudflare WARP\warp-cli.exe",
        r"C:\Program Files (x86)\Cloudflare\Cloudflare WARP\warp-cli.exe",
    ):
        if Path(p).exists():
            return p
    raise FileNotFoundError("找不到 warp-cli, 请确认 Cloudflare WARP 已安装")


def _warp(warp: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([warp, *args], capture_output=True, text=True)


def _is_connected(status_text: str) -> bool:
    """判断 warp-cli status 输出是否为已连接 (兼容中英文)。"""
    last = ""
    for line in status_text.splitlines():
        line = line.strip()
        if line:
            last = line
    return last.endswith(("Connected", "已连接"))


def warp_connect(warp: str, timeout: int = CONNECT_WAIT) -> bool:
    """开启 WARP 并轮询确认连接。"""
    logger.info(">>> 开启 WARP (向日葵可能短暂中断) ...")
    _warp(warp, "connect")
    for _ in range(timeout):
        r = _warp(warp, "status")
        if _is_connected(r.stdout + r.stderr):
            logger.info("WARP 已连接 ✅")
            return True
        time.sleep(1)
    logger.warning("WARP 连接超时 (仍尝试跑, GEE 可能连不上)")
    return False


def warp_disconnect(warp: str) -> None:
    """关闭 WARP, 恢复向日葵直连。"""
    logger.info("<<< 关闭 WARP (恢复向日葵直连) ...")
    _warp(warp, "disconnect")


def main() -> None:
    warp = _find_warp_cli()
    run_args = [sys.executable, "run_all.py", *sys.argv[1:]]
    project_root = Path(__file__).parent
    code = 0
    try:
        warp_connect(warp)
        ret = subprocess.run(run_args, cwd=str(project_root))
        code = ret.returncode
    except KeyboardInterrupt:
        logger.warning("用户中断 (Ctrl+C)")
        code = 130
    except Exception as e:  # noqa: BLE001
        logger.error("运行出错: %s", e)
        code = 1
    finally:
        warp_disconnect(warp)  # 任何情况都关 WARP
        logger.info("退出码 %s", code)
    sys.exit(code)


if __name__ == "__main__":
    main()
