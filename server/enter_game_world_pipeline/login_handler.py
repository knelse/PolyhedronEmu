import socket
from server.logger import ServerLogger
from server.utils.socket_utils import ServerSocketUtils
from .exceptions import LoginException


class LoginHandler:
    """Handles waiting for and processing login packets from clients."""

    @staticmethod
    def wait_for_login_packet(
        client_socket: socket.socket, player_index: int, logger: ServerLogger
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
            LoginException: If login packet reception fails
        """
        try:
            while True:
                data = ServerSocketUtils.receive_packet_with_logging(
                    client_socket,
                    player_index,
                    logger,
                    1024,
                    86400.0,
                    "login packet wait",
                )
                if not data:
                    raise LoginException(
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
            raise LoginException(
                f"Timeout waiting for login packet from player 0x{player_index:04X}"
            )
        except LoginException:
            raise
        except Exception as e:
            raise LoginException(
                f"Error waiting for login packet from player 0x{player_index:04X}: {str(e)}"
            )
