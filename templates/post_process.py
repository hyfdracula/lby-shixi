"""后处理串: 多源分析 + 补图 + 地理要素图 + 统计, 一次性跑完 (用 500m 新结果)。

用法(任意 cwd): python C:/Users/19161/Desktop/geo_phenology/post_process.py
"""
import os
import runpy
import sys
import traceback

os.chdir("C:/Users/19161/Desktop/geo_phenology")
sys.path.insert(0, ".")

STEPS = [
    ("make_extra_figs.py", False),   # 补图(原始滤波/植被年际/趋势堆叠)
    ("make_geo_figs.py", False),     # 地理要素空间图(指北针/比例尺/经纬度)
    ("src.multi_source", True),      # 多源 LAI/GPP 趋势分析
    ("report_stats.py", False),      # NDVI 趋势/物候统计(500m 新值)
    ("report_stats2.py", False),     # 三阶段/空间分位数/植被物候(500m 新值)
]

for target, is_module in STEPS:
    sys.argv = ["x", "config_hunan.yaml"]
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
