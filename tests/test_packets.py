import unittest
from server.packets import ServerPackets, INIT_PACKET


class TestPackets(unittest.TestCase):
    """Test packet definitions."""

    def test_server_packets_class_exists(self):
        """Test that ServerPackets class exists and has expected structure."""
        self.assertTrue(hasattr(ServerPackets, 'INIT_PACKET'))
        self.assertIsInstance(ServerPackets.INIT_PACKET, bytes)

    def test_init_packet_content(self):
        """Test that INIT_PACKET has the correct content."""
        expected_bytes = bytes([
            0x0A, 0x00, 0xC8, 0x00, 0x6C, 0x07, 0x00, 0x00, 0x40, 0x0E
        ])
        self.assertEqual(ServerPackets.INIT_PACKET, expected_bytes)
        self.assertEqual(INIT_PACKET, expected_bytes)

    def test_init_packet_length(self):
        """Test that INIT_PACKET has the correct length."""
        self.assertEqual(len(INIT_PACKET), 10)

    def test_init_packet_immutable(self):
        """Test that INIT_PACKET is immutable (bytes object)."""
        self.assertIsInstance(INIT_PACKET, bytes)
        self.assertNotIsInstance(INIT_PACKET, bytearray)
        self.assertNotIsInstance(INIT_PACKET, list)

    def test_init_packet_hex_representation(self):
        """Test the hex representation of INIT_PACKET."""
        expected_hex = "0a00c8006c070000400e"
        self.assertEqual(INIT_PACKET.hex(), expected_hex)

    def test_convenience_constant_matches_class_attribute(self):
        """Test that convenience constant matches class attribute."""
        self.assertIs(INIT_PACKET, ServerPackets.INIT_PACKET)

    def test_packet_structure_breakdown(self):
        """Test individual bytes of the init packet."""
        packet_bytes = list(INIT_PACKET)
        expected_structure = [
            (0, 0x0A),
            (1, 0x00),
            (2, 0xC8),
            (3, 0x00),
            (4, 0x6C),
            (5, 0x07),
            (6, 0x00),
            (7, 0x00),
            (8, 0x40),
            (9, 0x0E)
        ]
        for index, expected_byte in expected_structure:
            self.assertEqual(
                packet_bytes[index], expected_byte,
                f"Byte at index {index} should be 0x{expected_byte:02X}, "
                f"got 0x{packet_bytes[index]:02X}"
            )


if __name__ == '__main__':
    unittest.main()
