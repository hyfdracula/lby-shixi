"""GEE service-account 认证。

复用 rs-urban-monitor 的已验证写法: ``ee.ServiceAccountCredentials(email, key_file)``
+ ``ee.Initialize(credentials)`` —— **不显式传 project** (传 project 会触发
"project not found", 用 SA 自带默认 project 即可)。

仅读取 key 中的 ``client_email`` 字段 (账号邮箱, 非密钥); private_key 始终留在
文件内, 不读出、不打印、不提交 git。
"""
from __future__ import annotations

import json
import logging
import os
import argparse
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.yaml") -> dict[str, Any]:
    """读取配置。"""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def init_gee(cfg: dict[str, Any]) -> None:
    """用 service account key 初始化 GEE (不传 project, 与 rs-urban-monitor 一致)。"""
    key_file = cfg["gee"]["key_file"]
    if not Path(key_file).exists():
        raise FileNotFoundError(
            f"GEE key 未找到: {key_file}\n请确认 config.yaml -> gee.key_file 路径正确。"
        )
    with open(key_file, "r", encoding="utf-8") as f:
        info = json.load(f)
    email = info.get("client_email")
    if not email:
        raise ValueError("key 文件缺少 client_email 字段, 请确认是合法的 GCP service account key。")

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(key_file)  # 供其他 GCP 库复用
    import ee

    creds = ee.ServiceAccountCredentials(email, str(key_file))
    ee.Initialize(creds)  # 不传 project: 用 SA 默认 project (传 project 可能触发 "project not found")
    logger.info("GEE 已连接: account=%s", email)


def check_connection(cfg: dict[str, Any] | None = None) -> bool:
    """连通性测试: 能否在 GEE 上执行一次简单计算。"""
    cfg = cfg or load_config()
    try:
        init_gee(cfg)
        import ee

        val = ee.Number(1).add(1).getInfo()
        ok = val == 2
        logger.info("GEE 连通测试: %s (1+1=%s)", "PASS" if ok else "FAIL", val)
        return ok
    except Exception as e:  # noqa: BLE001
        logger.error("GEE 连通失败: %s", e)
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="测试 GEE service-account 连通性")
    parser.add_argument("-c", "--config", default="config.yaml", help="配置文件路径")
    args = parser.parse_args()
    raise SystemExit(0 if check_connection(load_config(args.config)) else 1)
