from __future__ import annotations

import unittest
from datetime import datetime, timezone

from schedule_pipeline.contracts import ShowSlot, StationSchedule, empty_week_schedule
from schedule_pipeline.resolver import resolve_now_playing_for_station


class ResolverTests(unittest.TestCase):
    def test_resolves_current_slot(self) -> None:
        schedule = empty_week_schedule()
        schedule["monday"] = [
            ShowSlot(
                title="Morning",
                host="Host A",
                start_time="09:00",
                end_time="11:00",
                day_of_week=0,
                genre="rock",
            )
        ]
        station_schedule = StationSchedule(
            station_id="test-station",
            station_name="Test Station",
            timezone_name="UTC",
            source_tier="tier3_seed",
            confidence=0.6,
            schedule=schedule,
            last_success=datetime.now(timezone.utc).isoformat(),
        )

        result = resolve_now_playing_for_station(
            station_schedule,
            now_utc=datetime(2026, 2, 23, 9, 30, tzinfo=timezone.utc),
        )
        self.assertIsNotNone(result["show"])
        self.assertEqual(result["show"]["title"], "Morning")

    def test_handles_overnight_slot(self) -> None:
        schedule = empty_week_schedule()
        schedule["monday"] = [
            ShowSlot(
                title="Overnight",
                host="Host B",
                start_time="22:00",
                end_time="02:00",
                day_of_week=0,
                genre="ambient",
            )
        ]
        station_schedule = StationSchedule(
            station_id="overnight-station",
            station_name="Overnight Station",
            timezone_name="UTC",
            source_tier="tier3_seed",
            confidence=0.6,
            schedule=schedule,
            last_success=datetime.now(timezone.utc).isoformat(),
        )

        result = resolve_now_playing_for_station(
            station_schedule,
            now_utc=datetime(2026, 2, 23, 23, 30, tzinfo=timezone.utc),
        )
        self.assertIsNotNone(result["show"])
        self.assertEqual(result["show"]["title"], "Overnight")


if __name__ == "__main__":
    unittest.main()

