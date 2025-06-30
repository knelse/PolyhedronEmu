import socket
import threading
import time
from typing import Callable
from server.logger import server_logger
from server.player_manager import player_manager
from server.client_state_manager import client_state_manager, client_state

from server.enter_game_world_handler import enter_game_world_handler
from server.enter_game_world_pipeline import (
    login_handler,
    authentication_handler,
    character_data_handler,
    server_credentials_handler,
)
from data_models.mongodb_models import character_database
from py4godot.utils.smart_cast import register_cast_function
from py4godot.classes.Script import Script

from py4godot.classes.Node3D import Node3D
from py4godot.classes.ResourceLoader import ResourceLoader

register_cast_function("PyScriptExtension", Script.cast)


class client_pre_ingame_handler:
    """Handles incoming client connections and manages client communication."""

    def __init__(
        self,
        logger: server_logger,
        player_manager: player_manager,
        parent_node: Node3D,  # type: ignore
    ):
        self.logger = logger
        self.player_manager = player_manager
        self.parent_node = parent_node
        self.state_manager = client_state_manager(logger)
        self.character_db = character_database()

        self.server_credentials_handler = server_credentials_handler()
        self.login_handler = login_handler()
        self.auth_handler = authentication_handler()
        self.character_data_handler = character_data_handler(self.character_db)
        self.enter_game_world_handler = enter_game_world_handler(self.character_db)

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
            player_index = self.player_manager.get_next_player_index()
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
                player_index, client_state.INIT_READY_FOR_INITIAL_DATA
            )

            self.server_credentials_handler.send_init_and_credentials(
                client_socket,
                player_index,
                self.logger,
            )

            self.state_manager.transition_state(
                player_index, client_state.INIT_WAITING_FOR_LOGIN_DATA
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

            self.enter_game_world_handler.handle_ingame_ack_and_world_entry(
                client_socket,
                player_index,
                self.logger,
                self.state_manager,
            )

            time.sleep(0.05)

            self._create_player_instance_and_transfer_control(
                client_socket,
                player_index,
                user_id,
                is_running,
            )

            # Socket ownership has been transferred to player_ingame_handler
            # Don't close it in cleanup
            client_socket = None

        except Exception as e:
            msg = f"Error in client thread for {address}"
            if player_index is not None:
                msg += f" (player 0x{player_index:04X})"
            self.logger.log_exception(msg, e)
        finally:
            if player_index is not None:
                self._cleanup_client(client_socket, player_index)

    def _create_player_instance_and_transfer_control(
        self,
        client_socket: socket.socket,
        player_index: int,
        user_id: str,
        is_running: Callable[[], bool],
    ) -> None:
        """
        Create a Player scene instance and transfer control to its PlayerIngameHandler.

        Args:
                        client_socket: The client's socket connection
                        player_index: The player's index
                        user_id: The user's ID
                        is_running: A callable that returns whether the server is still running
        """
        try:
            msg = f"Creating Player instance for player 0x{player_index:04X}"
            self.logger.info(msg)

            resource_loader = ResourceLoader.instance()
            player_scene = resource_loader.load("res://Player.tscn")
            player_instance_scene = player_scene.instantiate()
            player_ingame_handler = resource_loader.load(
                "res://server/player/player_ingame_handler.py"
            )

            player_instance_scene.set_script(player_ingame_handler)
            player_instance = player_instance_scene.get_pyscript()

            player_instance.client_socket = client_socket
            player_instance.player_index = player_index
            player_instance.logger = self.logger
            player_instance.state_manager = self.state_manager
            player_instance.user_id = user_id
            player_instance.player_manager = self.player_manager
            player_instance.is_running = is_running

            self.parent_node.call_deferred("add_child", player_instance_scene)

            with self._threads_lock:
                thread_id = threading.current_thread().ident
                if thread_id in self._client_threads:
                    self._client_threads[thread_id]["player_instance"] = player_instance

        except Exception as e:
            msg = f"Failed to create Player instance for player 0x{player_index:04X}"
            self.logger.log_exception(msg, e)
            # Clean up on failure
            if "player_instance" in locals() and player_instance:
                try:
                    self.parent_node.call_deferred("remove_child", player_instance)
                    player_instance.queue_free()
                except Exception:
                    pass
            raise

    def _cleanup_client(
        self,
        client_socket: socket.socket | None,
        player_index: int,
    ) -> None:
        """
        Clean up all resources associated with a client.
        This runs on the client's dedicated thread.

        Args:
            client_socket: The client's socket connection (None if ownership transferred)
            player_index: The player's index to clean up
        """
        if client_socket is not None:
            try:
                # Close the socket only if we still own it
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
        # Check if we have a Player instance for this player
        player_instance = self.get_player_instance(player_index)
        if player_instance:
            return player_instance

        # Fallback to parent node for pre-ingame clients
        return self.parent_node

    def get_player_instance(self, player_index: int):
        """
        Get the PlayerIngameHandler instance for a specific player.

        Args:
                        player_index: The player's index

        Returns:
                        PlayerIngameHandler instance if found, None otherwise
        """
        with self._threads_lock:
            for thread_info in self._client_threads.values():
                if (
                    thread_info.get("player_index") == player_index
                    and "player_instance" in thread_info
                ):
                    return thread_info["player_instance"]
        return None

    def get_all_player_instances(self) -> dict:
        """
        Get all active PlayerIngameHandler instances.

        Returns:
                        Dictionary mapping player_index to PlayerIngameHandler instances
        """
        player_instances = {}
        with self._threads_lock:
            for thread_info in self._client_threads.values():
                player_index = thread_info.get("player_index")
                player_instance = thread_info.get("player_instance")
                if player_index is not None and player_instance is not None:
                    player_instances[player_index] = player_instance
        return player_instances

    def get_ingame_player_count(self) -> int:
        """
        Get the number of players that have transferred to ingame handling.

        Returns:
                        Number of players with active PlayerIngameHandler instances
        """
        count = 0
        with self._threads_lock:
            for thread_info in self._client_threads.values():
                if "player_instance" in thread_info:
                    count += 1
        return count

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
