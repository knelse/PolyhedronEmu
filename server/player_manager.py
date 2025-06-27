import threading
from typing import Optional


class player_manager:
    INITIAL_PLAYER_INDEX = 0x4F6F
    MAX_PLAYER_INDEX = 0xFFFF

    def __init__(self):
        self._next_player_index = self.INITIAL_PLAYER_INDEX
        self._index_lock = threading.Lock()
        self._active_players = {}  # player_index -> connection info
        self._players_lock = threading.Lock()
        self._available_indices = set()

    def get_next_player_index(self) -> Optional[int]:
        """
        Thread-safely get the next available player index.
        First tries to reuse an available index, then creates a new one if
        none are available. Returns None if maximum number of players is
        reached.
        """
        with self._index_lock:
            if self._available_indices:
                return self._available_indices.pop()
            if self._next_player_index > self.MAX_PLAYER_INDEX:
                return None
            current_index = self._next_player_index
            self._next_player_index += 1
            return current_index

    def add_player(self, player_index: int, address: tuple) -> None:
        """
        Register a new player with their connection information.
        """
        with self._players_lock:
            self._active_players[player_index] = {
                "address": address,
                "connected_at": threading.get_native_id(),
            }

    def remove_player(self, player_index: int) -> None:
        """
        Remove a player when they disconnect and make their index available
        for reuse.
        """
        with self._players_lock, self._index_lock:
            if player_index in self._active_players:
                del self._active_players[player_index]
                self._available_indices.add(player_index)

    def get_player_count(self) -> int:
        """
        Get the current number of active players.
        """
        with self._players_lock:
            return len(self._active_players)

    def get_player_info(self, player_index: int) -> Optional[dict]:
        """
        Get information about a specific player.
        """
        with self._players_lock:
            return self._active_players.get(player_index)

    def get_all_players(self) -> dict:
        """
        Get a copy of all active players information.
        """
        with self._players_lock:
            return self._active_players.copy()

    def reserve_index(self, player_index: int) -> None:
        """
        Reserve a player index (mark it as in use).
        This is typically called when a player index is assigned to a client.

        Args:
            player_index: The player index to reserve
        """
        with self._index_lock:
            self._available_indices.discard(player_index)

    def release_index(self, player_index: int) -> None:
        """
        Release a player index and make it available for reuse.
        This is an alias for remove_player for consistency with the API.

        Args:
            player_index: The player index to release
        """
        self.remove_player(player_index)

    def release_all_indices(self) -> None:
        """
        Release all player indices and clear all active players.
        This is typically called during server shutdown.
        """
        with self._players_lock, self._index_lock:
            player_count = len(self._active_players)
            if player_count > 0:
                self._active_players.clear()
                self._available_indices.clear()
            # Reset the next player index to initial value
            self._next_player_index = self.INITIAL_PLAYER_INDEX
