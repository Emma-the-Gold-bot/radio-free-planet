"""
Sync health_status markers in stations.json from bad_stations.json.

Usage:
  source venv/bin/activate
  python sync_bad_stations.py
"""

from __future__ import annotations

from pathlib import Path
import json


PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIONS_PATH = PROJECT_ROOT / "static" / "data" / "stations.json"
BAD_LIST_PATH = PROJECT_ROOT / "static" / "data" / "bad_stations.json"


def main() -> None:
    stations_doc = json.loads(STATIONS_PATH.read_text(encoding="utf-8"))
    bad_doc = json.loads(BAD_LIST_PATH.read_text(encoding="utf-8"))

    bad_ids = set(bad_doc.get("bad_station_ids", []))
    stations = stations_doc.get("stations", [])
    by_id = {station.get("id"): station for station in stations}

    changed_to_bad = 0
    changed_to_validated = 0

    # Enforce bad list.
    for station_id in bad_ids:
        station = by_id.get(station_id)
        if not station:
            continue
        if station.get("health_status") != "bad":
            station["health_status"] = "bad"
            changed_to_bad += 1

    # Keep healthy stations explicit to avoid ambiguous state.
    for station in stations:
        if station.get("id") in bad_ids:
            continue
        if station.get("health_status") == "bad":
            station["health_status"] = "validated"
            changed_to_validated += 1

    missing = sorted(station_id for station_id in bad_ids if station_id not in by_id)

    stations_doc["last_updated"] = bad_doc.get("last_checked", stations_doc.get("last_updated"))
    STATIONS_PATH.write_text(json.dumps(stations_doc, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    print(f"stations_total={len(stations)}")
    print(f"bad_list_total={len(bad_ids)}")
    print(f"changed_to_bad={changed_to_bad}")
    print(f"changed_to_validated={changed_to_validated}")
    print(f"missing_bad_ids={len(missing)}")
    if missing:
        print("missing_ids=" + ",".join(missing))


if __name__ == "__main__":
    main()
