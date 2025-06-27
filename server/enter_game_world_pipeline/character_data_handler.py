import socket
import time
from server.logger import server_logger
from server.packets import server_packets
from server.utils.socket_utils import server_socket_utils
from data_models.mongodb_models import character_database
from .exceptions import character_data_exception


class character_data_handler:
	"""Handles character data creation and sending."""

	def __init__(self, character_db: character_database):
		self.character_db = character_db

	def send_character_select_and_data(
		self,
		player_index: int,
		user_id: str,
		client_socket: socket.socket,
		logger: server_logger,
	) -> None:
		"""
		Send character select start packet and triple character data.

		Args:
			player_index: The player's index
			user_id: The user's ID
			client_socket: The client's socket connection
			logger: The server logger instance

		Raises:
			character_data_exception: If sending character data fails
		"""
		time.sleep(0.05)
		char_select_packet = server_packets.get_character_select_start_data(player_index)
		send_packet_success = server_socket_utils.send_packet_or_cleanup(
			client_socket,
			char_select_packet,
			player_index,
			logger,
			f"Sent character select start to player "
			f"0x{player_index:04X}: {char_select_packet.hex().upper()}",
			None,  # No cleanup callback needed since we'll throw exception
			"character select packet",
		)
		if not send_packet_success:
			raise character_data_exception(
				f"Failed to send character select packet to player 0x{player_index:04X}"
			)

		# Send 3x new character data back-to-back
		time.sleep(0.1)
		char_data_packet = self._create_triple_character_data(
			player_index, user_id, logger
		)
		send_packet_success = server_socket_utils.send_packet_or_cleanup(
			client_socket,
			char_data_packet,
			player_index,
			logger,
			f"Sent triple character data to player "
			f"0x{player_index:04X}: {char_data_packet.hex().upper()}",
			None,  # No cleanup callback needed since we'll throw exception
			"character data packet",
		)
		if not send_packet_success:
			raise character_data_exception(
				f"Failed to send character data packet to player 0x{player_index:04X}"
			)

	def _create_triple_character_data(
		self, player_index: int, user_id: str, logger: server_logger
	) -> bytes:
		"""
		Create a packet containing 3 character data entries back-to-back.
		Uses actual characters from database, filling with defaults if needed.

		Args:
			player_index: The player's index
			user_id: The user's login ID to fetch characters for
			logger: The server logger instance

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
				# Convert MongoDB character to client_character
				character = user_characters[i].to_client_character()
				character.player_index = player_index
				characters.append(character)
				char_data = character.to_character_list_bytearray()
				char_data_packets.append(char_data)
			else:
				char_data_packets.append(
					server_packets.get_new_character_data(player_index)
				)

		# Combine all three packets without separators
		combined_packet = b"".join(char_data_packets)

		msg = (
			f"Created triple character data for user {user_id} "
			f"(player 0x{player_index:04X}): {len(user_characters)} actual characters, "
			f"{3 - len(user_characters)} default characters, "
			f"total length: {len(combined_packet)} bytes"
		)
		logger.debug(msg)

		return combined_packet
