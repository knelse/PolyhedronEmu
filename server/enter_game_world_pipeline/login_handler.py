import socket
from server.logger import server_logger
from server.utils.socket_utils import server_socket_utils
from .exceptions import login_exception


class login_handler:
    """Handles waiting for and processing login packets from clients."""

    @staticmethod
    def wait_for_login_packet(
        client_socket: socket.socket, player_index: int, logger: server_logger
    ) -> bytes:
        """
        Wait for client to send a login packet longer than 12 bytes.

        Args:
            client_socket: The client's socket connection
            player_index: The player's index for logging
            logger: The server logger instance

        Returns:
            The received packet data

        Raises:
            login_exception: If login packet reception fails
        """
        try:
            while True:
                data = server_socket_utils.receive_packet_with_logging(
                    client_socket,
                    player_index,
                    logger,
                    1024,
                    86400.0,
                    "login packet wait",
                )
                if not data:
                    raise login_exception(
                        f"Failed to receive login packet from player 0x{player_index:04X}"
                    )

                if len(data) > 12:
                    msg = (
                        f"Login packet accepted for player 0x{player_index:04X}, "
                        f"length: {len(data)}"
                    )
                    logger.info(msg)
                    return data

        except socket.timeout:
            raise login_exception(
                f"Timeout waiting for login packet from player 0x{player_index:04X}"
            )
        except login_exception:
            raise
        except Exception as e:
            raise login_exception(
                f"Error waiting for login packet from player 0x{player_index:04X}: {str(e)}"
            )
