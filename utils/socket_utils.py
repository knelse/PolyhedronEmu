"""
Socket utilities for safe packet sending with error handling and logging.
"""

import socket
from typing import Optional
from server.logger import ServerLogger


class SocketUtils:
    """Utility class for socket operations with built-in error handling."""

    @staticmethod
    def send(
        client_socket: socket.socket,
        data: bytes,
        player_index: int,
        logger: ServerLogger,
        message: Optional[str] = None,
    ) -> bool:
        """
        Send data through a socket with exception handling and logging.

        Args:
            client_socket: The socket to send data through
            data: The bytes to send
            player_index: The player's unique index for logging
            logger: Logger instance for logging messages
            message: Optional custom message to log. If not provided,
                    uses a generic format: "Sent packet to player <index>: <contents>"

        Returns:
            True if the data was sent successfully, False if an exception occurred
        """
        try:
            client_socket.send(data)

            if message is None:
                message = (
                    f"Sent packet to player 0x{player_index:04X}: {data.hex().upper()}"
                )

            logger.debug(message)
            return True

        except Exception as e:
            error_message = (
                f"Failed to send packet to player 0x{player_index:04X}: "
                f"{data.hex().upper()}"
            )
            logger.log_exception(error_message, e)
            return False
