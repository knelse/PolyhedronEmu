from py4godot.classes import gdclass
from py4godot.classes.Node import Node
from data_models.client_character import ClientCharacter


@gdclass
class CharacterSheet(Node):
    """
    CharacterSheet node that manages character data for a player.
    Stores an instance of ClientCharacter data model.
    """

    def __init__(self):
        super().__init__()
        self.character_data: ClientCharacter = None

    def _ready(self) -> None:
        """Called when the node is ready."""
        pass

    def set_character_data(self, character_data: ClientCharacter) -> None:
        """
        Set the character data for this character sheet.

        Args:
            character_data: The ClientCharacter instance to store
        """
        self.character_data = character_data

    def get_character_data(self) -> ClientCharacter:
        """
        Get the character data from this character sheet.

        Returns:
            The stored ClientCharacter instance
        """
        return self.character_data

    def has_character_data(self) -> bool:
        """
        Check if character data has been set.

        Returns:
            True if character data is set, False otherwise
        """
        return self.character_data is not None
