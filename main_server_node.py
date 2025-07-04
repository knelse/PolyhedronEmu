from py4godot.classes import gdclass
from py4godot.classes.Node3D import Node3D
import socket
import threading
import traceback
from server.config import load_config
from server.logger import create_logger
from server.player_manager import player_manager
from server.client_pre_ingame_handler import client_pre_ingame_handler


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
			self.player_manager = player_manager()
			self.client_handler = client_pre_ingame_handler(
				self.logger, self.player_manager, self
			)

			self.logger.info("Server node initialized")
			self.logger.debug(f"Loaded configuration: {self.config}")
		except Exception as e:
			# Fallback to basic logging if logger creation fails
			import logging

			logging.basicConfig(level=logging.ERROR)
			logger = logging.getLogger("main_server_node")
			logger.error(f"Error in __init__: {str(e)}")
			logger.error(f"Traceback: {traceback.format_exc()}")

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

	def _exit_tree(self) -> None:
		try:
			active_players = self.player_manager.get_player_count()
			shutdown_msg = f"Server shutting down with {active_players} active players"
			self.logger.info(shutdown_msg)
			self.is_running = False
			self.client_handler.stop_handling()
			if self.server_socket:
				self.server_socket.close()
				self.logger.info("Server socket closed")
		except Exception as e:
			self.logger.log_exception("Error in _exit_tree", e)
