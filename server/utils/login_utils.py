"""
Login utilities for parsing authentication data from byte streams.

This module provides functions for extracting login credentials from
encrypted or encoded byte data received from clients.
"""


def get_encrypted_login_and_password(data: bytes) -> tuple[bytearray, bytearray]:
    """
    Extract login and password from a byte stream using a specific algorithm.

    Algorithm:
    1. Start from byte number 18 (0-indexed)
    2. Read bytes and append to login until encountering byte value 0 or 1
    3. Continue reading bytes for password until end of data or encountering byte value 0
    4. Return login and password as tuple of bytearrays

    All data is assumed to be in win-1251 encoding where each character fits in a single byte.

    Args:
        data (bytes): The input byte stream containing login data

    Returns:
        tuple[bytearray, bytearray]: A tuple containing (login, password) as bytearrays

    Raises:
        ValueError: If the input data is too short or malformed
    """
    if len(data) < 18:
        raise ValueError(
            f"Input data too short: expected at least 18 bytes, got {len(data)}"
        )

    current_index = 18
    login_bytes = bytearray()
    password_bytes = bytearray()

    while current_index < len(data):
        byte_value = data[current_index]

        if byte_value == 0 or byte_value == 1:
            break

        login_bytes.append(byte_value)
        current_index += 1

    current_index += 1

    while current_index < len(data):
        byte_value = data[current_index]

        if byte_value == 0:
            break

        password_bytes.append(byte_value)
        current_index += 1

    return (login_bytes, password_bytes)


def decrypt_login_and_password(
    login_bytes: bytearray, password_bytes: bytearray
) -> tuple[str, str]:
    """
    Decrypt login and password bytearrays using a specific decryption algorithm.

    Algorithm:
    1. For login, subtract 3 from the value of byte 0. For password, add 1 to the value of byte 0
    2. Iterate through every byte in the arrays
    3. If byte value is even, the decoded value is (byte_value / 4) - 1 + 'A'
    4. If byte value is odd, the decoded value is (byte_value / 4) - 48 + '0'
    5. Result should return both as win-1251 strings

    Args:
        login_bytes (bytearray): The encrypted login data
        password_bytes (bytearray): The encrypted password data

    Returns:
        tuple[str, str]: A tuple containing (decrypted_login, decrypted_password)
                        as win-1251 strings

    Raises:
        ValueError: If decryption fails or produces invalid characters
    """

    def decrypt_bytearray(data: bytearray, first_byte_offset: int) -> str:
        """Helper function to decrypt a single bytearray."""
        if len(data) == 0:
            return ""

        # Create a working copy to avoid modifying the original
        working_data = bytearray(data)

        # Apply offset to first byte
        if len(working_data) > 0:
            working_data[0] = (working_data[0] + first_byte_offset) % 256

        decrypted_chars = []

        for byte_value in working_data:
            try:
                if byte_value % 2 == 0:  # Even
                    # (byte_value / 4) - 1 + 'A'
                    decoded_value = int(byte_value / 4) - 1 + ord("A")
                else:  # Odd
                    # (byte_value / 4) - 48 + '0'
                    decoded_value = int(byte_value / 4) - 48 + ord("0")

                # Ensure the decoded value is a valid byte (0-255)
                if decoded_value < 0 or decoded_value > 255:
                    raise ValueError(
                        f"Decoded value {decoded_value} out of valid range (0-255)"
                    )

                decrypted_chars.append(chr(decoded_value))

            except (ValueError, OverflowError) as e:
                raise ValueError(f"Failed to decrypt byte {byte_value}: {e}")

        # Join characters and encode/decode through win-1251
        try:
            decrypted_string = "".join(decrypted_chars)
            return decrypted_string.encode("cp1251", errors="replace").decode("cp1251")
        except LookupError:
            # Fallback to latin-1 which is always available
            return decrypted_string.encode("latin-1", errors="replace").decode(
                "latin-1"
            )
        except (UnicodeEncodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Encoding error: {e}")

    try:
        decrypted_login = decrypt_bytearray(login_bytes, -3)  # Subtract 3
        decrypted_password = decrypt_bytearray(password_bytes, 1)  # Add 1

        return (decrypted_login, decrypted_password)

    except Exception as e:
        raise ValueError(f"Decryption failed: {e}")


def get_login_data_info(data: bytes) -> dict:
    """
    Get detailed information about login data structure for debugging.

    Args:
        data (bytes): The input byte stream

    Returns:
        dict: Information about the data structure
    """
    if len(data) < 18:
        return {
            "valid": False,
            "error": f"Data too short: {len(data)} bytes (minimum 18 required)",
            "total_length": len(data),
        }

    # Find delimiter positions
    delimiter_positions = []
    terminator_positions = []

    for i in range(18, len(data)):
        if data[i] == 0:
            terminator_positions.append(i)
        elif data[i] == 1:
            delimiter_positions.append(i)

    return {
        "valid": True,
        "total_length": len(data),
        "start_offset": 18,
        "data_section_length": len(data) - 18,
        "delimiter_positions": delimiter_positions,
        "terminator_positions": terminator_positions,
        "header_bytes": data[:18].hex().upper(),
        "data_section_hex": data[18:].hex().upper() if len(data) > 18 else "",
    }
