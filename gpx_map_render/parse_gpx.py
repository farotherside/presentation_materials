#!/usr/bin/env python3
"""Parse the FarOtherSide master GPX into per-leg metadata + per-leg GeoJSON.

Outputs:
  - legs_index.json    : array of {id, name, description, start, end, duration_hours,
                                    points, stated_nm, computed_nm,
                                    avg_speed_kn, max_speed_kn, bbox} per leg.
  - geojson/leg_NN.geojson : per-leg LineString with time/elevation coordinate
                              properties (used by the renderer).
"""
import json
import math
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime

GPX_PATH = "/sessions/confident-blissful-allen/mnt/uploads/FarOtherSide_Everything_MASTER.gpx"
OUT_DIR = "/sessions/confident-blissful-allen/mnt/outputs"
GEOJSON_DIR = os.path.join(OUT_DIR, "geojson")
os.makedirs(GEOJSON_DIR, exist_ok=True)

NS = {"g": "http://www.topografix.com/GPX/1/1"}


def haversine_nm(lat1, lon1, lat2, lon2):
    """Great-circle distance in nautical miles."""
    R_NM = 3440.065  # Earth radius in nautical miles
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R_NM * math.asin(math.sqrt(a))


def parse_time(s):
    # 2017-11-22T14:22:48.000Z
    return datetime.strptime(s.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S.%f%z")


def main():
    print(f"Parsing {GPX_PATH} ...")
    # iterparse to keep memory low
    legs = []
    current = None
    points_buffer = []

    for event, elem in ET.iterparse(GPX_PATH, events=("start", "end")):
        tag = elem.tag.split("}", 1)[-1]
        if event == "start" and tag == "trk":
            current = {"name": None, "desc": None, "cmt": None, "number": None}
            points_buffer = []
        elif event == "end" and current is not None:
            if tag == "name" and current["name"] is None:
                current["name"] = elem.text
            elif tag == "desc" and current["desc"] is None:
                current["desc"] = elem.text
            elif tag == "cmt" and current["cmt"] is None:
                current["cmt"] = elem.text
            elif tag == "number" and current["number"] is None:
                current["number"] = int(elem.text) if elem.text else None
            elif tag == "trkpt":
                lat = float(elem.attrib["lat"])
                lon = float(elem.attrib["lon"])
                t_el = elem.find("g:time", NS)
                e_el = elem.find("g:ele", NS)
                t = parse_time(t_el.text) if t_el is not None and t_el.text else None
                ele = float(e_el.text) if e_el is not None and e_el.text else None
                points_buffer.append((lat, lon, t, ele))
                elem.clear()
            elif tag == "trk":
                # Finalize this leg
                if not points_buffer:
                    elem.clear()
                    current = None
                    continue

                pts = points_buffer
                lats = [p[0] for p in pts]
                lons = [p[1] for p in pts]
                times = [p[2] for p in pts if p[2] is not None]
                start_t = times[0] if times else None
                end_t = times[-1] if times else None
                duration_hours = (
                    (end_t - start_t).total_seconds() / 3600.0
                    if start_t and end_t
                    else None
                )

                # Compute cumulative distance + per-segment speed
                cum_nm = 0.0
                speeds = []
                for i in range(1, len(pts)):
                    d = haversine_nm(pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1])
                    cum_nm += d
                    if pts[i - 1][2] and pts[i][2]:
                        dt_h = (pts[i][2] - pts[i - 1][2]).total_seconds() / 3600.0
                        if dt_h > 0 and dt_h < 6:  # ignore long gaps
                            speeds.append(d / dt_h)

                stated_nm = None
                if current["cmt"]:
                    m = re.search(r"([\d,]+\.?\d*)\s*nm", current["cmt"])
                    if m:
                        stated_nm = float(m.group(1).replace(",", ""))

                avg_speed = (
                    cum_nm / duration_hours if duration_hours and duration_hours > 0 else None
                )
                max_speed = max(speeds) if speeds else None

                leg_id = current["number"] or (len(legs) + 1)
                leg = {
                    "id": leg_id,
                    "name": current["name"],
                    "description": current["desc"],
                    "start": start_t.isoformat() if start_t else None,
                    "end": end_t.isoformat() if end_t else None,
                    "duration_hours": round(duration_hours, 2) if duration_hours else None,
                    "points": len(pts),
                    "stated_nm": stated_nm,
                    "computed_nm": round(cum_nm, 1),
                    "avg_speed_kn": round(avg_speed, 2) if avg_speed else None,
                    "max_speed_kn": round(max_speed, 2) if max_speed else None,
                    "bbox": [min(lons), min(lats), max(lons), max(lats)],
                }
                legs.append(leg)

                # Write per-leg GeoJSON
                # Downsample heavy legs to keep payloads reasonable for browser
                MAX_PTS = 3000
                step = max(1, len(pts) // MAX_PTS)
                sampled = pts[::step]
                if sampled[-1] != pts[-1]:
                    sampled.append(pts[-1])

                geojson = {
                    "type": "Feature",
                    "properties": {
                        "leg_id": leg_id,
                        "name": current["name"],
                        "stated_nm": stated_nm,
                        "computed_nm": round(cum_nm, 1),
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[p[1], p[0]] for p in sampled],
                    },
                    "times": [p[2].isoformat() if p[2] else None for p in sampled],
                    "elevations": [p[3] for p in sampled],
                }
                with open(
                    os.path.join(GEOJSON_DIR, f"leg_{leg_id:02d}.geojson"), "w"
                ) as f:
                    json.dump(geojson, f)

                print(
                    f"  Leg {leg_id:>2}: {current['name'][:55]:<55} "
                    f"{len(pts):>6} pts  {round(cum_nm, 1):>7} nm  "
                    f"{round(duration_hours, 1) if duration_hours else '?':>5} h"
                )

                elem.clear()
                current = None
                points_buffer = []

    with open(os.path.join(OUT_DIR, "legs_index.json"), "w") as f:
        json.dump(legs, f, indent=2)

    total_nm = sum(l["computed_nm"] for l in legs if l["computed_nm"])
    print(f"\nWrote {len(legs)} legs.")
    print(f"Total computed distance: {total_nm:,.1f} nm")


if __name__ == "__main__":
    main()
