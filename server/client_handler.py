import socket
import threading
from typing import Callable
from py4godot.classes.Node3D import Node3D
from server.logger import ServerLogger
from server.player_manager import PlayerManager
from server.client_state_manager import ClientStateManager
from server.packets import INIT_PACKET


class ClientHandler:
    def __init__(self, logger: ServerLogger, player_manager: PlayerManager,
                 parent_node: Node3D):
        self.logger = logger
        self.player_manager = player_manager
        self.parent_node = parent_node
        self.state_manager = ClientStateManager(logger)
        self.is_running = False
        self.client_nodes = {}  # player_index -> Node3D
        self.nodes_lock = threading.Lock()

    def start_handling(self, server_socket: socket.socket,
                       is_running: Callable[[], bool]) -> None:
        """
        Start handling connections on the given server socket.

        Args:
            server_socket: The server socket to accept connections from
            is_running: A callable that returns whether the server is
                       still running
        """
        self.is_running = True
        while is_running():
            try:
                client_socket, address = server_socket.accept()

                player_index = self.player_manager.get_next_player_index()
                if player_index is None:
                    msg = (f"Rejecting connection from {address}: "
                           f"Maximum players reached")
                    self.logger.warning(msg)
                    client_socket.close()
                    continue

                client_node = Node3D()
                client_node.set_name(f"Player_{player_index:04X}")

                with self.nodes_lock:
                    self.parent_node.call_deferred("add_child", client_node)
                    self.client_nodes[player_index] = client_node

                self.player_manager.add_player(player_index, address)
                self.state_manager.add_client(player_index)

                try:
                    client_socket.send(INIT_PACKET)
                    msg = (f"Sent init packet to player "
                           f"0x{player_index:04X}: {INIT_PACKET.hex()}")
                    self.logger.debug(msg)

                    success = self.state_manager.transition_to_init_ready(
                        player_index)
                    if success:
                        msg = (f"Player 0x{player_index:04X} successfully "
                               f"initialized and ready for initial data")
                        self.logger.info(msg)

                except Exception as e:
                    msg = (f"Failed to send init packet to player "
                           f"0x{player_index:04X}")
                    self.logger.log_exception(msg, e)
                    client_socket.close()
                    self.player_manager.remove_player(player_index)
                    self.state_manager.remove_client(player_index)
                    with self.nodes_lock:
                        if player_index in self.client_nodes:
                            node = self.client_nodes[player_index]
                            node.call_deferred("queue_free")
                            del self.client_nodes[player_index]
                    continue

                msg = (f"New connection from {address} assigned player "
                       f"index: 0x{player_index:04X}, created node: "
                       f"{client_node.get_name()}")
                self.logger.info(msg)

                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address, player_index, is_running)
                )
                client_thread.daemon = True
                client_thread.start()
                msg = (f"Started client handler thread for player "
                       f"0x{player_index:04X}")
                self.logger.debug(msg)
            except Exception as e:
                if self.is_running:
                    self.logger.log_exception("Error in handle_connections", e)
                break

    def handle_client(self, client_socket: socket.socket, address: tuple,
                      player_index: int,
                      is_running: Callable[[], bool]) -> None:
        """
        Handle communication with a specific client.

        Args:
            client_socket: The client's socket connection
            address: The client's address
            player_index: The assigned player index
            is_running: A callable that returns whether the server is
                       still running
        """
        try:
            while is_running():
                data = client_socket.recv(1024)
                if not data:
                    msg = (f"Player 0x{player_index:04X} ({address}) "
                           f"disconnected")
                    self.logger.info(msg)
                    break

                msg = (f"Received from player 0x{player_index:04X}: "
                       f"{data.hex()}")
                self.logger.debug(msg)
                client_socket.send(data)
        except Exception as e:
            msg = f"Error handling player 0x{player_index:04X}"
            self.logger.log_exception(msg, e)
        finally:
            try:
                client_socket.close()
                self.player_manager.remove_player(player_index)
                self.state_manager.remove_client(player_index)

                with self.nodes_lock:
                    if player_index in self.client_nodes:
                        client_node = self.client_nodes[player_index]
                        client_node.call_deferred("queue_free")
                        del self.client_nodes[player_index]
                        msg = (f"Cleaned up node for player "
                               f"0x{player_index:04X}")
                        self.logger.debug(msg)

                msg = f"Connection closed for player 0x{player_index:04X}"
                self.logger.info(msg)
            except Exception as e:
                msg = (f"Error closing connection for player "
                       f"0x{player_index:04X}")
                self.logger.log_exception(msg, e)

    def stop_handling(self) -> None:
        """Stop handling new connections and clean up all client nodes."""
        self.is_running = False

        with self.nodes_lock:
            for player_index, client_node in self.client_nodes.items():
                try:
                    client_node.call_deferred("queue_free")
                    self.state_manager.remove_client(player_index)
                    msg = (f"Cleaned up node for player 0x{player_index:04X} "
                           f"during shutdown")
                    self.logger.debug(msg)
                except Exception as e:
                    msg = (f"Error cleaning up node for player "
                           f"0x{player_index:04X}")
                    self.logger.log_exception(msg, e)
            self.client_nodes.clear()

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
