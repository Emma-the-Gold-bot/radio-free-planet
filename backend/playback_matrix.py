"""
Basic playback validation matrix for direct and proxied stream paths.

Run with backend server running on localhost:8000:
    source venv/bin/activate
    python playback_matrix.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

from sync_bad_stations import main as sync_bad_station_statuses


BASE_URL = "http://127.0.0.1:8000"
OUTPUT_PATH = Path(__file__).resolve().parent / "playback_matrix_report.json"
BAD_LIST_PATH = Path(__file__).resolve().parent.parent / "static" / "data" / "bad_stations.json"


def test_direct(client: httpx.Client, url: str) -> tuple[bool, str]:
    try:
        response = client.head(url, follow_redirects=True, timeout=8.0)
        return response.status_code == 200, f"status={response.status_code}"
    except Exception as exc:  # pragma: no cover
        return False, str(exc)


def test_proxy(client: httpx.Client, station_id: str, stream_index: int) -> tuple[bool, str]:
    try:
        response = client.get(
            f"{BASE_URL}/api/proxy/health/{station_id}",
            params={},
            timeout=10.0,
        )
        if response.status_code != 200:
            return False, f"status={response.status_code}"
        payload = response.json()
        stream_entries = payload.get("streams", [])
        stream = next((entry for entry in stream_entries if entry.get("stream_index") == stream_index), None)
        if not stream:
            return False, "missing_stream_health_entry"
        if stream.get("healthy"):
            return True, "ok"
        return False, stream.get("error") or f"status={stream.get('status')}"
    except Exception as exc:  # pragma: no cover
        return False, str(exc)


def normalize_reason(detail: str) -> str:
    detail_lower = detail.lower()
    if "name or service not known" in detail_lower:
        return "dns_not_resolved"
    if "temporary failure in name resolution" in detail_lower:
        return "dns_resolution_failure"
    if "server disconnected without sending a response" in detail_lower:
        return "upstream_disconnected"
    if detail_lower.startswith("status="):
        return f"http_{detail.split('=', 1)[1]}"
    return "unknown"


def update_bad_station_registry(report: dict) -> tuple[int, int]:
    bad_rows = [
        row
        for row in report["stations"]
        if (not row["direct"]["ok"]) and (not row["proxy"]["ok"])
    ]

    bad_ids = sorted({row["station_id"] for row in bad_rows})
    failures = []
    for row in bad_rows:
        failures.append(
            {
                "id": row["station_id"],
                "reason": normalize_reason(row["direct"]["detail"]),
            }
        )

    payload = {
        "version": "1.0.0",
        "last_checked": datetime.now(timezone.utc).isoformat(),
        "source_report": "backend/playback_matrix_report.json",
        "notes": (
            "Stations in this list failed both direct and proxied health checks in the latest matrix run. "
            "Treat as blocked during future station ingestion until manually revalidated."
        ),
        "bad_station_ids": bad_ids,
        "failures": failures,
    }

    BAD_LIST_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return len(bad_ids), len(failures)


def main() -> None:
    report = {"base_url": BASE_URL, "stations": []}
    with httpx.Client(timeout=10.0) as client:
        stations_resp = client.get(f"{BASE_URL}/api/stations")
        stations_resp.raise_for_status()
        stations = stations_resp.json()

        for station in stations:
            station_id = station["id"]
            mode = station.get("playback_mode", "unknown")
            for index, stream in enumerate(station.get("streams", [])):
                direct_ok, direct_detail = test_direct(client, stream["url"])
                proxy_ok, proxy_detail = test_proxy(client, station_id, index)
                report["stations"].append(
                    {
                        "station_id": station_id,
                        "station_name": station.get("name"),
                        "stream_index": index,
                        "playback_mode": mode,
                        "direct": {"ok": direct_ok, "detail": direct_detail},
                        "proxy": {"ok": proxy_ok, "detail": proxy_detail},
                    }
                )

    OUTPUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    total = len(report["stations"])
    direct_ok = sum(1 for row in report["stations"] if row["direct"]["ok"])
    proxy_ok = sum(1 for row in report["stations"] if row["proxy"]["ok"])
    bad_station_count, failure_rows = update_bad_station_registry(report)
    sync_bad_station_statuses()

    print(f"Wrote report: {OUTPUT_PATH}")
    print(f"Streams tested: {total}")
    print(f"Direct healthy: {direct_ok}/{total}")
    print(f"Proxy healthy: {proxy_ok}/{total}")
    print(f"Wrote bad station list: {BAD_LIST_PATH}")
    print(f"Bad stations: {bad_station_count}")
    print(f"Failure rows captured: {failure_rows}")
    print("Synced health_status markers in stations.json from bad_stations.json")


if __name__ == "__main__":
    main()
