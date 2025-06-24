import socket
import threading
import time
from typing import Callable
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
from server.auth_pipeline import auth_pipeline
from data_models.mongodb_models import CharacterDatabase


class ClientHandler:
    def __init__(
        self, logger: ServerLogger, player_manager: PlayerManager, parent_node: Node3D
    ):
        self.logger = logger
        self.player_manager = player_manager
        self.parent_node = parent_node
        self.state_manager = ClientStateManager(logger)
        self.character_db = CharacterDatabase()
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

            state_change_success = self.state_manager.transition_state(
                player_index, ClientState.INIT_READY_FOR_INITIAL_DATA
            )
            if not state_change_success:
                self._cleanup_client(client_socket, player_index)
                return

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

                # Authenticate or register user
                auth_result = auth_pipeline.authenticate_or_register(
                    decrypted_login, decrypted_password
                )

                if not auth_result.success:
                    msg = (
                        f"Authentication failed for player 0x{player_index:04X}: "
                        f"{auth_result.message}"
                    )
                    self.logger.warning(msg)

                    # Send connection error packet and close connection for any failure
                    failure_packet = auth_pipeline.get_authentication_failure_packet(
                        player_index
                    )
                    SocketUtils.send(
                        client_socket,
                        failure_packet,
                        player_index,
                        self.logger,
                        f"Sent connection error to player 0x{player_index:04X}: "
                        f"{failure_packet.hex().upper()}",
                    )
                    # Close connection immediately for any authentication failure
                    try:
                        client_socket.close()
                    except Exception:
                        pass
                    self._cleanup_client(client_socket, player_index)
                    return

                # Log successful authentication
                if auth_result.is_new_user:
                    msg = (
                        f"New user registered and authenticated: {auth_result.user.login} "
                        f"(player 0x{player_index:04X})"
                    )
                else:
                    msg = (
                        f"User authenticated: {auth_result.user.login} "
                        f"(player 0x{player_index:04X}, login #{auth_result.user.login_count})"
                    )
                self.logger.info(msg)

                # Store user_id for later use
                self.state_manager.set_user_id(player_index, auth_result.user.login)

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
            char_data_packet = self._create_triple_character_data(
                player_index, auth_result.user.login
            )
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

            character_screen_result = self._wait_for_character_screen(
                client_socket, player_index
            )
            if character_screen_result is None:
                return

            # If character_screen_result is not None, it contains the slot index
            if character_screen_result is not False:
                # Character creation succeeded, send enter game data and transition state
                self.send_enter_game_data(
                    character_screen_result, player_index, client_socket
                )

                state_change_success = self.state_manager.transition_state(
                    player_index, ClientState.INIT_WAITING_FOR_CLIENT_INGAME_ACK
                )
                if not state_change_success:
                    self._cleanup_client(client_socket, player_index)
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

    def _wait_for_character_screen(
        self, client_socket: socket.socket, player_index: int
    ):
        """
        Wait for client to interact with the character screen (select or delete character).

        Args:
            client_socket: The client's socket connection
            player_index: The player's index for logging

        Returns:
            int: character slot index if character creation succeeded
            False: for character selection or deletion (connection will be closed)
            None: for errors or disconnection
        """
        try:
            client_socket.settimeout(86400.0)  # we can wait

            while True:
                data = client_socket.recv(1024)
                if not data:
                    self.logger.warning(
                        f"Player 0x{player_index:04X} disconnected during character screen"
                    )
                    self._cleanup_client(client_socket, player_index)
                    return None

                msg = f"Received packet from player 0x{player_index:04X}: {data.hex().upper()}"
                self.logger.debug(msg)

                if len(data) > 0 and data[0] == 0x2A:
                    self.logger.debug("Requested character delete")
                    if len(data) >= 18:
                        character_slot_index = data[17] // 4 - 1
                        user_id = self.state_manager.get_user_id(player_index)
                        if user_id:
                            success = self.character_db.delete_character_by_user_index(
                                user_id, character_slot_index
                            )
                            if success:
                                msg = (
                                    f"Player 0x{player_index:04X} deleted character "
                                    f"at slot {character_slot_index}"
                                )
                                self.logger.info(msg)
                            else:
                                msg = (
                                    f"Player 0x{player_index:04X} failed to delete "
                                    f"character at slot {character_slot_index}"
                                )
                                self.logger.warning(msg)
                        else:
                            msg = (
                                f"Player 0x{player_index:04X} attempted character "
                                f"delete but no user_id found"
                            )
                            self.logger.warning(msg)
                    else:
                        msg = (
                            f"Player 0x{player_index:04X} sent character delete "
                            f"packet too short: {len(data)} bytes"
                        )
                        self.logger.warning(msg)
                    self._cleanup_client(client_socket, player_index)
                    return False

                if len(data) >= 18 and data[0] == 0x15:
                    character_slot_index = data[17] // 4 - 1
                    user_id = self.state_manager.get_user_id(player_index)
                    if user_id:
                        # Check if character exists in database
                        character_data = self.character_db.characters.find_one(
                            {
                                "user_id": user_id,
                                "character_slot_index": character_slot_index,
                                "is_not_queued_for_deletion": True,
                            }
                        )

                        if character_data:
                            msg = (
                                f"Player 0x{player_index:04X} selected character "
                                f"at slot {character_slot_index}"
                            )
                            self.logger.info(msg)

                            # Send enter game world data and close connection
                            self.send_enter_game_world_data(
                                character_slot_index, user_id
                            )
                            self._cleanup_client(client_socket, player_index)
                            return False
                        else:
                            msg = (
                                f"Player 0x{player_index:04X} tried to select "
                                f"non-existent character at slot {character_slot_index}"
                            )
                            self.logger.warning(msg)
                    else:
                        msg = (
                            f"Player 0x{player_index:04X} attempted character "
                            f"selection but no user_id found"
                        )
                        self.logger.warning(msg)
                    continue

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

                # Character creation packet detected
                user_id = self.state_manager.get_user_id(player_index)
                if user_id:
                    character_slot_index = data[17] // 4 - 1
                    creation_result = self._create_character_from_packet(
                        data, user_id, character_slot_index, player_index
                    )

                    if creation_result:
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
                            return None

                        msg = f"Character creation completed for player 0x{player_index:04X}"
                        self.logger.info(msg)
                        return character_slot_index
                    else:
                        # Name already exists or other error
                        name_taken_packet = ServerPackets.character_name_already_taken(
                            player_index
                        )
                        send_packet_success = SocketUtils.send(
                            client_socket,
                            name_taken_packet,
                            player_index,
                            self.logger,
                            f"Sent character name already taken to player "
                            f"0x{player_index:04X}: {name_taken_packet.hex().upper()}",
                        )
                        if not send_packet_success:
                            self._cleanup_client(client_socket, player_index)
                            return None

                        msg = (
                            f"Character creation failed for player 0x{player_index:04X} - "
                            f"name already exists"
                        )
                        self.logger.warning(msg)

                        # Close connection after sending the packet
                        self._cleanup_client(client_socket, player_index)
                        return None
                else:
                    msg = (
                        f"Player 0x{player_index:04X} attempted character "
                        f"creation but no user_id found"
                    )
                    self.logger.warning(msg)
                    continue

        except socket.timeout:
            self.logger.warning(
                f"Timeout waiting for character screen interaction from player 0x{player_index:04X}"
            )
            self._cleanup_client(client_socket, player_index)
            return None
        except Exception as e:
            msg = f"Error waiting for character screen interaction from player 0x{player_index:04X}"
            self.logger.log_exception(msg, e)
            self._cleanup_client(client_socket, player_index)
            return None

    def _create_triple_character_data(self, player_index: int, user_id: str) -> bytes:
        """
        Create a packet containing 3 character data entries back-to-back.
        Uses actual characters from database, filling with defaults if needed.

        Args:
            player_index: The player's index
            user_id: The user's login ID to fetch characters for

        Returns:
            Combined packet data
        """
        # Fetch user's characters from database
        user_characters = self.character_db.get_characters_by_user(user_id)

        # Create 3 characters (mix of user's actual characters and defaults)
        characters = []
        char_data_packets = []

        # Use actual characters up to 3, then fill with defaults
        for i in range(3):
            if i < len(user_characters):
                # Convert MongoDB character to ClientCharacter
                character = user_characters[i].to_client_character()
                character.player_index = player_index
                characters.append(character)
                char_data = character.to_character_list_bytearray()
                char_data_packets.append(char_data)
            else:
                char_data_packets.append(
                    ServerPackets.get_new_character_data(player_index)
                )

        # Combine all three packets without separators
        combined_packet = b"".join(char_data_packets)

        msg = (
            f"Created triple character data for user {user_id} "
            f"(player 0x{player_index:04X}): {len(user_characters)} actual characters, "
            f"{3 - len(user_characters)} default characters, "
            f"total length: {len(combined_packet)} bytes"
        )
        self.logger.debug(msg)

        return combined_packet

    def send_enter_game_world_data(
        self, character_slot_index: int, user_id: str
    ) -> None:
        """
        Send enter game world data for the selected character.
        For now, this method just logs the action and closes the connection.

        Args:
            character_slot_index: The character slot index that was selected
            user_id: The user's login ID
        """
        msg = (
            f"Entering game world with character at slot {character_slot_index} "
            f"for user {user_id}"
        )
        self.logger.info(msg)

        # TODO: Implement game world entry logic here
        # For now, just log and let the calling method handle connection closure

    def send_enter_game_data(
        self,
        character_slot_index: int,
        player_index: int,
        client_socket: socket.socket,
    ) -> None:
        """
        Send enter game data for a newly created character.
        This is called after successful character creation.

        Args:
            character_slot_index: The character slot index that was created
            player_index: The player's index for logging
            client_socket: The client's socket connection
        """
        try:
            # Get the user_id from state manager
            user_id = self.state_manager.get_user_id(player_index)
            if not user_id:
                msg = (
                    f"Cannot send enter game data for player 0x{player_index:04X} - "
                    f"no user_id found"
                )
                self.logger.error(msg)
                return

            # Retrieve the newly created character from database
            character_data = self.character_db.characters.find_one(
                {
                    "user_id": user_id,
                    "character_slot_index": character_slot_index,
                    "is_not_queued_for_deletion": True,
                }
            )

            if not character_data:
                msg = (
                    f"Cannot send enter game data for player 0x{player_index:04X} - "
                    f"character not found at slot {character_slot_index}"
                )
                self.logger.error(msg)
                return

            # Convert MongoDB character to ClientCharacter
            from data_models.mongodb_models import ClientCharacterMongo

            character_mongo = ClientCharacterMongo.from_dict(character_data)
            character = character_mongo.to_client_character()

            # Set the correct player index
            character.player_index = player_index

            # Generate the game data bytearray
            game_data = character.to_game_data_bytearray()

            # Send the game data to the client
            from utils.socket_utils import SocketUtils

            send_success = SocketUtils.send(
                client_socket,
                game_data,
                player_index,
                self.logger,
                f"Sent enter game data to player 0x{player_index:04X}: "
                f"{len(game_data)} bytes",
            )

            if send_success:
                msg = (
                    f"Successfully sent enter game data for character '{character.name}' "
                    f"at slot {character_slot_index} to player 0x{player_index:04X} "
                    f"({len(game_data)} bytes)"
                )
                self.logger.info(msg)
            else:
                msg = f"Failed to send enter game data for player 0x{player_index:04X}"
                self.logger.error(msg)

        except Exception as e:
            msg = f"Error sending enter game data for player 0x{player_index:04X}"
            self.logger.log_exception(msg, e)

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

    def _create_character_from_packet(
        self, data, user_id, character_slot_index, player_index
    ):
        """
        Create a new character from the received packet data.

        Args:
            data: The packet data bytes
            user_id: The user's ID
            character_slot_index: The character slot index (0-3)
            player_index: The player index for logging

        Returns:
            bool: True if character was created successfully, False otherwise
        """
        try:
            # Decode character name from packet
            name = self._decode_character_name(data)

            # Check if name is valid (not already taken)
            if self.character_db.character_name_exists(name):
                msg = (
                    f"Player 0x{player_index:04X} tried to create character "
                    f"with existing name: {name}"
                )
                self.logger.warning(msg)
                return False

            # Extract character appearance data
            char_data_bytes_start = data[0] - 5
            char_data_bytes = data[
                char_data_bytes_start : char_data_bytes_start + data[0]
            ]

            # Parse appearance data
            is_gender_female = (char_data_bytes[1] >> 4) % 2 == 1
            face_type = ((char_data_bytes[1] & 0b111111) << 2) + (
                char_data_bytes[0] >> 6
            )
            hair_style = ((char_data_bytes[2] & 0b111111) << 2) + (
                char_data_bytes[1] >> 6
            )
            hair_color = ((char_data_bytes[3] & 0b111111) << 2) + (
                char_data_bytes[2] >> 6
            )
            tattoo = ((char_data_bytes[4] & 0b111111) << 2) + (char_data_bytes[3] >> 6)

            # Apply female adjustments
            if is_gender_female:
                face_type = 256 - face_type
                hair_style = 255 - hair_style
                hair_color = 255 - hair_color
                tattoo = 255 - tattoo

            # Create character data
            character_data = {
                "user_id": user_id,
                "character_slot_index": character_slot_index,
                "name": name,
                "is_gender_female": is_gender_female,
                "face_type": face_type,
                "hair_style": hair_style,
                "hair_color": hair_color,
                "tattoo": tattoo,
            }

            # Save character to database
            character_id = self.character_db.create_character(character_data)

            if character_id:
                msg = (
                    f"Player 0x{player_index:04X} created character '{name}' "
                    f"in slot {character_slot_index} with ID {character_id}"
                )
                self.logger.info(msg)
                return True
            else:
                msg = f"Player 0x{player_index:04X} failed to save character '{name}' to database"
                self.logger.error(msg)
                return False

        except Exception as e:
            msg = f"Error creating character for player 0x{player_index:04X}: {e}"
            self.logger.error(msg)
            return False

    def _decode_character_name(self, data):
        """
        Decode character name from packet data using the game's encoding scheme.

        Args:
            data: The packet data bytes

        Returns:
            str: The decoded character name
        """
        length = data[0] - 20 - 5
        name_check_bytes = data[20:]

        name_chars = []
        first_letter_char_code = ((name_check_bytes[1] & 0b11111) << 3) + (
            name_check_bytes[0] >> 5
        )
        first_letter_should_be_russian = False

        # Decode characters starting from index 1
        for i in range(1, length):
            current_char_code = ((name_check_bytes[i] & 0b11111) << 3) + (
                name_check_bytes[i - 1] >> 5
            )

            if current_char_code % 2 == 0:
                # English character
                current_letter = chr(current_char_code // 2)
                name_chars.append(current_letter)
            else:
                # Russian character
                if current_char_code >= 193:
                    current_letter = chr((current_char_code - 192) // 2 + ord("а"))
                else:
                    current_letter = chr((current_char_code - 129) // 2 + ord("А"))
                name_chars.append(current_letter)

                if i == 2:
                    # Assume first letter was Russian if second letter is
                    first_letter_should_be_russian = True

        # Handle first letter
        if first_letter_should_be_russian:
            first_letter_char_code += 1
            if first_letter_char_code >= 193:
                first_letter = chr((first_letter_char_code - 192) // 2 + ord("а"))
            else:
                first_letter = chr((first_letter_char_code - 129) // 2 + ord("А"))
            name = (
                first_letter + "".join(name_chars[1:])
                if len(name_chars) > 1
                else first_letter
            )
        else:
            first_letter = chr(first_letter_char_code // 2)
            name = (
                first_letter + "".join(name_chars[1:])
                if len(name_chars) > 1
                else first_letter
            )

        return name
