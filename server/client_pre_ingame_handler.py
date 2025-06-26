import socket
import threading
from typing import Callable
from server.logger import ServerLogger
from server.player_manager import PlayerManager
from server.client_state_manager import ClientStateManager, ClientState
from server.utils.socket_utils import ServerSocketUtils
from server.enter_game_world_handler import EnterGameWorldHandler
from server.enter_game_world_pipeline import (
    LoginHandler,
    AuthenticationHandler,
    CharacterDataHandler,
    ServerCredentialsHandler,
)
from data_models.mongodb_models import CharacterDatabase

try:
    from py4godot.classes.Node3D import Node3D
except ImportError:
    Node3D = object


class ClientPreIngameHandler:
    """Handles incoming client connections and manages client communication."""

    def __init__(
        self,
        logger: ServerLogger,
        player_manager: PlayerManager,
        parent_node: Node3D,  # type: ignore
    ):
        self.logger = logger
        self.player_manager = player_manager
        self.parent_node = parent_node
        self.state_manager = ClientStateManager(logger)
        self.character_db = CharacterDatabase()

        self.server_credentials_handler = ServerCredentialsHandler()
        self.login_handler = LoginHandler()
        self.auth_handler = AuthenticationHandler()
        self.character_data_handler = CharacterDataHandler(self.character_db)
        self.enter_game_world_handler = EnterGameWorldHandler(self.character_db)

        self._client_threads = {}
        self._threads_lock = threading.Lock()

    def start_handling(
        self, server_socket: socket.socket, is_running: Callable[[], bool]
    ) -> None:
        """
        Start handling incoming client connections.
        This runs on the main server thread.

        Args:
            server_socket: The server's listening socket
            is_running: A callable that returns whether the server is still running
        """
        self.logger.info("Client handler started - waiting for connections")

        while is_running():
            try:
                client_socket, address = server_socket.accept()
                client_thread = threading.Thread(
                    target=self._handle_new_client,
                    args=(client_socket, address, is_running),
                    daemon=True,
                )
                client_thread.start()

                with self._threads_lock:
                    self._client_threads[client_thread.ident] = {
                        "thread": client_thread,
                        "address": address,
                        "player_index": None,
                    }

            except socket.timeout:
                continue
            except Exception as e:
                if is_running():
                    self.logger.log_exception("Error accepting client connection", e)

    def _handle_new_client(
        self,
        client_socket: socket.socket,
        address: tuple,
        is_running: Callable[[], bool],
    ) -> None:
        """
        Handle a new client connection through the full pipeline.
        This runs on the client's dedicated thread.

        Args:
            client_socket: The client's socket connection
            address: The client's address
            is_running: A callable that returns whether the server is still running
        """
        player_index = None
        try:
            player_index = self.player_manager.get_next_available_index()
            if player_index is None:
                msg = f"No available player slots for {address}"
                self.logger.warning(msg)
                client_socket.close()
                return

            with self._threads_lock:
                thread_id = threading.current_thread().ident
                if thread_id in self._client_threads:
                    self._client_threads[thread_id]["player_index"] = player_index

            self.player_manager.reserve_index(player_index)
            self.state_manager.add_client(player_index)

            msg = f"New client {address} assigned to player index 0x{player_index:04X}"
            self.logger.info(msg)

            self.state_manager.transition_state(
                player_index, ClientState.INIT_READY_FOR_INITIAL_DATA
            )

            ServerCredentialsHandler.send_init_and_credentials(
                client_socket,
                player_index,
                self.logger,
            )

            self.state_manager.transition_state(
                player_index, ClientState.INIT_WAITING_FOR_LOGIN_DATA
            )

            login_packet = self.login_handler.wait_for_login_packet(
                client_socket, player_index, self.logger
            )

            self.auth_handler.process_authentication(
                login_packet,
                player_index,
                client_socket,
                self.logger,
                self.state_manager,
            )

            user_id = self.state_manager.get_user_id(player_index)
            self.character_data_handler.send_character_select_and_data(
                player_index,
                user_id,
                client_socket,
                self.logger,
            )

            self.enter_game_world_handler.handle_enter_game_world(
                client_socket,
                player_index,
                user_id,
                self.logger,
                self.state_manager,
            )

            # Handle ingame ack and world entry
            self.enter_game_world_handler.handle_ingame_ack_and_world_entry(
                client_socket,
                player_index,
                self.logger,
                self.state_manager,
            )

            # Start ongoing client communication loop
            msg = f"Started communication loop for player 0x{player_index:04X}"
            self.logger.debug(msg)

            while is_running():
                try:
                    data = ServerSocketUtils.receive_packet_with_logging(
                        client_socket,
                        player_index,
                        self.logger,
                        1024,
                        10.0,
                        "client communication",
                    )

                    if not data:
                        break

                    # TODO: Handle ongoing game packets here
                    # For now, just log the received data
                    msg = (
                        f"Player 0x{player_index:04X} sent packet: "
                        f"{data.hex().upper()}"
                    )
                    self.logger.debug(msg)

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
            msg = f"Error in client thread for {address}"
            if player_index is not None:
                msg += f" (player 0x{player_index:04X})"
            self.logger.log_exception(msg, e)
        finally:
            if player_index is not None:
                self._cleanup_client(client_socket, player_index)

    def _cleanup_client(self, client_socket: socket.socket, player_index: int) -> None:
        """
        Clean up all resources associated with a client.
        This runs on the client's dedicated thread.

        Args:
            client_socket: The client's socket connection
            player_index: The player's index to clean up
        """
        try:
            # Close the socket
            client_socket.close()
        except Exception:
            pass

        # Clean up player manager
        if player_index is not None:
            self.player_manager.release_index(player_index)

        # Clean up state manager
        if player_index is not None:
            self.state_manager.cleanup_client(player_index)

        # Remove from thread tracking
        with self._threads_lock:
            thread_id = threading.current_thread().ident
            if thread_id in self._client_threads:
                del self._client_threads[thread_id]

        if player_index is not None:
            msg = f"Cleaned up resources for player 0x{player_index:04X}"
            self.logger.debug(msg)

    def get_client_node(self, player_index: int) -> Node3D:  # type: ignore
        """
        Get the client node for a specific player.

        Args:
            player_index: The player's index

        Returns:
            Node3D: The client's node
        """
        # This would be implemented based on the specific game engine requirements
        return self.parent_node

    def get_active_client_count(self) -> int:
        """
        Get the number of currently active clients.

        Returns:
            int: The number of active clients
        """
        with self._threads_lock:
            return len(
                [t for t in self._client_threads.values() if t["thread"].is_alive()]
            )

    def get_client_thread_info(self) -> dict:
        """
        Get information about all client threads.

        Returns:
            dict: Thread information for debugging
        """
        with self._threads_lock:
            return {
                tid: {
                    "address": info["address"],
                    "player_index": info["player_index"],
                    "is_alive": info["thread"].is_alive(),
                }
                for tid, info in self._client_threads.items()
            }

    def stop_handling(self) -> None:
        """
        Stop handling clients and clean up all resources.
        This should be called when shutting down the server.
        """
        self.logger.info("Stopping client handler...")

        # Close all client connections
        with self._threads_lock:
            for thread_info in self._client_threads.values():
                try:
                    # Force close the thread (not graceful, but necessary for shutdown)
                    thread_info["thread"].join(timeout=1.0)
                except Exception as e:
                    self.logger.log_exception("Error stopping client thread", e)

            self._client_threads.clear()

        # Clean up state manager
        self.state_manager.cleanup_all_clients()

        # Clean up player manager
        self.player_manager.release_all_indices()

        self.logger.info("Client handler stopped")
