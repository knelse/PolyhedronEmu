class SimpleBitStream:
    """
    A simple bitstream implementation for reading and writing bits, integers, and bytes.
    """

    def __init__(self, data: bytes = None):
        """
        Initialize the bitstream.

        Args:
            data (bytes, optional): Initial data to populate the stream
        """
        self.data = bytearray(data) if data else bytearray()
        self.write_bit_position = 0
        self.read_bit_position = 0

        if data:
            # If initialized with data, set write position to end
            self.write_bit_position = len(data) * 8

    def write_bit(self, bit: bool) -> None:
        """Write a single bit to the stream."""
        byte_index = self.write_bit_position // 8
        bit_offset = self.write_bit_position % 8

        # Extend data if needed
        while len(self.data) <= byte_index:
            self.data.append(0)

        if bit:
            self.data[byte_index] |= 1 << (7 - bit_offset)
        else:
            self.data[byte_index] &= ~(1 << (7 - bit_offset))

        self.write_bit_position += 1

    def read_bit(self) -> bool:
        """Read a single bit from the stream."""
        if self.read_bit_position >= len(self.data) * 8:
            return False

        byte_index = self.read_bit_position // 8
        bit_offset = self.read_bit_position % 8

        if byte_index >= len(self.data):
            return False

        bit = bool(self.data[byte_index] & (1 << (7 - bit_offset)))
        self.read_bit_position += 1
        return bit

    def write_int(self, value: int, num_bits: int = None) -> None:
        """
        Write an integer to the stream.

        Args:
            value (int): The integer value to write
            num_bits (int, optional): Number of bits to write.
                                    If None, auto-determine based on value
        """

        if num_bits is None:
            # Auto-determine bit count based on value
            if value == 0:
                num_bits = 1
            else:
                num_bits = value.bit_length()

        if num_bits <= 0:
            raise ValueError("Number of bits must be positive")

        # Truncate value if it's too large for the specified bit count
        mask = (1 << num_bits) - 1
        masked_value = value & mask

        # Write bits from most significant to least significant
        for bit_pos in range(num_bits - 1, -1, -1):
            bit = bool((masked_value >> bit_pos) & 1)
            self.write_bit(bit)

    def read_int(self, num_bits: int) -> int:
        """
        Read an integer from the stream.

        Args:
            num_bits (int): Number of bits to read

        Returns:
            int: The read integer value
        """
        if num_bits <= 0:
            raise ValueError("Number of bits must be positive")

        result = 0
        for i in range(num_bits):
            bit = self.read_bit()
            result = (result << 1) | (1 if bit else 0)

        return result

    def write_bytes(self, data: bytes) -> None:
        """Write a byte array to the stream."""
        for byte in data:
            self.write_int(byte, 8)

    def read_bytes(self, num_bytes: int) -> bytes:
        """
        Read a specified number of bytes from the stream.

        Args:
            num_bytes (int): Number of bytes to read

        Returns:
            bytes: The read bytes
        """
        if num_bytes < 0:
            raise ValueError("Number of bytes must be non-negative")

        result = bytearray()
        for _ in range(num_bytes):
            byte_value = self.read_int(8)
            result.append(byte_value)

        return bytes(result)

    def to_bytes(self) -> bytes:
        """Convert the entire stream to bytes."""
        return bytes(self.data)

    def reset_read_position(self) -> None:
        """Reset the read position to the beginning."""
        self.read_bit_position = 0

    def get_bit_length(self) -> int:
        """Get the number of bits written to the stream."""
        return self.write_bit_position

    def get_byte_length(self) -> int:
        """Get the number of bytes in the stream (rounded up)."""
        return len(self.data)

    def is_empty(self) -> bool:
        """Check if the stream is empty."""
        return self.write_bit_position == 0

    def available_bits(self) -> int:
        """Get the number of bits available for reading."""
        return self.write_bit_position - self.read_bit_position


def read_stream_bytes_range(stream, start_byte: int, end_byte: int) -> bytes:
    """
    Read bytes from a stream from position start_byte to end_byte.
    Compatible with both SimpleBitStream and external BitStream.

    Args:
        stream: The bitstream to read from
        start_byte (int): Starting byte position (0-based, inclusive)
        end_byte (int): Ending byte position (0-based, exclusive)

    Returns:
        bytes: The bytes from start_byte to end_byte
    """
    if start_byte < 0:
        raise ValueError("start_byte must be >= 0")
    if end_byte <= start_byte:
        raise ValueError("end_byte must be > start_byte")

    stream.reset_read_position()

    # Skip to start position by reading bytes
    if start_byte > 0:
        stream.read_bytes(start_byte)

    # Read the desired range
    num_bytes_to_read = end_byte - start_byte
    return stream.read_bytes(num_bytes_to_read)


def read_stream_bytes_to_end(stream) -> bytes:
    """
    Read all remaining bytes from the current position to the end of the stream.
    Compatible with both SimpleBitStream and external BitStream.

    Args:
        stream: The bitstream to read from

    Returns:
        bytes: All remaining bytes in the stream
    """
    available_bits = stream.available_bits()
    available_bytes = available_bits // 8
    if available_bits % 8 != 0:
        available_bytes += 1
    if available_bytes > 0:
        return stream.read_bytes(available_bytes)
    return b""
