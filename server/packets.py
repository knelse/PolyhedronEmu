"""
Constants and definitions for server packets.

This module contains packet definitions and constants used for communication
between the server and clients.
"""


class ServerPackets:
    """Container for server-to-client packet definitions."""

    # Initialization packet sent to new clients when they connect
    INIT_PACKET = bytes([
        0x0A, 0x00, 0xC8, 0x00, 0x6C, 0x07, 0x00, 0x00, 0x40, 0x0E
    ])


# Convenience constants for direct access
INIT_PACKET = ServerPackets.INIT_PACKET
