import socket
from server.logger import server_logger
from server.client_state_manager import client_state_manager, client_state
from server.packets import server_packets
from server.utils.socket_utils import server_socket_utils
from server.enter_game_world_pipeline import (
    character_screen_handler,
    enter_game_handler,
)
from data_models.mongodb_models import character_database


class enter_game_world_handler:
    """Handles the complete enter game world process for clients."""

    def __init__(self, character_db: character_database):
        self.character_db = character_db
        self.character_screen_handler = character_screen_handler(character_db)
        self.enter_game_handler = enter_game_handler(character_db)

    def handle_enter_game_world(
        self,
        client_socket: socket.socket,
        player_index: int,
        user_id: str,
        logger: server_logger,
        state_manager: client_state_manager,
    ) -> None:
        """
        Handle the complete enter game world process.

        Args:
            client_socket: The client's socket connection
            player_index: The player's unique index
            user_id: The user's login ID
            logger: The server logger
            state_manager: The client state manager
        """
        # Transition to waiting for character select
        state_manager.transition_state(
            player_index, client_state.INIT_WAITING_FOR_CHARACTER_SELECT
        )

        # Handle character screen interaction
        character_slot_index = (
            self.character_screen_handler.wait_for_character_screen_interaction(
                client_socket,
                player_index,
                logger,
                state_manager,
            )
        )

        # Send enter game data
        self.enter_game_handler.send_enter_game_data(
            character_slot_index,
            player_index,
            client_socket,
            logger,
            state_manager,
        )

        # Transition to waiting for client ingame ack
        state_manager.transition_state(
            player_index, client_state.INIT_WAITING_FOR_CLIENT_INGAME_ACK
        )

    def _wait_for_ingame_ack(
        self,
        client_socket: socket.socket,
        player_index: int,
        logger: server_logger,
        state_manager: client_state_manager,
    ) -> bytes:
        """
        Wait for a non-0x13 packet from the client as the ingame acknowledgment.

        Args:
            client_socket: The client's socket connection
            player_index: The player's unique index
            logger: The server logger
            state_manager: The client state manager

        Returns:
            The received packet data

        Raises:
            Exception: If waiting for ingame ack fails
        """
        while True:
            data = server_socket_utils.receive_packet_with_logging(
                client_socket,
                player_index,
                logger,
                1024,
                10.0,
                "ingame ack wait",
            )

            if not data:
                raise Exception(
                    f"Failed to receive ingame ack from player 0x{player_index:04X}"
                )

            # Ignore packets starting with 0x13
            if len(data) > 0 and data[0] == 0x13:
                msg = (
                    f"Player 0x{player_index:04X} sent packet starting with 0x13, "
                    f"ignoring: {data.hex().upper()}"
                )
                logger.debug(msg)
                continue

            # Return the first non-0x13 packet
            return data

    def handle_ingame_ack_and_world_entry(
        self,
        client_socket: socket.socket,
        player_index: int,
        logger: server_logger,
        state_manager: client_state_manager,
    ) -> None:
        """
        Handle the ingame acknowledgment and world entry process.

        Args:
            client_socket: The client's socket connection
            player_index: The player's unique index
            logger: The server logger
            state_manager: The client state manager

        Raises:
            Exception: If ingame ack and world entry fails
        """
        # Check current client state
        current_state = state_manager.get_client_state(player_index)

        if current_state != client_state.INIT_WAITING_FOR_CLIENT_INGAME_ACK:
            raise Exception(
                f"Player 0x{player_index:04X} not in correct state for ingame ack. "
                f"Current state: {current_state}"
            )

        # Wait for ingame ack (non-0x13 packet)
        data = self._wait_for_ingame_ack(
            client_socket, player_index, logger, state_manager
        )

        msg = (
            f"Player 0x{player_index:04X} sent ingame ack packet: "
            f"{data.hex().upper()}"
        )
        logger.info(msg)

        # Send new_character_world_data packet
        world_data_packet = server_packets.new_character_world_data(player_index)
        send_packet_success = server_socket_utils.send_packet_with_logging(
            client_socket,
            world_data_packet,
            player_index,
            logger,
            f"Sent new character world data to player "
            f"0x{player_index:04X}: {len(world_data_packet)} bytes",
            "world data packet",
        )
        if not send_packet_success:
            raise Exception(
                f"Failed to send world data packet to player 0x{player_index:04X}"
            )

        # Transition to IN_GAME state
        state_manager.transition_state(player_index, client_state.IN_GAME)

        msg = f"Player 0x{player_index:04X} successfully entered game world"
        logger.info(msg)
