from py4godot.classes import gdclass
from py4godot.classes.Node3D import Node3D
import socket
import threading
import traceback
from server.config import load_config
from server.logger import create_logger
from server.player_manager import PlayerManager
from server.client_handler import ClientHandler
from server.signal_handler import SignalHandler


@gdclass
class main_server_node(Node3D):
    SERVER_PORT = 25860

    def __init__(self):
        try:
            super().__init__()
            self.server_socket = None
            self.is_running = False

            self.config = load_config()

            self.logger = create_logger()
            self.player_manager = PlayerManager()
            self.client_handler = ClientHandler(self.logger, self.player_manager, self)

            # Initialize signal handler for graceful shutdown
            self.signal_handler = SignalHandler(self.logger)
            self.signal_handler.add_shutdown_callback(self._graceful_shutdown)
            self.signal_handler.setup_signal_handlers()

            self.logger.info("Server node initialized")
            self.logger.debug(f"Loaded configuration: {self.config}")
        except Exception as e:
            print(f"Error in __init__: {str(e)}")
            print(traceback.format_exc())

    def _ready(self) -> None:
        try:
            self.logger.info("Starting server in _ready")
            self.start_server()
        except Exception as e:
            self.logger.log_exception("Error in _ready", e)

    def start_server(self) -> None:
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            host = self.config["server"]["host"]
            port = self.config["server"]["port"]
            backlog = self.config["server"]["backlog"]

            self.server_socket.bind((host, port))
            self.server_socket.listen(backlog)
            self.is_running = True

            self.logger.info(f"Server socket created and bound to {host}:{port}")

            server_thread = threading.Thread(
                target=self.client_handler.start_handling,
                args=(self.server_socket, lambda: self.is_running),
            )
            server_thread.daemon = True
            server_thread.start()
            self.logger.info("Server thread started")
        except Exception as e:
            self.logger.log_exception("Error in start_server", e)

    def get_state_manager(self):
        """Get the client state manager instance."""
        return self.client_handler.state_manager

    def get_client_handler(self):
        """Get the client handler instance."""
        return self.client_handler

    def _graceful_shutdown(self) -> None:
        """
        Perform graceful shutdown of the server.
        This method is called by the signal handler.
        """
        try:
            active_players = self.player_manager.get_player_count()
            shutdown_msg = f"Server shutting down with {active_players} active players"
            self.logger.info(shutdown_msg)

            # Stop the server
            self.is_running = False

            # Stop client handler and wait for threads to finish
            self.client_handler.stop_handling()

            # Close server socket
            if self.server_socket:
                self.server_socket.close()
                self.logger.info("Server socket closed")

            # Force cleanup any remaining threads
            self.signal_handler.force_thread_cleanup(timeout=3.0)

        except Exception as e:
            self.logger.log_exception("Error in graceful shutdown", e)

    def _exit_tree(self) -> None:
        try:
            # Restore original signal handlers
            if hasattr(self, "signal_handler"):
                self.signal_handler.restore_signal_handlers()

            # If not already shut down, perform shutdown
            if self.is_running:
                self._graceful_shutdown()

        except Exception as e:
            self.logger.log_exception("Error in _exit_tree", e)
