import socket
from server.logger import server_logger
from server.client_state_manager import client_state_manager
from server.utils.login_utils import (
    get_encrypted_login_and_password,
    decrypt_login_and_password,
)
from server.utils.socket_utils import server_socket_utils
from server.auth_pipeline import auth_pipeline
from .exceptions import authentication_exception


class authentication_handler:
    """Handles user authentication and registration."""

    @staticmethod
    def process_authentication(
        login_packet: bytes,
        player_index: int,
        client_socket: socket.socket,
        logger: server_logger,
        state_manager: client_state_manager,
    ) -> None:
        """
        Process user authentication from login packet.

        Args:
                login_packet: The received login packet data
                player_index: The player's index
                client_socket: The client's socket connection
                logger: The server logger instance
                state_manager: The client state manager

        Raises:
                authentication_exception: If authentication fails
        """
        try:
            login_bytes, password_bytes = get_encrypted_login_and_password(login_packet)
            decrypted_login, decrypted_password = decrypt_login_and_password(
                login_bytes, password_bytes
            )
            msg = (
                f"Player 0x{player_index:04X} login attempt: "
                f"login_length={len(login_bytes)}, password_length={len(password_bytes)}, "
                f"login={decrypted_login}, password={decrypted_password}"
            )
            logger.info(msg)

            # Authenticate or register user
            auth_result = auth_pipeline.authenticate_or_register(
                decrypted_login, decrypted_password
            )

            if not auth_result.success:
                # Send connection error packet and close connection for any failure
                failure_packet = auth_pipeline.get_authentication_failure_packet(
                    player_index
                )
                server_socket_utils.send_packet_with_logging(
                    client_socket,
                    failure_packet,
                    player_index,
                    logger,
                    f"Sent connection error to player 0x{player_index:04X}: "
                    f"{failure_packet.hex().upper()}",
                    "authentication failure packet",
                )
                # Close connection immediately for any authentication failure
                try:
                    client_socket.close()
                except Exception:
                    pass

                raise authentication_exception(
                    f"Authentication failed for player 0x{player_index:04X}: {auth_result.message}"
                )

            # Log successful authentication
            if auth_result.is_new_polyhedron_user:
                msg = (
                    f"New user registered and authenticated: {auth_result.user.login} "
                    f"(player 0x{player_index:04X})"
                )
            else:
                msg = (
                    f"user authenticated: {auth_result.user.login} "
                    f"(player 0x{player_index:04X}, login #{auth_result.user.login_count})"
                )
            logger.info(msg)

            # Store user_id for later use
            state_manager.set_user_id(player_index, auth_result.user.login)

        except authentication_exception:
            raise
        except Exception as e:
            raise authentication_exception(
                f"Failed to decode login data for player 0x{player_index:04X}: {str(e)}"
            )
