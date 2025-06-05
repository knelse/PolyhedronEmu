import unittest
import sys
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from utils.time_utils import get_ingame_time, encode_ingame_time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestTimeUtils(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Reference date: 1998-08-21 10:00:00 UTC
        self.reference_date = datetime(1998, 8, 21, 10, 0, 0, tzinfo=timezone.utc)
        self.reference_timestamp = self.reference_date.timestamp()

    def test_get_ingame_time_at_reference(self):
        """Test that ingame time equals year 1 at the reference date."""
        with patch("time.time", return_value=self.reference_timestamp):
            ingame_time = get_ingame_time()

            # At reference time, ingame time should be year 1
            self.assertEqual(ingame_time.year, 1)
            self.assertEqual(ingame_time.month, 1)
            self.assertEqual(ingame_time.day, 1)
            self.assertEqual(ingame_time.hour, 0)
            self.assertEqual(ingame_time.minute, 0)
            self.assertEqual(ingame_time.second, 0)

    def test_get_ingame_time_future(self):
        """Test ingame time calculation for a future date."""
        # Test 1 hour (3600 seconds) after reference
        future_timestamp = self.reference_timestamp + 3600

        with patch("time.time", return_value=future_timestamp):
            ingame_time = get_ingame_time()

            # 1 hour * 12 = 12 hours should have passed in game time
            expected_time = datetime(1, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

            self.assertEqual(ingame_time.year, expected_time.year)
            self.assertEqual(ingame_time.month, expected_time.month)
            self.assertEqual(ingame_time.day, expected_time.day)
            self.assertEqual(ingame_time.hour, expected_time.hour)
            self.assertEqual(ingame_time.minute, expected_time.minute)
            self.assertEqual(ingame_time.second, expected_time.second)

    def test_get_ingame_time_acceleration(self):
        """Test that time acceleration factor of 12 is applied correctly."""
        # Test 24 real hours = 24 * 3600 = 86400 seconds
        future_timestamp = self.reference_timestamp + 86400

        with patch("time.time", return_value=future_timestamp):
            ingame_time = get_ingame_time()

            # 24 hours * 12 = 288 hours = 12 days in game time
            # Starting from year 1, day 1, we should be at day 13
            self.assertEqual(ingame_time.day, 13)

    def test_get_ingame_time_long_period(self):
        """Test ingame time for a longer period."""
        # Test 365 real days after reference
        days_to_add = 365
        future_timestamp = self.reference_timestamp + (days_to_add * 24 * 3600)

        with patch("time.time", return_value=future_timestamp):
            ingame_time = get_ingame_time()

            # 365 real days * 12 = 4380 game days = ~12 game years
            # Should be around year 13
            self.assertGreaterEqual(ingame_time.year, 12)
            self.assertLessEqual(ingame_time.year, 14)

    def test_get_ingame_time_consistency(self):
        """Test that ingame time is consistent between calls."""
        test_timestamp = self.reference_timestamp + 1000

        with patch("time.time", return_value=test_timestamp):
            time1 = get_ingame_time()
            time2 = get_ingame_time()

            # Should be identical since we're mocking time.time()
            self.assertEqual(time1, time2)

    def test_encode_ingame_time_structure(self):
        """Test that encode_ingame_time returns bytes."""
        with patch("time.time", return_value=self.reference_timestamp + 3600):
            encoded = encode_ingame_time()

            # Should return bytes
            self.assertIsInstance(encoded, bytes)

            # Should have some length (our encoding uses specific bit counts)
            self.assertGreater(len(encoded), 0)

    def test_encode_ingame_time_different_times(self):
        """Test that different times produce different encodings."""
        # Encode time at reference
        with patch("time.time", return_value=self.reference_timestamp):
            encoded1 = encode_ingame_time()

        # Encode time 1 hour later
        with patch("time.time", return_value=self.reference_timestamp + 3600):
            encoded2 = encode_ingame_time()

        # Should be different
        self.assertNotEqual(encoded1, encoded2)

    def test_encode_ingame_time_specific_values(self):
        """Test encoding with specific time values that we can verify."""
        # Use a specific time that will give us predictable values
        test_timestamp = self.reference_timestamp + (12 * 3600)  # 12 hours later

        with patch("time.time", return_value=test_timestamp):
            encoded = encode_ingame_time()

            # The encoded data should represent the ingame time components
            # We can't easily decode without implementing a decoder, but we can
            # verify the data has the expected structure
            self.assertIsInstance(encoded, bytes)
            self.assertGreater(len(encoded), 4)  # Should be at least a few bytes

    def test_ingame_time_timezone(self):
        """Test that ingame time uses UTC timezone."""
        with patch("time.time", return_value=self.reference_timestamp):
            ingame_time = get_ingame_time()

            self.assertEqual(ingame_time.tzinfo, timezone.utc)

    def test_time_calculation_precision(self):
        """Test precision of time calculations."""
        # Test with fractional seconds
        test_timestamp = (
            self.reference_timestamp + 3661.5
        )  # 1 hour, 1 minute, 1.5 seconds

        with patch("time.time", return_value=test_timestamp):
            ingame_time = get_ingame_time()

            # Should handle fractional seconds correctly
            # 3661.5 * 12 = 43938 seconds = 12 hours, 12 minutes, 18 seconds
            expected_hours = 12
            expected_minutes = 12
            expected_seconds = 18

            self.assertEqual(ingame_time.hour, expected_hours)
            self.assertEqual(ingame_time.minute, expected_minutes)
            self.assertEqual(ingame_time.second, expected_seconds)

    def test_edge_case_year_boundaries(self):
        """Test behavior around year boundaries."""
        # Calculate timestamp for exactly 1 year of game time
        # 1 game year ≈ 365.25 * 24 * 3600 = 31,557,600 game seconds
        # Real time = game time / 12 = 2,629,800 real seconds ≈ 30.4 real days
        one_game_year_real_seconds = (365.25 * 24 * 3600) / 12
        test_timestamp = self.reference_timestamp + one_game_year_real_seconds

        with patch("time.time", return_value=test_timestamp):
            ingame_time = get_ingame_time()

            # Should be around year 2
            self.assertGreaterEqual(ingame_time.year, 1)
            self.assertLessEqual(ingame_time.year, 3)

    def test_encode_decode_consistency(self):
        """Test that encoding produces consistent results for the same time."""
        test_timestamp = self.reference_timestamp + 7200  # 2 hours

        with patch("time.time", return_value=test_timestamp):
            encoded1 = encode_ingame_time()
            encoded2 = encode_ingame_time()

            # Should be identical
            self.assertEqual(encoded1, encoded2)

    def test_reference_date_constants(self):
        """Test that reference date constants are correct."""
        # Verify our reference date is what we expect
        self.assertEqual(self.reference_date.year, 1998)
        self.assertEqual(self.reference_date.month, 8)
        self.assertEqual(self.reference_date.day, 21)
        self.assertEqual(self.reference_date.hour, 10)
        self.assertEqual(self.reference_date.minute, 0)
        self.assertEqual(self.reference_date.second, 0)

    def test_time_progression(self):
        """Test that ingame time progresses correctly over multiple calls."""
        base_timestamp = self.reference_timestamp + 1000

        times = []
        for i in range(5):
            timestamp = base_timestamp + (i * 3600)  # Each hour
            with patch("time.time", return_value=timestamp):
                times.append(get_ingame_time())

        # Each subsequent time should be later than the previous
        for i in range(1, len(times)):
            self.assertGreater(times[i], times[i - 1])

            # Should be exactly 12 hours apart (12x acceleration)
            time_diff = times[i] - times[i - 1]
            expected_diff = timedelta(hours=12)
            self.assertEqual(time_diff, expected_diff)


if __name__ == "__main__":
    unittest.main()
