"""校验 config.yaml 必填字段, 缺失报清晰提示 (而非 KeyError 栈)。

用法: python validate_config.py [config.yaml]
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

# section -> 必填字段 (空字符串/None 算缺)
REQUIRED: dict[str, list[str]] = {
    "roi": ["name", "bbox"],
    "gee": ["key_file"],
    "date": ["start", "end"],
    "paths": ["data", "outputs", "report"],
}


def _validate_veg_reclass(cfg: dict) -> list[str]:
    """P1-2: veg_reclass 校验."""
    errors: list[str] = []
    vr = cfg.get("veg_reclass")
    if not vr:
        errors.append("缺 veg_reclass 段或为空 (若 by_veg=true 必填)")
        return errors
    REQUIRED_KEYS = ("forest", "grassland", "cropland")
    missing = [k for k in REQUIRED_KEYS if k not in vr]
    if missing:
        errors.append(f"veg_reclass 缺少必需类别: {missing} (至少含 forest/grassland/cropland)")
    for key, val in vr.items():
        if not isinstance(val, list) or not val:
            errors.append(f"veg_reclass.{key} 必须是非空 list (value 列表)")
    return errors


def _validate_slope_magnitude(cfg: dict) -> list[str]:
    """P1-2: slope_threshold 量级 sanity 检查."""
    errors: list[str] = []
    trend = cfg.get("trend") or {}
    s1 = trend.get("slope_threshold")
    if s1 is not None:
        try:
            s1_f = float(s1)
            if not (1e-5 <= s1_f <= 0.01):
                errors.append(f"trend.slope_threshold={s1_f} 超出建议范围 [1e-5, 0.01] (NDVI/年)")
        except (TypeError, ValueError):
            errors.append(f"trend.slope_threshold 不是数值: {s1!r}")
    ph = cfg.get("phenology_trend") or {}
    s2 = ph.get("pheno_slope_threshold")
    if s2 is not None:
        try:
            s2_f = float(s2)
            if not (0.1 <= s2_f <= 5.0):
                errors.append(f"phenology_trend.pheno_slope_threshold={s2_f} 超出建议范围 [0.1, 5.0] (DOY/年)")
        except (TypeError, ValueError):
            errors.append(f"phenology_trend.pheno_slope_threshold 不是数值: {s2!r}")
    return errors


def _validate_params_ndvi(cfg: dict) -> list[str]:
    """P1-2: params 含 phenology 时必含 ndvi."""
    errors: list[str] = []
    steps = set((cfg.get("analysis") or {}).get("steps") or [])
    params = list((cfg.get("download") or {}).get("params", []))
    # 若 steps 未指定, 默认含 phenology
    has_phenology = (not steps) or ("phenology" in steps)
    if has_phenology and params and "ndvi" not in params:
        errors.append("params 显式指定但不含 ndvi, 无法做 phenology 分析")
    return errors


def _validate_scale(cfg: dict) -> list[str]:
    """P2-1: scale 提示."""
    warnings: list[str] = []
    scale = (cfg.get("download") or {}).get("scale")
    if scale is not None:
        try:
            scale_i = int(scale)
            if scale_i < 500:
                warnings.append(
                    f"download.scale={scale_i}m < 500, 像元数大易超 GEE 内存, "
                    f"建议增大 ndvi_tiled 的 tiles 分块数"
                )
        except (TypeError, ValueError):
            pass
    return warnings


def validate(cfg: dict) -> list[str]:
    errors: list[str] = []
    for section, fields in REQUIRED.items():
        sec = cfg.get(section)
        if not isinstance(sec, dict):
            errors.append(f"缺段: {section}")
            continue
        for f in fields:
            v = sec.get(f)
            if v in (None, "", []):
                errors.append(f"缺字段或为空: {section}.{f}")
    # bbox 长度
    bb = (cfg.get("roi") or {}).get("bbox")
    if bb and len(bb) != 4:
        errors.append(f"roi.bbox 需 4 元素 [west,south,east,north], 当前 {len(bb)}")

    # P1-2 校验集
    if (cfg.get("by_veg") is True) or (
        isinstance(cfg.get("by_veg"), dict) and cfg.get("by_veg", {}).get("enabled", True)
    ):
        errors.extend(_validate_veg_reclass(cfg))
    errors.extend(_validate_slope_magnitude(cfg))
    errors.extend(_validate_params_ndvi(cfg))

    # P2-1 提示 (不阻塞, 走 stderr)
    scale_warnings = _validate_scale(cfg)
    for w in scale_warnings:
        import sys as _sys
        print(f"⚠️  {w}", file=_sys.stderr)
    return errors


def main() -> None:
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    cfg = yaml.safe_load(Path(cfg_path).read_text(encoding="utf-8"))
    errors = validate(cfg)
    if errors:
        print("❌ config 校验失败:")
        for e in errors:
            print(f"  - {e}")
        print("\n参考 config.yaml.example 补齐字段。")
        sys.exit(1)
    print("✅ config 必填字段校验通过")
    print(f"   研究区: {(cfg.get('roi') or {}).get('name')}  时段: {(cfg.get('date') or {}).get('start')} ~ {(cfg.get('date') or {}).get('end')}")


if __name__ == "__main__":
    main()
