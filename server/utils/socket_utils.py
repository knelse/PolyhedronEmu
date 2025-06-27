"""
Socket utilities for server operations.

This module provides utility functions for common socket operations
with integrated logging and error handling.
"""

import socket
from typing import Optional
from server.logger import server_logger


class server_socket_utils:
    """Utility class for server socket operations with logging."""

    @staticmethod
    def send_packet_with_logging(
        client_socket: socket.socket,
        packet_data: bytes,
        player_index: int,
        logger: server_logger,
        success_message: str,
        error_context: str = "packet send",
    ) -> bool:
        """
        Send a packet to a client with integrated logging and error handling.

        Args:
            client_socket: The client's socket connection
            packet_data: The packet data to send
            player_index: The player's index for logging
            logger: The logger instance
            success_message: Message to log on successful send
            error_context: Context description for error messages

        Returns:
            True if packet was sent successfully, False otherwise
        """
        try:
            client_socket.send(packet_data)
            logger.debug(success_message)
            return True
        except ConnectionResetError:
            msg = f"Player 0x{player_index:04X} connection reset during {error_context}"
            logger.info(msg)
            return False
        except BrokenPipeError:
            msg = f"Player 0x{player_index:04X} broken pipe during {error_context}"
            logger.info(msg)
            return False
        except socket.error as e:
            msg = f"Socket error sending {error_context} to player 0x{player_index:04X}"
            logger.log_exception(msg, e)
            return False
        except Exception as e:
            msg = f"Unexpected error sending {error_context} to player 0x{player_index:04X}"
            logger.log_exception(msg, e)
            return False

    @staticmethod
    def receive_packet_with_logging(
        client_socket: socket.socket,
        player_index: int,
        logger: server_logger,
        buffer_size: int = 1024,
        timeout: Optional[float] = None,
        error_context: str = "packet receive",
    ) -> Optional[bytes]:
        """
        Receive a packet from a client with integrated logging and error handling.

        Args:
            client_socket: The client's socket connection
            player_index: The player's index for logging
            logger: The logger instance
            buffer_size: Maximum number of bytes to receive
            timeout: Socket timeout in seconds (None for no timeout)
            error_context: Context description for error messages

        Returns:
            Received packet data, or None if error/disconnection occurred
        """
        try:
            if timeout is not None:
                client_socket.settimeout(timeout)

            data = client_socket.recv(buffer_size)

            if not data:
                msg = f"Player 0x{player_index:04X} disconnected during {error_context}"
                logger.info(msg)
                return None

            msg = f"Received from player 0x{player_index:04X}: {data.hex().upper()}"
            logger.debug(msg)
            return data

        except socket.timeout:
            # Timeout is often expected, so we don't log it as an error
            return None
        except ConnectionResetError:
            msg = f"Player 0x{player_index:04X} connection reset during {error_context}"
            logger.info(msg)
            return None
        except socket.error as e:
            msg = (
                f"Socket error during {error_context} from player 0x{player_index:04X}"
            )
            logger.log_exception(msg, e)
            return None
        except Exception as e:
            msg = f"Unexpected error during {error_context} from player 0x{player_index:04X}"
            logger.log_exception(msg, e)
            return None

    @staticmethod
    def send_packet_or_cleanup(
        client_socket: socket.socket,
        packet_data: bytes,
        player_index: int,
        logger: server_logger,
        success_message: str,
        cleanup_callback,
        error_context: str = "packet send",
    ) -> bool:
        """
        Send a packet to a client and cleanup on failure.

        Args:
            client_socket: The client's socket connection
            packet_data: The packet data to send
            player_index: The player's index for logging
            logger: The logger instance
            success_message: Message to log on successful send
            cleanup_callback: Function to call on failure (func <client_socket, player_index>)
            error_context: Context description for error messages

        Returns:
            True if packet was sent successfully, False if failed (cleanup was called)
        """
        success = server_socket_utils.send_packet_with_logging(
            client_socket,
            packet_data,
            player_index,
            logger,
            success_message,
            error_context,
        )

        if not success:
            cleanup_callback(client_socket, player_index)

        return success
