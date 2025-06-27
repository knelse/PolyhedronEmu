import socket
import time
from server.logger import server_logger
from server.packets import server_packets
from server.utils.socket_utils import server_socket_utils
from .exceptions import server_credentials_exception


class server_credentials_handler:
    """Handles sending server credentials to clients."""

    @staticmethod
    def send_init_and_credentials(
        client_socket: socket.socket,
        player_index: int,
        logger: server_logger,
    ) -> None:
        """
        Send init packet and server credentials to the client.

        Args:
            client_socket: The client's socket connection
            player_index: The player's index for logging
            logger: The server logger instance

        Raises:
            server_credentials_exception: If sending packets fails
        """
        # Send init packet
        send_packet_success = server_socket_utils.send_packet_or_cleanup(
            client_socket,
            server_packets.INIT_PACKET,
            player_index,
            logger,
            f"Sent init packet to player 0x{player_index:04X}: "
            f"{server_packets.INIT_PACKET.hex().upper()}",
            None,  # No cleanup callback needed since we'll throw exception
            "init packet",
        )
        if not send_packet_success:
            raise server_credentials_exception(
                f"Failed to send init packet to player 0x{player_index:04X}"
            )

        # Send credentials packet
        credentials_packet = server_packets.get_server_credentials(player_index)
        time.sleep(0.2)
        send_packet_success = server_socket_utils.send_packet_or_cleanup(
            client_socket,
            credentials_packet,
            player_index,
            logger,
            f"Sent credentials to player 0x{player_index:04X}: "
            f"{credentials_packet.hex().upper()}",
            None,  # No cleanup callback needed since we'll throw exception
            "credentials packet",
        )
        if not send_packet_success:
            raise server_credentials_exception(
                f"Failed to send credentials packet to player 0x{player_index:04X}"
            )
