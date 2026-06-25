"""研究区边界自动获取: DataV GeoAtlas (adcode) → geojson + bbox。

DataV 坑(玉门实战): 县级用 {adcode}.json (不带 _full); 市/省级 {adcode}_full.json。
  县级带 _full 会返回 403 XML(NoSuchKey); 本脚本 _full 失败自动回退不带 _full。

用法:
  python fetch_boundary.py 430000              # 湖南省 → 430000.json + 打印 bbox
  python fetch_boundary.py 620981              # 玉门市(县级, 自动不带 _full)
  python fetch_boundary.py 430100 --full       # 长沙市(含下辖县)
  python fetch_boundary.py 430000 -o hunan.json

输出 geojson + 打印 bbox(写入 config.roi.bbox) 和 boundary_geojson 路径。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests

DATAV_URL = "https://geo.datav.aliyun.com/areas_v3/bound/{adcode}{suffix}.json"


def fetch_geojson(adcode: int, full: bool = False) -> dict:
    """下载 DataV 行政区 geojson。县级不带 _full; 市/省级 full=True。_full 失败自动回退。"""
    suffix = "_full" if full else ""
    url = DATAV_URL.format(adcode=adcode, suffix=suffix)
    r = requests.get(url, timeout=30)
    if r.status_code != 200 or len(r.content) < 1000:
        if full:  # 县级 _full 返回 403 XML, 回退不带 _full
            return fetch_geojson(adcode, full=False)
        raise RuntimeError(f"DataV 获取失败 adcode={adcode}: HTTP {r.status_code} ({len(r.content)} bytes)")
    return r.json()


def geojson_bbox(gj: dict) -> list[float]:
    """算 geojson 的 [west, south, east, north] bbox。"""
    xs, ys = [], []
    feats = gj.get("features", [gj] if gj.get("type") == "Feature" else [])
    for f in feats:
        geom = f.get("geometry", f)
        gt = geom.get("type")
        coords = geom.get("coordinates", [])
        rings: list = []
        if gt == "Polygon":
            rings.extend(coords)
        elif gt == "MultiPolygon":
            for poly in coords:
                rings.extend(poly)
        for ring in rings:
            for pt in ring:
                if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                    xs.append(pt[0]); ys.append(pt[1])
    if not xs:
        raise RuntimeError("geojson 无有效坐标")
    return [min(xs), min(ys), max(xs), max(ys)]


def main() -> None:
    ap = argparse.ArgumentParser(description="DataV adcode → geojson + bbox (解玉门县级 _full 坑)")
    ap.add_argument("adcode", type=int, help="行政区代码 (湖南 430000 / 长沙 430100 / 玉门 620981)")
    ap.add_argument("-o", "--output", default=None, help="输出 geojson 路径 (默认 {adcode}.json)")
    ap.add_argument("--full", action="store_true", help="市级含下辖县 (_full); 县级不要加")
    args = ap.parse_args()

    gj = fetch_geojson(args.adcode, full=args.full)
    bbox = geojson_bbox(gj)
    out = args.output or f"{args.adcode}.json"
    Path(out).write_text(json.dumps(gj, ensure_ascii=False), encoding="utf-8")
    name = gj.get("features", [{}])[0].get("properties", {}).get("name", str(args.adcode))
    print(f"✅ {name} 边界 -> {out}")
    print(f"   config.roi.bbox: [{bbox[0]:.4f}, {bbox[1]:.4f}, {bbox[2]:.4f}, {bbox[3]:.4f}]")
    print(f'   config.roi.boundary_geojson: "{out}"')


if __name__ == "__main__":
    main()
