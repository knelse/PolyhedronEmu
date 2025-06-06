import socket
import threading
import time
from typing import Callable
from data_models.client_character import ClientCharacter
from py4godot.classes.Node3D import Node3D
from server.logger import ServerLogger
from server.player_manager import PlayerManager
from server.client_state_manager import ClientStateManager, ClientState
from server.packets import INIT_PACKET, ServerPackets
from utils.login_utils import (
    get_encrypted_login_and_password,
    decrypt_login_and_password,
)
from utils.socket_utils import SocketUtils


class ClientHandler:
    def __init__(
        self, logger: ServerLogger, player_manager: PlayerManager, parent_node: Node3D
    ):
        self.logger = logger
        self.player_manager = player_manager
        self.parent_node = parent_node
        self.state_manager = ClientStateManager(logger)
        self.is_running = False
        self.client_nodes = {}  # player_index -> Node3D
        self.nodes_lock = threading.Lock()
        self.client_threads = {}  # player_index -> threading.Thread
        self.threads_lock = threading.Lock()

    def start_handling(
        self, server_socket: socket.socket, is_running: Callable[[], bool]
    ) -> None:
        """
        Start handling connections on the given server socket.
        Spawns a new thread for each client connection immediately.

        Args:
            server_socket: The server socket to accept connections from
            is_running: A callable that returns whether the server is
                       still running
        """
        self.is_running = True
        while is_running():
            try:
                client_socket, address = server_socket.accept()
                client_thread = threading.Thread(
                    target=self._handle_new_client,
                    args=(client_socket, address, is_running),
                    name=f"Client-{address[0]}:{address[1]}",
                )
                client_thread.daemon = True
                client_thread.start()

                msg = f"Spawned new thread for connection from {address}"
                self.logger.debug(msg)

            except Exception as e:
                if self.is_running:
                    self.logger.log_exception("Error accepting connection", e)
                break

    def _handle_new_client(
        self,
        client_socket: socket.socket,
        address: tuple,
        is_running: Callable[[], bool],
    ) -> None:
        """
        Handle all operations for a new client connection on a dedicated thread.
        This includes initial setup, player assignment, packet sending, and ongoing communication.

        Args:
            client_socket: The client's socket connection
            address: The client's address
            is_running: A callable that returns whether the server is still running
        """
        player_index = None
        try:
            player_index = self.player_manager.get_next_player_index()
            if player_index is None:
                msg = (
                    f"Rejecting connection from {address}: " f"Maximum players reached"
                )
                self.logger.warning(msg)
                client_socket.close()
                return

            client_node = Node3D()
            client_node.set_name(f"Player_{player_index:04X}")

            with self.nodes_lock:
                self.parent_node.call_deferred("add_child", client_node)
                self.client_nodes[player_index] = client_node

            self.player_manager.add_player(player_index, address)
            self.state_manager.add_client(player_index)

            with self.threads_lock:
                self.client_threads[player_index] = threading.current_thread()

            msg = (
                f"New connection from {address} assigned player "
                f"index: 0x{player_index:04X}, created node: "
                f"{client_node.get_name()}"
            )
            self.logger.info(msg)

            send_packet_success = SocketUtils.send(
                client_socket,
                INIT_PACKET,
                player_index,
                self.logger,
                f"Sent init packet to player 0x{player_index:04X}: {INIT_PACKET.hex().upper()}",
            )
            if not send_packet_success:
                self._cleanup_client(client_socket, player_index)
                return

            credentials_packet = ServerPackets.get_server_credentials(player_index)
            time.sleep(0.2)
            send_packet_success = SocketUtils.send(
                client_socket,
                credentials_packet,
                player_index,
                self.logger,
                f"Sent credentials to player 0x{player_index:04X}: "
                f"{credentials_packet.hex().upper()}",
            )
            if not send_packet_success:
                self._cleanup_client(client_socket, player_index)
                return

            state_change_success = self.state_manager.transition_state(
                player_index, ClientState.INIT_WAITING_FOR_LOGIN_DATA
            )
            if not state_change_success:
                self._cleanup_client(client_socket, player_index)
                return

            login_packet = self._wait_for_login_packet(client_socket, player_index)
            if login_packet is None:
                msg = f"Failed to receive login packet from player 0x{player_index:04X}"
                self.logger.warning(msg)
                self._cleanup_client(client_socket, player_index)
                return

            try:
                login_bytes, password_bytes = get_encrypted_login_and_password(
                    login_packet
                )
                decrypted_login, decrypted_password = decrypt_login_and_password(
                    login_bytes, password_bytes
                )
                msg = (
                    f"Player 0x{player_index:04X} login attempt: "
                    f"login_length={len(login_bytes)}, password_length={len(password_bytes)}, "
                    f"login={decrypted_login}, password={decrypted_password}"
                )
                self.logger.info(msg)
            except Exception as e:
                msg = f"Failed to decode login data for player 0x{player_index:04X}"
                self.logger.log_exception(msg, e)
                self._cleanup_client(client_socket, player_index)
                return

            time.sleep(0.05)
            char_select_packet = ServerPackets.get_character_select_start_data(
                player_index
            )
            send_packet_success = SocketUtils.send(
                client_socket,
                char_select_packet,
                player_index,
                self.logger,
                f"Sent character select start to player "
                f"0x{player_index:04X}: {char_select_packet.hex().upper()}",
            )
            if not send_packet_success:
                self._cleanup_client(client_socket, player_index)
                return

            # Send 3x new character data back-to-back
            time.sleep(0.1)
            char_data_packet = self._create_triple_character_data(player_index)
            send_packet_success = SocketUtils.send(
                client_socket,
                char_data_packet,
                player_index,
                self.logger,
                f"Sent triple character data to player "
                f"0x{player_index:04X}: {char_data_packet.hex().upper()}",
            )
            if not send_packet_success:
                self._cleanup_client(client_socket, player_index)
                return

            state_change_success = self.state_manager.transition_state(
                player_index, ClientState.INIT_WAITING_FOR_CHARACTER_SELECT
            )
            if not state_change_success:
                self._cleanup_client(client_socket, player_index)
                return

            character_selected = self._wait_for_character_selection(
                client_socket, player_index
            )
            if not character_selected:
                return

            self._handle_client_communication(
                client_socket, address, player_index, is_running
            )

        except Exception as e:
            msg = f"Error in client thread for {address}"
            if player_index is not None:
                msg += f" (player 0x{player_index:04X})"
            self.logger.log_exception(msg, e)
            if player_index is not None:
                self._cleanup_client(client_socket, player_index)

    def _handle_client_communication(
        self,
        client_socket: socket.socket,
        address: tuple,
        player_index: int,
        is_running: Callable[[], bool],
    ) -> None:
        """
        Handle ongoing communication with a specific client.
        This runs on the client's dedicated thread.

        Args:
            client_socket: The client's socket connection
            address: The client's address
            player_index: The assigned player index
            is_running: A callable that returns whether the server is still running
        """
        try:
            msg = f"Started communication loop for player 0x{player_index:04X}"
            self.logger.debug(msg)

            while is_running():
                try:
                    client_socket.settimeout(10.0)
                    data = client_socket.recv(1024)

                    if not data:
                        msg = f"Player 0x{player_index:04X} ({address}) disconnected"
                        self.logger.info(msg)
                        break

                    msg = f"Received from player 0x{player_index:04X}: {data.hex().upper()}"
                    self.logger.debug(msg)

                    send_packet_success = SocketUtils.send(
                        client_socket,
                        data,
                        player_index,
                        self.logger,
                        f"Echoed data to player 0x{player_index:04X}: {data.hex().upper()}",
                    )
                    if not send_packet_success:
                        break

                except socket.timeout:
                    continue
                except ConnectionResetError:
                    msg = f"Player 0x{player_index:04X} ({address}) connection reset"
                    self.logger.info(msg)
                    break
                except Exception as e:
                    msg = f"Error in communication with player 0x{player_index:04X}"
                    self.logger.log_exception(msg, e)
                    break

        except Exception as e:
            msg = f"Error in communication loop for player 0x{player_index:04X}"
            self.logger.log_exception(msg, e)
        finally:
            self._cleanup_client(client_socket, player_index)

    def _wait_for_login_packet(
        self, client_socket: socket.socket, player_index: int
    ) -> bytes:
        """
        Wait for client to send a login packet longer than 12 bytes.

        Args:
            client_socket: The client's socket connection
            player_index: The player's index for logging

        Returns:
            The received packet data, or None if failed
        """
        try:
            client_socket.settimeout(86400.0)  # we can wait
            while True:
                data = client_socket.recv(1024)
                if not data:
                    self.logger.warning(
                        f"Player 0x{player_index:04X} disconnected during login"
                    )
                    return None

                msg = f"Received packet from player 0x{player_index:04X}: {data.hex().upper()}"
                self.logger.debug(msg)

                if len(data) > 12:
                    msg = (
                        f"Login packet accepted for player 0x{player_index:04X}, "
                        f"length: {len(data)}"
                    )
                    self.logger.info(msg)
                    return data

        except socket.timeout:
            self.logger.warning(
                f"Timeout waiting for login packet from player 0x{player_index:04X}"
            )
            return None
        except Exception as e:
            msg = f"Error waiting for login packet from player 0x{player_index:04X}"
            self.logger.log_exception(msg, e)
            return None

    def _wait_for_character_selection(
        self, client_socket: socket.socket, player_index: int
    ) -> bool:
        """
        Wait for client to select a character in the character selection loop.

        Args:
            client_socket: The client's socket connection
            player_index: The player's index for logging

        Returns:
            True if character selection was successful, False if client should be cleaned up
        """
        try:
            client_socket.settimeout(86400.0)  # we can wait

            while True:
                data = client_socket.recv(1024)
                if not data:
                    self.logger.warning(
                        f"Player 0x{player_index:04X} disconnected during character selection"
                    )
                    self._cleanup_client(client_socket, player_index)
                    return False

                msg = f"Received packet from player 0x{player_index:04X}: {data.hex().upper()}"
                self.logger.debug(msg)

                if len(data) > 0 and data[0] == 0x2A:
                    self.logger.debug("Requested character delete")
                    self._cleanup_client(client_socket, player_index)
                    return False

                if len(data) < 17:
                    continue

                if (
                    data[0] < 0x1B
                    or data[13] != 0x08
                    or data[14] != 0x40
                    or data[15] != 0x80
                    or data[16] != 0x05
                ):
                    continue

                success_packet = ServerPackets.character_name_check_success(
                    player_index
                )
                send_packet_success = SocketUtils.send(
                    client_socket,
                    success_packet,
                    player_index,
                    self.logger,
                    f"Sent character name check success to player "
                    f"0x{player_index:04X}: {success_packet.hex().upper()}",
                )
                if not send_packet_success:
                    self._cleanup_client(client_socket, player_index)
                    return False

                msg = f"Character selection completed for player 0x{player_index:04X}"
                self.logger.info(msg)
                return True

        except socket.timeout:
            self.logger.warning(
                f"Timeout waiting for character selection from player 0x{player_index:04X}"
            )
            self._cleanup_client(client_socket, player_index)
            return False
        except Exception as e:
            msg = f"Error waiting for character selection from player 0x{player_index:04X}"
            self.logger.log_exception(msg, e)
            self._cleanup_client(client_socket, player_index)
            return False

    def _create_triple_character_data(self, player_index: int) -> bytes:
        """
        Create a packet containing 3x get_new_character_data back-to-back without separators.

        Args:
            player_index: The player's index

        Returns:
            Combined packet data
        """
        character_1 = ClientCharacter()
        character_1.player_index = player_index
        character_2 = ClientCharacter()
        character_2.player_index = player_index
        character_2.name = "Test2"
        character_3 = ClientCharacter()
        character_3.player_index = player_index
        character_3.name = "Test3"
        char_data1 = (
            character_1.to_character_list_bytearray()
        )  # ServerPackets.get_new_character_data(player_index)
        char_data2 = (
            character_2.to_character_list_bytearray()
        )  # ServerPackets.get_new_character_data(player_index)
        char_data3 = (
            character_3.to_character_list_bytearray()
        )  # ServerPackets.get_new_character_data(player_index)

        # Combine all three packets without separators
        combined_packet = char_data1 + char_data2 + char_data3

        msg = (
            f"Created triple character data for player 0x{player_index:04X}, "
            f"total length: {len(combined_packet)} bytes "
            f"(3x {len(char_data1)} bytes each)"
        )
        self.logger.debug(msg)

        return combined_packet

    def _cleanup_client(self, client_socket: socket.socket, player_index: int) -> None:
        """
        Clean up all resources associated with a client.
        This runs on the client's dedicated thread.

        Args:
            client_socket: The client's socket connection
            player_index: The player's index
        """
        try:
            client_socket.close()
            self.player_manager.remove_player(player_index)
            self.state_manager.remove_client(player_index)

            with self.nodes_lock:
                if player_index in self.client_nodes:
                    client_node = self.client_nodes[player_index]
                    client_node.call_deferred("queue_free")
                    del self.client_nodes[player_index]
                    msg = f"Cleaned up node for player 0x{player_index:04X}"
                    self.logger.debug(msg)

            with self.threads_lock:
                if player_index in self.client_threads:
                    del self.client_threads[player_index]

            msg = f"Connection closed for player 0x{player_index:04X}"
            self.logger.info(msg)

        except Exception as e:
            msg = f"Error cleaning up client 0x{player_index:04X}"
            self.logger.log_exception(msg, e)

    def get_client_node(self, player_index: int) -> Node3D:
        """
        Get the Node3D associated with a specific player.

        Args:
            player_index: The player's index

        Returns:
            The Node3D for the player, or None if not found
        """
        with self.nodes_lock:
            return self.client_nodes.get(player_index)

    def get_active_client_count(self) -> int:
        """
        Get the number of active client threads.

        Returns:
            The number of active client connections
        """
        with self.threads_lock:
            return len(self.client_threads)

    def get_client_thread_info(self) -> dict:
        """
        Get information about all active client threads.

        Returns:
            Dictionary mapping player_index to thread info
        """
        with self.threads_lock:
            return {
                player_index: {
                    "thread_name": thread.name,
                    "is_alive": thread.is_alive(),
                    "ident": thread.ident,
                }
                for player_index, thread in self.client_threads.items()
            }

    def stop_handling(self) -> None:
        """
        Stop handling and clean up all client connections.
        This method signals shutdown and cleans up resources.
        """
        self.is_running = False

        # Clean up all client nodes
        with self.nodes_lock:
            for player_index, client_node in self.client_nodes.items():
                try:
                    client_node.call_deferred("queue_free")
                except Exception as e:
                    msg = f"Error freeing node for player 0x{player_index:04X}"
                    self.logger.log_exception(msg, e)
            self.client_nodes.clear()

        # Wait for threads to complete (with timeout)
        with self.threads_lock:
            threads_to_wait = list(self.client_threads.values())
            self.client_threads.clear()

        for thread in threads_to_wait:
            try:
                thread.join(timeout=2.0)  # Wait up to 2 seconds per thread
            except Exception as e:
                self.logger.debug(f"Error joining thread {thread.name}: {e}")

        self.logger.info("Client handler stopped and all resources cleaned up")

    def wait_for_client_setup(self, player_index: int, timeout: float = 2.0) -> bool:
        """
        Wait for a client to be fully set up (for testing purposes).

        Args:
            player_index: The player index to wait for
            timeout: Maximum time to wait in seconds

        Returns:
            True if client was set up within timeout, False otherwise
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.nodes_lock:
                if player_index in self.client_nodes:
                    # Also check if state manager has the client
                    if self.state_manager.get_client_state(player_index) is not None:
                        return True
            time.sleep(0.1)
        return False
