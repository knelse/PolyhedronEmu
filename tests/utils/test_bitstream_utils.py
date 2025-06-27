import unittest
import sys
import os
from utils.bitstream_utils import simple_bit_stream

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestSimpleBitStream(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.stream = simple_bit_stream()

    def test_write_read_basic(self):
        """Test basic write_int and read_int functionality."""
        # Test writing 4 bits with value 10 (binary: 1010)
        self.stream.write_int(10, 4)
        self.stream.reset_read_position()
        result = self.stream.read_int(4)
        self.assertEqual(result, 10)

    def test_write_read_single_bit(self):
        """Test writing and reading single bits."""
        self.stream.write_bit(True)
        self.stream.write_bit(False)
        self.stream.write_bit(True)

        self.stream.reset_read_position()
        self.assertEqual(self.stream.read_bit(), True)
        self.assertEqual(self.stream.read_bit(), False)
        self.assertEqual(self.stream.read_bit(), True)

    def test_write_read_full_byte(self):
        """Test writing and reading full 8-bit values."""
        test_values = [0, 255, 127, 128, 85, 170]  # Various bit patterns

        for value in test_values:
            with self.subTest(value=value):
                stream = simple_bit_stream()
                stream.write_int(value, 8)
                stream.reset_read_position()
                result = stream.read_int(8)
                self.assertEqual(result, value)

    def test_write_read_larger_values(self):
        """Test writing and reading larger bit values."""
        # Test 16-bit value
        self.stream.write_int(65535, 16)  # Max 16-bit value
        self.stream.reset_read_position()
        result = self.stream.read_int(16)
        self.assertEqual(result, 65535)

        # Test 12-bit value
        stream2 = simple_bit_stream()
        stream2.write_int(4095, 12)  # Max 12-bit value (0xFFF)
        stream2.reset_read_position()
        result = stream2.read_int(12)
        self.assertEqual(result, 4095)

    def test_write_read_bytes(self):
        """Test writing and reading byte arrays."""
        test_data = bytes([0x01, 0x02, 0x03, 0xFF, 0x00, 0xAB])

        self.stream.write_bytes(test_data)
        self.stream.reset_read_position()
        result = self.stream.read_bytes(len(test_data))

        self.assertEqual(result, test_data)

    def test_mixed_bit_sizes(self):
        """Test writing and reading different bit sizes in sequence."""
        # Write: 4 bits (10), 6 bits (45), 3 bits (7), 5 bits (16)
        self.stream.write_int(10, 4)  # 1010
        self.stream.write_int(45, 6)  # 101101
        self.stream.write_int(7, 3)  # 111
        self.stream.write_int(16, 5)  # 10000

        self.stream.reset_read_position()
        self.assertEqual(self.stream.read_int(4), 10)
        self.assertEqual(self.stream.read_int(6), 45)
        self.assertEqual(self.stream.read_int(3), 7)
        self.assertEqual(self.stream.read_int(5), 16)

    def test_error_conditions(self):
        """Test error conditions and edge cases."""

        # Test negative bit count
        with self.assertRaises(ValueError):
            self.stream.write_int(10, -1)

        # Test zero bit count
        with self.assertRaises(ValueError):
            self.stream.write_int(10, 0)

        # Test reading with invalid bit count
        with self.assertRaises(ValueError):
            self.stream.read_int(-1)

        with self.assertRaises(ValueError):
            self.stream.read_int(0)

    def test_boundary_values(self):
        """Test boundary values for different bit sizes."""
        test_cases = [
            (1, 1),  # 1 bit: max value 1
            (3, 2),  # 2 bits: max value 3
            (15, 4),  # 4 bits: max value 15
            (255, 8),  # 8 bits: max value 255
            (1023, 10),  # 10 bits: max value 1023
        ]

        for value, bits in test_cases:
            with self.subTest(value=value, bits=bits):
                stream = simple_bit_stream()
                stream.write_int(value, bits)
                stream.reset_read_position()
                result = stream.read_int(bits)
                self.assertEqual(result, value)

    def test_bit_precision(self):
        """Test that only the specified number of bits are used."""
        # Write a value that has more bits than we specify
        value = 0b11111111  # 255 in 8 bits

        # Write only 4 bits of this value
        self.stream.write_int(value, 4)
        self.stream.reset_read_position()
        result = self.stream.read_int(4)

        # Should get only the lower 4 bits: 1111 = 15
        self.assertEqual(result, 15)

    def test_complex_sequence(self):
        """Test a complex sequence of mixed operations."""
        # Simulate encoding game time data
        seconds = 45
        minutes = 30
        hours = 14
        days = 15
        months = 8
        years = 2024

        self.stream.write_int(seconds, 6)  # 0-59 seconds
        self.stream.write_int(minutes, 6)  # 0-59 minutes
        self.stream.write_int(hours, 5)  # 0-23 hours
        self.stream.write_int(days, 5)  # 1-31 days
        self.stream.write_int(months, 4)  # 1-12 months
        self.stream.write_int(years, 11)  # Up to 2047 years

        self.stream.reset_read_position()
        self.assertEqual(self.stream.read_int(6), seconds)
        self.assertEqual(self.stream.read_int(6), minutes)
        self.assertEqual(self.stream.read_int(5), hours)
        self.assertEqual(self.stream.read_int(5), days)
        self.assertEqual(self.stream.read_int(4), months)
        self.assertEqual(self.stream.read_int(11), years)

    def test_auto_bit_count(self):
        """Test automatic bit count determination."""
        # Test with different values
        test_cases = [
            (0, 1),  # 0 should use 1 bit
            (1, 1),  # 1 should use 1 bit
            (2, 2),  # 2 should use 2 bits
            (7, 3),  # 7 should use 3 bits
            (255, 8),  # 255 should use 8 bits
        ]

        for value, expected_bits in test_cases:
            with self.subTest(value=value):
                stream = simple_bit_stream()
                stream.write_int(value)  # No bit count specified

                # The bit count should be auto-determined
                expected_bit_length = expected_bits
                self.assertEqual(stream.get_bit_length(), expected_bit_length)

    def test_to_bytes_conversion(self):
        """Test converting stream to bytes."""
        # Write some test data
        self.stream.write_int(0xFF, 8)
        self.stream.write_int(0x00, 8)
        self.stream.write_int(0xAB, 8)

        result = self.stream.to_bytes()
        expected = bytes([0xFF, 0x00, 0xAB])
        self.assertEqual(result, expected)

    def test_utility_methods(self):
        """Test utility methods of simple_bit_stream."""
        # Test empty stream
        self.assertTrue(self.stream.is_empty())
        self.assertEqual(self.stream.get_bit_length(), 0)
        self.assertEqual(self.stream.get_byte_length(), 0)
        self.assertEqual(self.stream.available_bits(), 0)

        # Add some data
        self.stream.write_int(255, 8)

        self.assertFalse(self.stream.is_empty())
        self.assertEqual(self.stream.get_bit_length(), 8)
        self.assertEqual(self.stream.get_byte_length(), 1)
        self.assertEqual(self.stream.available_bits(), 8)

        # Read some data
        self.stream.read_int(4)
        self.assertEqual(self.stream.available_bits(), 4)

    def test_initialization_with_data(self):
        """Test initializing simple_bit_stream with existing data."""
        initial_data = bytes([0x01, 0x02, 0x03])
        stream = simple_bit_stream(initial_data)

        # Should be able to read the initial data
        result = stream.read_bytes(len(initial_data))
        self.assertEqual(result, initial_data)

        # Write position should be at the end
        self.assertEqual(stream.get_bit_length(), len(initial_data) * 8)


if __name__ == "__main__":
    unittest.main()
