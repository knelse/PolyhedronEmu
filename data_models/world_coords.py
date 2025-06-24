"""
World coordinates representation and encoding utilities.
"""

import math
from typing import List


class WorldCoords:
    """Represents world coordinates with X, Y, Z position and angle."""

    def __init__(
        self, x: float = 0.0, y: float = 0.0, z: float = 0.0, angle: float = 0.0
    ):
        """
        Initialize world coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
            z: Z coordinate
            angle: Angle in degrees or radians
        """
        self.x: float = x
        self.y: float = y
        self.z: float = z
        self.angle: float = angle

    @staticmethod
    def encode_server_coord(a: float) -> List[int]:
        """
        Encode a coordinate value for server transmission.

        Args:
            a: The coordinate value to encode

        Returns:
            List of 4 bytes representing the encoded coordinate
        """
        scale = 69

        a_abs = abs(a)
        a_temp = a_abs

        steps = 0

        if int(a_abs) == 0:
            scale = 58
        elif a_temp < 2048:
            while a_temp < 2048:
                a_temp *= 2
                steps += 1

            scale -= (steps + 1) // 2

            if scale < 0:
                scale = 58
        else:
            while a_temp > 4096:
                a_temp /= 2
                steps += 1

            scale += steps // 2

        a_3 = ((1 if a < 0 else 0) << 7) + scale

        if a_abs == 0:
            mul = 1
            num_to_encode = 0b100000000000000000000000
        else:
            mul = math.pow(2, int(math.log(a_abs, 2)))
            num_to_encode = int(0b100000000000000000000000 * (a_abs / mul + 1))

        a_2 = ((num_to_encode & 0b111111110000000000000000) >> 16) + (
            0b10000000 if steps % 2 == 1 else 0
        )
        a_1 = (num_to_encode & 0b1111111100000000) >> 8
        a_0 = num_to_encode & 0b11111111

        return [a_0, a_1, a_2, a_3]

    def __str__(self) -> str:
        """String representation of world coordinates."""
        return f"WorldCoords(x={self.x}, y={self.y}, z={self.z}, angle={self.angle})"

    def __repr__(self) -> str:
        """Detailed string representation of world coordinates."""
        return self.__str__()
