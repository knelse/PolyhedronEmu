import threading
from enum import Enum
from typing import Dict, Optional
from server.logger import ServerLogger
from server.exceptions import StateTransitionException


class ClientState(Enum):
    """Enumeration of possible client states."""

    BASE = 0
    INIT_READY_FOR_INITIAL_DATA = 1
    INIT_WAITING_FOR_LOGIN_DATA = 2
    INIT_WAITING_FOR_CHARACTER_SELECT = 3
    INIT_WAITING_FOR_CLIENT_INGAME_ACK = 4
    IN_GAME = 5


class ClientStateManager:
    """Manages the state of connected clients."""

    def __init__(self, logger: ServerLogger):
        self.logger = logger
        # player_index -> ClientState
        self._client_states: Dict[int, ClientState] = {}
        # player_index -> user_id
        self._client_user_ids: Dict[int, str] = {}
        self._state_lock = threading.Lock()

    def add_client(self, player_index: int) -> None:
        """
        Add a new client with initial base state.

        Args:
            player_index: The player's unique index
        """
        with self._state_lock:
            self._client_states[player_index] = ClientState.BASE
            msg = (
                f"Client 0x{player_index:04X} added with state: "
                f"{ClientState.BASE.name.lower()}"
            )
            self.logger.info(msg)

    def remove_client(self, player_index: int) -> None:
        """
        Remove a client from state tracking.

        Args:
            player_index: The player's unique index
        """
        with self._state_lock:
            if player_index in self._client_states:
                old_state = self._client_states[player_index]
                del self._client_states[player_index]
                if player_index in self._client_user_ids:
                    del self._client_user_ids[player_index]
                msg = (
                    f"Client 0x{player_index:04X} removed from state "
                    f"tracking (was in {old_state.name.lower()})"
                )
                self.logger.info(msg)

    def set_client_state(self, player_index: int, new_state: ClientState) -> bool:
        """
        Set a client's state.

        Args:
            player_index: The player's unique index
            new_state: The new state to set

        Returns:
            True if state was changed, False if client not found
        """
        with self._state_lock:
            if player_index not in self._client_states:
                msg = (
                    f"Attempted to set state for unknown client "
                    f"0x{player_index:04X}"
                )
                self.logger.warning(msg)
                return False

            old_state = self._client_states[player_index]
            self._client_states[player_index] = new_state

            if old_state != new_state:
                msg = (
                    f"Client 0x{player_index:04X} state changed: "
                    f"{old_state.name.lower()} -> {new_state.name.lower()}"
                )
                self.logger.info(msg)

            return True

    def get_client_state(self, player_index: int) -> Optional[ClientState]:
        """
        Get a client's current state.

        Args:
            player_index: The player's unique index

        Returns:
            The client's current state, or None if client not found
        """
        with self._state_lock:
            return self._client_states.get(player_index)

    def transition_state(self, player_index: int, new_state: ClientState) -> None:
        """
        Transition a client from their current state to a new state.
        Validates that the transition follows the expected sequential order.

        Args:
            player_index: The player's unique index
            new_state: The new state to transition to

        Raises:
            StateTransitionException: If the transition fails
        """
        with self._state_lock:
            current_state = self._client_states.get(player_index)

            if current_state is None:
                msg = (
                    f"Cannot transition unknown client "
                    f"0x{player_index:04X} to {new_state.name.lower()}"
                )
                self.logger.warning(msg)
                raise StateTransitionException(msg)

            if new_state.value != current_state.value + 1:
                msg = (
                    f"Client 0x{player_index:04X} cannot transition from "
                    f"{current_state.name.lower()} to {new_state.name.lower()}"
                )
                self.logger.warning(msg)
                raise StateTransitionException(msg)

            self._client_states[player_index] = new_state
            msg = (
                f"Client 0x{player_index:04X} transitioned to "
                f"{new_state.name.lower()}"
            )
            self.logger.info(msg)

    def get_clients_by_state(self, state: ClientState) -> list[int]:
        """
        Get all client indices that are in a specific state.

        Args:
            state: The state to filter by

        Returns:
            List of player indices in the specified state
        """
        with self._state_lock:
            return [
                player_index
                for player_index, client_state in self._client_states.items()
                if client_state == state
            ]

    def get_all_client_states(self) -> Dict[int, ClientState]:
        """
        Get a copy of all client states.

        Returns:
            Dictionary mapping player indices to their current states
        """
        with self._state_lock:
            return self._client_states.copy()

    def get_client_count_by_state(self, state: ClientState) -> int:
        """
        Get the count of clients in a specific state.

        Args:
            state: The state to count

        Returns:
            Number of clients in the specified state
        """
        with self._state_lock:
            return sum(
                1
                for client_state in self._client_states.values()
                if client_state == state
            )

    def set_user_id(self, player_index: int, user_id: str) -> bool:
        """
        Set the user_id for a client.

        Args:
            player_index: The player's unique index
            user_id: The user's login ID

        Returns:
            True if set successfully, False if client not found
        """
        with self._state_lock:
            if player_index not in self._client_states:
                msg = (
                    f"Attempted to set user_id for unknown client "
                    f"0x{player_index:04X}"
                )
                self.logger.warning(msg)
                return False

            self._client_user_ids[player_index] = user_id
            msg = f"Set user_id '{user_id}' for client 0x{player_index:04X}"
            self.logger.debug(msg)
            return True

    def get_user_id(self, player_index: int) -> Optional[str]:
        """
        Get the user_id for a client.

        Args:
            player_index: The player's unique index

        Returns:
            The user_id if found, None otherwise
        """
        with self._state_lock:
            return self._client_user_ids.get(player_index)

    def cleanup_client(self, player_index: int) -> None:
        """
        Clean up a client's state and user_id information.
        This is an alias for remove_client for consistency with the API.

        Args:
            player_index: The player's unique index
        """
        self.remove_client(player_index)

    def cleanup_all_clients(self) -> None:
        """
        Clean up all clients' state and user_id information.
        This is typically called during server shutdown.
        """
        with self._state_lock:
            client_count = len(self._client_states)
            if client_count > 0:
                self._client_states.clear()
                self._client_user_ids.clear()
                self.logger.info(
                    f"Cleaned up all {client_count} clients from state tracking"
                )
            else:
                self.logger.debug("No clients to clean up")
