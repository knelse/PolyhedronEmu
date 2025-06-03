import threading
from enum import Enum
from typing import Dict, Optional
from server.logger import ServerLogger

class ClientState(Enum):
    """Enumeration of possible client states."""
    BASE = "base"
    INIT_READY_FOR_INITIAL_DATA = "init_ready_for_initial_data"
    IN_GAME = "in_game"

class ClientStateManager:
    """Manages the state of connected clients."""
    
    def __init__(self, logger: ServerLogger):
        self.logger = logger
        self._client_states: Dict[int, ClientState] = {}  # player_index -> ClientState
        self._state_lock = threading.Lock()
    
    def add_client(self, player_index: int) -> None:
        """
        Add a new client with initial base state.
        
        Args:
            player_index: The player's unique index
        """
        with self._state_lock:
            self._client_states[player_index] = ClientState.BASE
            self.logger.info(f"Client 0x{player_index:04X} added with state: {ClientState.BASE.value}")
    
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
                self.logger.info(f"Client 0x{player_index:04X} removed from state tracking (was in {old_state.value})")
    
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
                self.logger.warning(f"Attempted to set state for unknown client 0x{player_index:04X}")
                return False
            
            old_state = self._client_states[player_index]
            self._client_states[player_index] = new_state
            
            if old_state != new_state:
                self.logger.info(f"Client 0x{player_index:04X} state changed: {old_state.value} -> {new_state.value}")
            
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
    
    def transition_to_init_ready(self, player_index: int) -> bool:
        """
        Transition a client from base state to init_ready_for_initial_data state.
        
        Args:
            player_index: The player's unique index
            
        Returns:
            True if transition was successful, False otherwise
        """
        with self._state_lock:
            current_state = self._client_states.get(player_index)
            
            if current_state is None:
                self.logger.warning(f"Cannot transition unknown client 0x{player_index:04X} to init ready")
                return False
            
            if current_state != ClientState.BASE:
                self.logger.warning(f"Client 0x{player_index:04X} cannot transition to init ready from {current_state.value}")
                return False
            
            self._client_states[player_index] = ClientState.INIT_READY_FOR_INITIAL_DATA
            self.logger.info(f"Client 0x{player_index:04X} transitioned to init ready state")
            return True
    
    def transition_to_game(self, player_index: int) -> bool:
        """
        Transition a client from init_ready_for_initial_data state to in_game state.
        
        Args:
            player_index: The player's unique index
            
        Returns:
            True if transition was successful, False otherwise
        """
        with self._state_lock:
            current_state = self._client_states.get(player_index)
            
            if current_state is None:
                self.logger.warning(f"Cannot transition unknown client 0x{player_index:04X} to game")
                return False
            
            if current_state != ClientState.INIT_READY_FOR_INITIAL_DATA:
                self.logger.warning(f"Client 0x{player_index:04X} cannot transition to game from {current_state.value}")
                return False
            
            self._client_states[player_index] = ClientState.IN_GAME
            self.logger.info(f"Client 0x{player_index:04X} transitioned to game state")
            return True
    
    def get_clients_by_state(self, state: ClientState) -> list[int]:
        """
        Get all client indices that are in a specific state.
        
        Args:
            state: The state to filter by
            
        Returns:
            List of player indices in the specified state
        """
        with self._state_lock:
            return [player_index for player_index, client_state in self._client_states.items() 
                   if client_state == state]
    
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
            return sum(1 for client_state in self._client_states.values() if client_state == state) 