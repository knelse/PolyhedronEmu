import socket
from server.logger import ServerLogger
from server.client_state_manager import ClientStateManager
from server.utils.socket_utils import ServerSocketUtils
from data_models.mongodb_models import CharacterDatabase
from .exceptions import EnterGameException


class EnterGameHandler:
    """Handles sending enter game data to clients."""

    def __init__(self, character_db: CharacterDatabase):
        self.character_db = character_db

    def send_enter_game_data(
        self,
        character_slot_index: int,
        player_index: int,
        client_socket: socket.socket,
        logger: ServerLogger,
        state_manager: ClientStateManager,
    ) -> None:
        """
        Send enter game data for a newly created character.
        This is called after successful character creation.

        Args:
            character_slot_index: The character slot index that was created
            player_index: The player's index for logging
            client_socket: The client's socket connection
            logger: The server logger instance
            state_manager: The client state manager

        Raises:
            EnterGameException: If sending enter game data fails
        """
        try:
            # Get the user_id from state manager
            user_id = state_manager.get_user_id(player_index)
            if not user_id:
                raise EnterGameException(
                    f"Cannot send enter game data for player 0x{player_index:04X} - "
                    f"no user_id found"
                )

            # Retrieve the newly created character from database
            character_data = self.character_db.characters.find_one(
                {
                    "user_id": user_id,
                    "character_slot_index": character_slot_index,
                    "is_not_queued_for_deletion": True,
                }
            )

            if not character_data:
                raise EnterGameException(
                    f"Cannot send enter game data for player 0x{player_index:04X} - "
                    f"character not found at slot {character_slot_index}"
                )

            # Convert MongoDB character to ClientCharacter
            from data_models.mongodb_models import ClientCharacterMongo

            character_mongo = ClientCharacterMongo.from_dict(character_data)
            character = character_mongo.to_client_character()

            # Set the correct player index
            character.player_index = player_index

            # Generate the game data bytearray
            game_data = character.to_game_data_bytearray()

            # Send the game data to the client
            send_success = ServerSocketUtils.send_packet_with_logging(
                client_socket,
                game_data,
                player_index,
                logger,
                f"Sent enter game data to player 0x{player_index:04X}: "
                f"{len(game_data)} bytes",
                "enter game data packet",
            )

            if not send_success:
                raise EnterGameException(
                    f"Failed to send enter game data for player 0x{player_index:04X}"
                )

            msg = (
                f"Successfully sent enter game data for character '{character.name}' "
                f"at slot {character_slot_index} to player 0x{player_index:04X} "
                f"({len(game_data)} bytes)"
            )
            logger.info(msg)

        except EnterGameException:
            raise
        except Exception as e:
            raise EnterGameException(
                f"Error sending enter game data for player 0x{player_index:04X}: {str(e)}"
            )
