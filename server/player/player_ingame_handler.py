import socket
import threading
from typing import Callable
from py4godot.classes import gdclass
from py4godot.classes.Node3D import Node3D
from server.client_state_manager import ClientStateManager
from server.logger import ServerLogger
from server.player_manager import PlayerManager
from server.utils.socket_utils import ServerSocketUtils


@gdclass
class PlayerIngameHandler(Node3D):
	"""
	PlayerIngameHandler manages the ingame behavior and interactions for a player.
	This script is attached to the Player node (Node3D).
	"""

	client_socket: socket.socket | None
	player_index: int
	logger: ServerLogger | None
	state_manager: ClientStateManager
	user_id: str | None
	player_manager: PlayerManager | None
	is_running: Callable[[], bool] | None

	def __init__(self):
		super().__init__()
		self.client_thread = None
		self._cleanup_done = False

	def start_ingame_handling(self) -> None:
		"""Start the ingame communication handling in a separate thread."""
		if self.client_socket is None or self.is_running is None:
			raise RuntimeError("Player not properly initialized")

		self.client_thread = threading.Thread(
			target=self._handle_ingame_communication, daemon=True
		)
		self.client_thread.start()

		msg = (
			f"Started ingame communication thread for player 0x{self.player_index:04X}"
		)
		self.logger.info(msg)

	def send_data(self, data: bytes) -> bool:
		"""
		Send data to the client.

		Args:
			data: The data to send

		Returns:
		   True if data was sent successfully, False otherwise
		"""
		if not self.client_socket:
			return False

		try:
			self.client_socket.send(data)
			return True
		except Exception as e:
			msg = f"Error sending data to player 0x{self.player_index:04X}"
			self.logger.log_exception(msg, e)
			return False

	def _handle_ingame_communication(self) -> None:
		"""
		Handle ongoing ingame communication with the client.
		This runs on a dedicated thread.
		"""
		try:
			msg = f"Started ingame communication loop for player 0x{self.player_index:04X}"
			self.logger.debug(msg)

			while self.is_running():
				try:
					data = ServerSocketUtils.receive_packet_with_logging(
						self.client_socket,
						self.player_index,
						self.logger,
						1024,
						10.0,
						"ingame communication",
					)

					if not data:
						break

					# TODO: Handle ingame packets here
					# For now, just log the received data
					msg = (
						f"Player 0x{self.player_index:04X} sent ingame packet: "
						f"{data.hex().upper()}"
					)
					self.logger.debug(msg)

				except socket.timeout:
					continue
				except ConnectionResetError:
					msg = f"Player 0x{self.player_index:04X} connection reset"
					self.logger.info(msg)
					break
				except Exception as e:
					msg = f"Error in ingame communication with player 0x{self.player_index:04X}"
					self.logger.log_exception(msg, e)
					break

		except Exception as e:
			msg = f"Error in ingame communication thread for player 0x{self.player_index:04X}"
			self.logger.log_exception(msg, e)
		finally:
			self._cleanup_player()

	def stop_handling(self) -> None:
		"""Stop the ingame handling and clean up resources."""
		if self.client_thread and self.client_thread.is_alive():
			msg = f"Stopping ingame handling for player 0x{self.player_index:04X}"
			self.logger.info(msg)

			# The thread will stop when is_running() returns False
			# Wait for the thread to finish
			self.client_thread.join(timeout=5.0)

			if self.client_thread.is_alive():
				msg = f"Ingame thread for player 0x{self.player_index:04X} did not stop gracefully"
				self.logger.warning(msg)

	def _cleanup_player(self) -> None:
		"""
		Clean up all resources associated with this player.
		"""
		if self._cleanup_done:
			return

		self._cleanup_done = True

		try:
			if self.client_socket:
				self.client_socket.close()
		except Exception:
			pass

		if self.player_manager and self.player_index is not None:
			self.player_manager.release_index(self.player_index)

		if self.state_manager and self.player_index is not None:
			self.state_manager.cleanup_client(self.player_index)

		if self.player_index is not None:
			msg = f"Cleaned up ingame resources for player 0x{self.player_index:04X}"
			self.logger.debug(msg)

	def _ready(self) -> None:
		"""Called when the node is ready. Handle character sheet setup and start ingame handling."""
		if self.logger and self.player_index is not None:
			msg = f"Player 0x{self.player_index:04X} ingame handler ready"
			self.logger.info(msg)

		# Get character sheet and set character data
		character_sheet = self.get_node("CharacterSheet")
		if character_sheet and hasattr(character_sheet, "set_character_data"):
			if self.state_manager and hasattr(self.state_manager, "get_character_data"):
				character_data = self.state_manager.get_character_data(
					self.player_index
				)
				if character_data:
					character_sheet.set_character_data(character_data)

		# Start ingame handling
		self.start_ingame_handling()

	def _process(self, delta: float) -> None:
		"""Called every frame."""
		pass

	def _exit_tree(self) -> None:
		"""Called when the node is removed from the scene tree."""
		self.stop_handling()
