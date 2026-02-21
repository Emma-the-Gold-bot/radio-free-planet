from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from main import app, parse_show_payload


class NowPlayingApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_parse_show_payload_legacy_shape(self) -> None:
        payload = parse_show_payload(
            {
                "show_title": "Legacy Show",
                "host": "Legacy Host",
                "genre": "rock",
                "start_time": "09:00",
                "end_time": "10:00",
            }
        )
        self.assertEqual(payload["title"], "Legacy Show")
        self.assertEqual(payload["genres"], ["rock"])

    def test_unknown_station_filter_returns_empty(self) -> None:
        response = self.client.get("/api/now-playing", params={"station_id": "not-a-real-station-id"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_now_playing_excludes_bad_stations(self) -> None:
        response = self.client.get("/api/now-playing")
        self.assertEqual(response.status_code, 200)
        for item in response.json():
            station = item.get("station") or {}
            self.assertNotEqual(station.get("health_status"), "bad")


if __name__ == "__main__":
    unittest.main()

