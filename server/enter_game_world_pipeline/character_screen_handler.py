import socket
from server.logger import ServerLogger
from server.client_state_manager import ClientStateManager
from server.packets import ServerPackets
from server.utils.socket_utils import ServerSocketUtils
from data_models.mongodb_models import CharacterDatabase
from .character_creation_handler import CharacterCreationHandler
from .exceptions import CharacterScreenException


class CharacterScreenHandler:
    """Handles character screen interactions including selection, deletion, and creation."""

    def __init__(self, character_db: CharacterDatabase):
        self.character_db = character_db
        self.character_creator = CharacterCreationHandler(character_db)

    def wait_for_character_screen_interaction(
        self,
        client_socket: socket.socket,
        player_index: int,
        logger: ServerLogger,
        state_manager: ClientStateManager,
    ) -> int:
        """
        Wait for client to interact with the character screen (select or delete character).

        Args:
            client_socket: The client's socket connection
            player_index: The player's index for logging
            logger: The server logger instance
            state_manager: The client state manager

        Returns:
            int: character slot index if character creation or selection succeeded

        Raises:
            CharacterScreenException: If character screen interaction fails or character
                is deleted
        """
        try:
            while True:
                data = ServerSocketUtils.receive_packet_with_logging(
                    client_socket,
                    player_index,
                    logger,
                    1024,
                    86400.0,
                    "character screen wait",
                )
                if not data:
                    raise CharacterScreenException(
                        f"Failed to receive character screen data from player "
                        f"0x{player_index:04X}"
                    )

                if len(data) > 0 and data[0] == 0x2A:
                    logger.debug("Requested character delete")
                    if len(data) >= 18:
                        character_slot_index = data[17] // 4 - 1
                        user_id = state_manager.get_user_id(player_index)
                        if user_id:
                            success = self.character_db.delete_character_by_user_index(
                                user_id, character_slot_index
                            )
                            if success:
                                msg = (
                                    f"Player 0x{player_index:04X} deleted character "
                                    f"at slot {character_slot_index}"
                                )
                                logger.info(msg)
                            else:
                                msg = (
                                    f"Player 0x{player_index:04X} failed to delete "
                                    f"character at slot {character_slot_index}"
                                )
                                logger.warning(msg)
                        else:
                            msg = (
                                f"Player 0x{player_index:04X} attempted character "
                                f"delete but no user_id found"
                            )
                            logger.warning(msg)
                    else:
                        msg = (
                            f"Player 0x{player_index:04X} sent character delete "
                            f"packet too short: {len(data)} bytes"
                        )
                        logger.warning(msg)

                    raise CharacterScreenException(
                        f"Player 0x{player_index:04X} deleted character - "
                        f"connection should be closed"
                    )

                if len(data) >= 18 and data[0] == 0x15:
                    character_slot_index = data[17] // 4 - 1
                    user_id = state_manager.get_user_id(player_index)
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
                            logger.info(msg)
                            return character_slot_index
                        else:
                            raise CharacterScreenException(
                                f"Player 0x{player_index:04X} tried to select "
                                f"non-existent character at slot {character_slot_index}"
                            )
                    else:
                        msg = (
                            f"Player 0x{player_index:04X} attempted character "
                            f"selection but no user_id found"
                        )
                        logger.warning(msg)
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
                user_id = state_manager.get_user_id(player_index)
                if user_id:
                    character_slot_index = data[17] // 4 - 1
                    try:
                        self.character_creator.create_character_from_packet(
                            data, user_id, character_slot_index, player_index, logger
                        )
                        # If we get here, character creation succeeded
                        success_packet = ServerPackets.character_name_check_success(
                            player_index
                        )
                        send_packet_success = ServerSocketUtils.send_packet_or_cleanup(
                            client_socket,
                            success_packet,
                            player_index,
                            logger,
                            f"Sent character name check success to player "
                            f"0x{player_index:04X}: {success_packet.hex().upper()}",
                            None,  # No cleanup callback needed since we'll throw exception
                            "character name check success packet",
                        )
                        if not send_packet_success:
                            raise CharacterScreenException(
                                f"Failed to send character name check success to player "
                                f"0x{player_index:04X}"
                            )

                        msg = f"Character creation completed for player 0x{player_index:04X}"
                        logger.info(msg)
                        return character_slot_index
                    except Exception:
                        # Name already exists or other error
                        name_taken_packet = ServerPackets.character_name_already_taken(
                            player_index
                        )
                        send_packet_success = ServerSocketUtils.send_packet_or_cleanup(
                            client_socket,
                            name_taken_packet,
                            player_index,
                            logger,
                            f"Sent character name already taken to player "
                            f"0x{player_index:04X}: {name_taken_packet.hex().upper()}",
                            None,  # No cleanup callback needed since we'll throw exception
                            "character name taken packet",
                        )
                        if not send_packet_success:
                            raise CharacterScreenException(
                                f"Failed to send character name taken packet to player "
                                f"0x{player_index:04X}"
                            )

                        # Close connection after sending the packet
                        raise CharacterScreenException(
                            f"Character creation failed for player 0x{player_index:04X} - "
                            f"name already exists"
                        )
                else:
                    msg = (
                        f"Player 0x{player_index:04X} attempted character "
                        f"creation but no user_id found"
                    )
                    logger.warning(msg)
                    continue

        except socket.timeout:
            raise CharacterScreenException(
                f"Timeout waiting for character screen interaction from player "
                f"0x{player_index:04X}"
            )
        except CharacterScreenException:
            raise
        except Exception as e:
            raise CharacterScreenException(
                f"Error waiting for character screen interaction from player "
                f"0x{player_index:04X}: {str(e)}"
            )
