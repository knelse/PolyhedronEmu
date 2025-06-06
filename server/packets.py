"""
Constants and definitions for server packets.

This module contains packet definitions and constants used for communication
between the server and clients.
"""

from utils.time_utils import encode_ingame_time
from utils.bitstream_utils import SimpleBitStream


class ServerPackets:
    """Container for server-to-client packet definitions."""

    # Initialization packet sent to new clients when they connect
    INIT_PACKET = bytes([0x0A, 0x00, 0xC8, 0x00, 0x6C, 0x07, 0x00, 0x00, 0x40, 0x0E])

    def get_server_credentials(player_index: int) -> bytes:
        stream = SimpleBitStream()
        current_time = encode_ingame_time()
        stream.write_bytes(bytes([0x38, 0x00, 0x2C, 0x01, 0x00, 0x00, 0x04]))
        stream.write_int(player_index, 16)
        stream.write_bytes(bytes([0x08, 0x40, 0x20, 0x10]))
        stream.write_bytes(current_time)
        stream.write_bytes(
            bytes(
                [
                    0x7C,
                    0x12,
                    0x02,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x1A,
                    0x3B,
                    0x12,
                    0x01,
                    0x00,
                    0xFF,
                    0xFF,
                    0xFF,
                    0xFF,
                    0xFF,
                    0xFF,
                    0xFF,
                    0xFF,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x8D,
                    0x9D,
                    0x01,
                    0x00,
                    0x00,
                    0x00,
                ]
            )
        )
        return stream.to_bytes()

    def get_character_select_start_data(player_index: int) -> bytes:
        stream = SimpleBitStream()
        stream.write_bytes(bytes([0x52, 0x00, 0x2C, 0x01, 0x00, 0x00, 0x04]))
        stream.write_int(player_index, 16)
        stream.write_bytes(
            bytes(
                [
                    0x08,
                    0x40,
                    0x80,
                    0x10,
                    0x01,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                ]
            )
        )
        return stream.to_bytes()

    def get_new_character_data(player_index: int) -> bytes:
        stream = SimpleBitStream()
        stream.write_bytes(bytes([0x6C, 0x00, 0x2C, 0x01, 0x00, 0x00, 0x04]))
        stream.write_int(player_index, 16)
        stream.write_bytes(
            bytes(
                [
                    0x08,
                    0x40,
                    0x60,
                    0x79,
                    0x91,
                    0x01,
                    0x90,
                    0x01,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x0C,
                    0xC8,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0xC8,
                    0x00,
                    0x90,
                    0x01,
                    0x90,
                    0x01,
                    0x10,
                    0x00,
                    0x10,
                    0x00,
                    0x10,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x10,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0xFC,
                    0xFF,
                    0xFF,
                    0xFF,
                    0x03,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                ]
            )
        )
        return stream.to_bytes()


INIT_PACKET = ServerPackets.INIT_PACKET
