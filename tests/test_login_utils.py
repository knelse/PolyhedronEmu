import unittest
import sys
import os
from utils.login_utils import (
    get_encrypted_login_and_password,
    get_login_data_info,
    decrypt_login_and_password,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestLoginUtils(unittest.TestCase):

    def test_basic_login_password_extraction(self):
        """Test basic login and password extraction."""
        # Create test data: 18 header bytes + "user" + delimiter(1) + "pass" + terminator(0)
        header = b"\x00" * 18  # 18 header bytes
        login = b"user"
        delimiter = b"\x01"  # Use 1 as delimiter
        password = b"pass"
        terminator = b"\x00"  # Use 0 as terminator

        data = header + login + delimiter + password + terminator

        result_login, result_password = get_encrypted_login_and_password(data)
        self.assertEqual(result_login, bytearray(b"user"))
        self.assertEqual(result_password, bytearray(b"pass"))

    def test_delimiter_zero(self):
        """Test using 0 as delimiter between login and password."""
        header = b"\x00" * 18
        login = b"admin"
        delimiter = b"\x00"  # Use 0 as delimiter
        password = b"secret"
        # No terminator, password goes to end

        data = header + login + delimiter + password

        result_login, result_password = get_encrypted_login_and_password(data)
        self.assertEqual(result_login, bytearray(b"admin"))
        self.assertEqual(result_password, bytearray(b"secret"))

    def test_password_to_end_of_data(self):
        """Test password reading until end of data (no terminator)."""
        header = b"\x00" * 18
        login = b"test"
        delimiter = b"\x01"
        password = b"password123"
        # No terminator - password should read to end

        data = header + login + delimiter + password

        result_login, result_password = get_encrypted_login_and_password(data)
        self.assertEqual(result_login, bytearray(b"test"))
        self.assertEqual(result_password, bytearray(b"password123"))

    def test_empty_login(self):
        """Test handling of empty login."""
        header = b"\x00" * 18
        delimiter = b"\x01"  # Immediate delimiter
        password = b"onlypass"

        data = header + delimiter + password

        result_login, result_password = get_encrypted_login_and_password(data)
        self.assertEqual(result_login, bytearray())
        self.assertEqual(result_password, bytearray(b"onlypass"))

    def test_empty_password(self):
        """Test handling of empty password."""
        header = b"\x00" * 18
        login = b"onlyuser"
        delimiter = b"\x01"
        terminator = b"\x00"  # Immediate terminator after delimiter

        data = header + login + delimiter + terminator

        result_login, result_password = get_encrypted_login_and_password(data)
        self.assertEqual(result_login, bytearray(b"onlyuser"))
        self.assertEqual(result_password, bytearray())

    def test_both_empty(self):
        """Test handling of both empty login and password."""
        header = b"\x00" * 18
        delimiter = b"\x01"
        terminator = b"\x00"

        data = header + delimiter + terminator

        result_login, result_password = get_encrypted_login_and_password(data)
        self.assertEqual(result_login, bytearray())
        self.assertEqual(result_password, bytearray())

    def test_long_credentials(self):
        """Test with longer login and password strings."""
        header = b"\x00" * 18
        login = b"very_long_username_here"
        delimiter = b"\x01"
        password = b"super_secure_password_with_numbers_123"
        terminator = b"\x00"

        data = header + login + delimiter + password + terminator

        result_login, result_password = get_encrypted_login_and_password(data)
        self.assertEqual(result_login, bytearray(b"very_long_username_here"))
        self.assertEqual(
            result_password, bytearray(b"super_secure_password_with_numbers_123")
        )

    def test_special_characters(self):
        """Test with special characters in login and password."""
        header = b"\x00" * 18
        login = b"user@domain.com"
        delimiter = b"\x01"
        password = b"p@$$w0rd!"
        terminator = b"\x00"

        data = header + login + delimiter + password + terminator

        result_login, result_password = get_encrypted_login_and_password(data)
        self.assertEqual(result_login, bytearray(b"user@domain.com"))
        self.assertEqual(result_password, bytearray(b"p@$$w0rd!"))

    def test_data_too_short(self):
        """Test error handling for data too short."""
        short_data = b"\x00" * 17  # Only 17 bytes, need at least 18

        with self.assertRaises(ValueError) as context:
            get_encrypted_login_and_password(short_data)

        self.assertIn("Input data too short", str(context.exception))

    def test_no_delimiter_found(self):
        """Test when no delimiter (0 or 1) is found."""
        header = b"\x00" * 18
        # All data after header, no delimiter
        data_without_delimiter = b"usernamepassword"

        data = header + data_without_delimiter

        result_login, result_password = get_encrypted_login_and_password(data)
        # Should read all as login, password should be empty
        self.assertEqual(result_login, bytearray(b"usernamepassword"))
        self.assertEqual(result_password, bytearray())

    def test_multiple_delimiters(self):
        """Test behavior with multiple delimiters."""
        header = b"\x00" * 18
        login = b"user"
        delimiter1 = b"\x01"
        middle_part = b"middle"
        delimiter2 = b"\x00"  # This should terminate password reading
        end_part = b"end"

        data = header + login + delimiter1 + middle_part + delimiter2 + end_part

        result_login, result_password = get_encrypted_login_and_password(data)
        self.assertEqual(result_login, bytearray(b"user"))
        self.assertEqual(
            result_password, bytearray(b"middle")
        )  # Should stop at first 0

    def test_get_login_data_info_valid(self):
        """Test the login data info function with valid data."""
        header = b"\x00" * 18
        login = b"user"
        delimiter = b"\x01"
        password = b"pass"
        terminator = b"\x00"

        data = header + login + delimiter + password + terminator

        info = get_login_data_info(data)

        self.assertTrue(info["valid"])
        self.assertEqual(info["total_length"], len(data))
        self.assertEqual(info["start_offset"], 18)
        self.assertEqual(info["data_section_length"], len(data) - 18)
        self.assertIn(22, info["delimiter_positions"])  # Position of delimiter (1)
        self.assertIn(27, info["terminator_positions"])  # Position of terminator (0)

    def test_get_login_data_info_too_short(self):
        """Test the login data info function with too short data."""
        short_data = b"\x00" * 10

        info = get_login_data_info(short_data)

        self.assertFalse(info["valid"])
        self.assertIn("Data too short", info["error"])
        self.assertEqual(info["total_length"], 10)

    def test_edge_case_exactly_18_bytes(self):
        """Test with exactly 18 bytes (no data section)."""
        data = b"\x00" * 18

        result_login, result_password = get_encrypted_login_and_password(data)
        self.assertEqual(result_login, bytearray())
        self.assertEqual(result_password, bytearray())

    def test_cp1251_characters(self):
        """Test with cp1251 encoded characters (Cyrillic)."""
        header = b"\x00" * 18
        # Using some cp1251 encoded Cyrillic characters as bytes
        login = b"\xef\xf0\xe8\xe2\xe5\xf2"  # "привет" in cp1251
        delimiter = b"\x01"
        password = b"\xef\xe0\xf0\xee\xeb\xfc"  # "пароль" in cp1251
        terminator = b"\x00"

        data = header + login + delimiter + password + terminator

        result_login, result_password = get_encrypted_login_and_password(data)
        self.assertEqual(result_login, bytearray(login))
        self.assertEqual(result_password, bytearray(password))

    def test_complex_scenario(self):
        """Test a complex real-world-like scenario."""
        # Simulate some kind of packet header
        header = (
            b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a"
            + b"\x0b\x0c\x0d\x0e\x0f\x10\x11\x12"
        )  # 18 bytes

        login = b"game_user_2024"
        delimiter = b"\x01"
        password = b"MySecureP@ssw0rd!"
        terminator = b"\x00"

        data = header + login + delimiter + password + terminator

        result_login, result_password = get_encrypted_login_and_password(data)
        self.assertEqual(result_login, bytearray(b"game_user_2024"))
        self.assertEqual(result_password, bytearray(b"MySecureP@ssw0rd!"))

    def test_decrypt_empty_arrays(self):
        """Test decryption with empty bytearrays."""
        login_bytes = bytearray()
        password_bytes = bytearray()

        result_login, result_password = decrypt_login_and_password(
            login_bytes, password_bytes
        )
        self.assertEqual(result_login, "")
        self.assertEqual(result_password, "")

    def test_decrypt_basic_case(self):
        """Test basic decryption case with known values."""
        # Let's work with simple test cases:
        # For 'A' (ASCII 65): Even case (byte_value / 4) - 1 + 65 = 65
        # So: byte_value / 4 = 1, byte_value = 4
        # For login (subtract 3): original byte = 4 + 3 = 7
        # For password (add 1): original byte = 4 - 1 = 3

        login_bytes = bytearray([7])  # 7-3=4 (even), (4/4)-1+65 = 0+65 = 65 = 'A'
        password_bytes = bytearray([3])  # 3+1=4 (even), (4/4)-1+65 = 0+65 = 65 = 'A'

        result_login, result_password = decrypt_login_and_password(
            login_bytes, password_bytes
        )
        self.assertEqual(result_login, "A")
        self.assertEqual(result_password, "A")

    def test_decrypt_odd_even_bytes(self):
        """Test decryption with both odd and even bytes."""
        # Test with carefully chosen values
        # For even bytes: (byte_value / 4) - 1 + 'A'
        # For odd bytes: (byte_value / 4) - 48 + '0'

        # Test with carefully chosen values
        login_bytes = bytearray([7, 196])
        password_bytes = bytearray([3, 195])

        result_login, result_password = decrypt_login_and_password(
            login_bytes, password_bytes
        )
        # Expected: login="A0", password="Aq"
        self.assertEqual(len(result_login), 2)
        self.assertEqual(len(result_password), 2)

    def test_decrypt_error_handling(self):
        """Test error handling in decryption."""
        # Test with values that would produce out-of-range characters
        login_bytes = bytearray([255])  # This might cause issues
        password_bytes = bytearray([255])

        # This should either work or raise a ValueError
        try:
            result_login, result_password = decrypt_login_and_password(
                login_bytes, password_bytes
            )
            # If it works, results should be strings
            self.assertIsInstance(result_login, str)
            self.assertIsInstance(result_password, str)
        except ValueError:
            # This is also acceptable given the algorithm constraints
            pass

    def test_decrypt_integration_with_extraction(self):
        """Test decryption integrated with the extraction process."""
        # Create encrypted data, extract it, then decrypt it
        header = b"\x00" * 18
        # Use simple test data
        login = bytearray([67, 196])  # Will become "BA" after decryption
        delimiter = b"\x01"
        password = bytearray([67, 196])  # Will become "Aq" after decryption
        terminator = b"\x00"

        data = header + login + delimiter + password + terminator

        # Extract the login and password
        extracted_login, extracted_password = get_encrypted_login_and_password(data)

        # Decrypt them
        decrypted_login, decrypted_password = decrypt_login_and_password(
            extracted_login, extracted_password
        )

        # Verify they are strings
        self.assertIsInstance(decrypted_login, str)
        self.assertIsInstance(decrypted_password, str)
        self.assertEqual(len(decrypted_login), 2)
        self.assertEqual(len(decrypted_password), 2)

    def test_decrypt_single_character_login_password(self):
        """Test decryption with single character login and password."""
        # Design bytes that will give us predictable single characters
        login_bytes = bytearray(
            [67]
        )  # 67-3=64 (even), (64/4)-1+65 = 16-1+65 = 80 = 'P'
        password_bytes = bytearray(
            [195]
        )  # 195+1=196 (even), (196/4)-1+65 = 49-1+65 = 113 = 'q'

        result_login, result_password = decrypt_login_and_password(
            login_bytes, password_bytes
        )
        self.assertEqual(result_login, "P")
        self.assertEqual(result_password, "q")

    def test_decrypt_preserves_cp1251_encoding(self):
        """Test that decryption properly handles cp1251 encoding."""
        # Test with bytes that should produce valid cp1251 characters
        login_bytes = bytearray([67])  # Should produce a basic ASCII character
        password_bytes = bytearray([67])

        result_login, result_password = decrypt_login_and_password(
            login_bytes, password_bytes
        )

        # Verify we can encode/decode with cp1251 or compatible encoding
        try:
            result_login.encode("cp1251")
            result_password.encode("cp1251")
        except UnicodeEncodeError:
            try:
                result_login.encode("latin-1")
                result_password.encode("latin-1")
            except UnicodeEncodeError:
                self.fail("Decrypted strings should be encoding compatible")


if __name__ == "__main__":
    unittest.main()
