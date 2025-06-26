from server.logger import ServerLogger
from data_models.mongodb_models import CharacterDatabase
from .exceptions import CharacterCreationException


class CharacterCreationHandler:
    """Handles character creation from packet data."""

    def __init__(self, character_db: CharacterDatabase):
        self.character_db = character_db

    def create_character_from_packet(
        self,
        data: bytes,
        user_id: str,
        character_slot_index: int,
        player_index: int,
        logger: ServerLogger,
    ) -> None:
        """
        Create a new character from the received packet data.

        Args:
            data: The packet data bytes
            user_id: The user's ID
            character_slot_index: The character slot index (0-3)
            player_index: The player index for logging
            logger: The server logger instance

        Raises:
            CharacterCreationException: If character creation fails
        """
        try:
            # Decode character name from packet
            name = self._decode_character_name(data)

            # Check if name is valid (not already taken)
            if self.character_db.character_name_exists(name):
                raise CharacterCreationException(
                    f"Player 0x{player_index:04X} tried to create character "
                    f"with existing name: {name}"
                )

            # Extract character appearance data
            char_data_bytes_start = data[0] - 5
            char_data_bytes = data[
                char_data_bytes_start : char_data_bytes_start + data[0]
            ]

            # Parse appearance data
            is_gender_female = (char_data_bytes[1] >> 4) % 2 == 1
            face_type = ((char_data_bytes[1] & 0b111111) << 2) + (
                char_data_bytes[0] >> 6
            )
            hair_style = ((char_data_bytes[2] & 0b111111) << 2) + (
                char_data_bytes[1] >> 6
            )
            hair_color = ((char_data_bytes[3] & 0b111111) << 2) + (
                char_data_bytes[2] >> 6
            )
            tattoo = ((char_data_bytes[4] & 0b111111) << 2) + (char_data_bytes[3] >> 6)

            # Apply female adjustments
            if is_gender_female:
                face_type = 256 - face_type
                hair_style = 255 - hair_style
                hair_color = 255 - hair_color
                tattoo = 255 - tattoo

            # Create character data
            character_data = {
                "user_id": user_id,
                "character_slot_index": character_slot_index,
                "name": name,
                "is_gender_female": is_gender_female,
                "face_type": face_type,
                "hair_style": hair_style,
                "hair_color": hair_color,
                "tattoo": tattoo,
            }

            # Save character to database
            character_id = self.character_db.create_character(character_data)

            if not character_id:
                raise CharacterCreationException(
                    f"Player 0x{player_index:04X} failed to save character '{name}' to database"
                )

            msg = (
                f"Player 0x{player_index:04X} created character '{name}' "
                f"in slot {character_slot_index} with ID {character_id}"
            )
            logger.info(msg)

        except CharacterCreationException:
            raise
        except Exception as e:
            raise CharacterCreationException(
                f"Error creating character for player 0x{player_index:04X}: {str(e)}"
            )

    def _decode_character_name(self, data: bytes) -> str:
        """
        Decode character name from packet data using the game's encoding scheme.

        Args:
            data: The packet data bytes

        Returns:
            str: The decoded character name
        """
        length = data[0] - 20 - 5
        name_check_bytes = data[20:]

        name_chars = []
        first_letter_char_code = ((name_check_bytes[1] & 0b11111) << 3) + (
            name_check_bytes[0] >> 5
        )
        first_letter_should_be_russian = False

        # Decode characters starting from index 1
        for i in range(1, length):
            current_char_code = ((name_check_bytes[i] & 0b11111) << 3) + (
                name_check_bytes[i - 1] >> 5
            )

            if current_char_code % 2 == 0:
                # English character
                current_letter = chr(current_char_code // 2)
                name_chars.append(current_letter)
            else:
                # Russian character
                if current_char_code >= 193:
                    current_letter = chr((current_char_code - 192) // 2 + ord("а"))
                else:
                    current_letter = chr((current_char_code - 129) // 2 + ord("А"))
                name_chars.append(current_letter)

                if i == 2:
                    # Assume first letter was Russian if second letter is
                    first_letter_should_be_russian = True

        # Handle first letter
        if first_letter_should_be_russian:
            first_letter_char_code += 1
            if first_letter_char_code >= 193:
                first_letter = chr((first_letter_char_code - 192) // 2 + ord("а"))
            else:
                first_letter = chr((first_letter_char_code - 129) // 2 + ord("А"))
            name = (
                first_letter + "".join(name_chars[1:])
                if len(name_chars) > 1
                else first_letter
            )
        else:
            first_letter = chr(first_letter_char_code // 2)
            name = (
                first_letter + "".join(name_chars[1:])
                if len(name_chars) > 1
                else first_letter
            )

        return name
