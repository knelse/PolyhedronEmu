"""
Constants and definitions for server packets.

This module contains packet definitions and constants used for communication
between the server and clients.
"""


INIT_PACKET = bytes([
    0xD1, 0x70, 0x20, 0x02,
    0x63, 0x5F, 0x00, 0x00
])
# INIT_PACKET: Sent to clients upon successful connection
