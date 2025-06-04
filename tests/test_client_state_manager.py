import threading
import unittest
from unittest.mock import Mock
from server.client_state_manager import ClientStateManager, ClientState
from unittest import TestCase
import sys
import os

sys.modules['py4godot'] = Mock()
sys.modules['py4godot.classes'] = Mock()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestClientStateManager(TestCase):
    """Test cases for ClientStateManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = Mock()
        self.state_manager = ClientStateManager(self.mock_logger)
        self.player_index = 0x5000

    def test_add_client_initial_state(self):
        """Test adding a client sets initial state to BASE."""
        self.state_manager.add_client(self.player_index)

        state = self.state_manager.get_client_state(self.player_index)
        self.assertEqual(state, ClientState.BASE)

        expected_msg = (
            f"Client 0x{self.player_index:04X} added with state: base"
        )
        self.mock_logger.info.assert_called_with(expected_msg)

    def test_remove_client(self):
        """Test removing a client."""
        self.state_manager.add_client(self.player_index)

        self.state_manager.remove_client(self.player_index)

        state = self.state_manager.get_client_state(self.player_index)
        self.assertIsNone(state)

        expected_msg = (
            f"Client 0x{self.player_index:04X} removed from state tracking "
            f"(was in base)"
        )
        self.mock_logger.info.assert_called_with(expected_msg)

    def test_remove_nonexistent_client(self):
        """Test removing a client that doesn't exist."""
        self.state_manager.remove_client(self.player_index)

    def test_set_client_state_success(self):
        """Test setting client state successfully."""
        self.state_manager.add_client(self.player_index)

        result = self.state_manager.set_client_state(
            self.player_index, ClientState.IN_GAME
        )
        self.assertTrue(result)

        state = self.state_manager.get_client_state(self.player_index)
        self.assertEqual(state, ClientState.IN_GAME)

        expected_msg = (
            f"Client 0x{self.player_index:04X} state changed: "
            f"base -> in_game"
        )
        self.mock_logger.info.assert_called_with(expected_msg)

    def test_set_client_state_same_state(self):
        """Test setting client to same state."""
        self.state_manager.add_client(self.player_index)

        result = self.state_manager.set_client_state(
            self.player_index, ClientState.BASE
        )
        self.assertTrue(result)

        # Should not log a state change since it's the same state
        # Only the add_client call should have logged
        expected_msg = (
            f"Client 0x{self.player_index:04X} added with state: base"
        )
        self.mock_logger.info.assert_called_with(expected_msg)

    def test_set_client_state_unknown_client(self):
        """Test setting state for unknown client."""
        result = self.state_manager.set_client_state(
            self.player_index, ClientState.IN_GAME
        )
        self.assertFalse(result)

        expected_msg = (
            f"Attempted to set state for unknown client "
            f"0x{self.player_index:04X}"
        )
        self.mock_logger.warning.assert_called_with(expected_msg)

    def test_get_clients_by_state(self):
        """Test getting clients by state."""
        player1 = 0x5001
        player2 = 0x5002
        player3 = 0x5003

        self.state_manager.add_client(player1)
        self.state_manager.add_client(player2)
        self.state_manager.add_client(player3)

        self.state_manager.transition_to_init_ready(player2)
        self.state_manager.transition_to_init_ready(player3)
        self.state_manager.transition_to_game(player3)

        base_clients = self.state_manager.get_clients_by_state(
            ClientState.BASE
        )
        init_clients = self.state_manager.get_clients_by_state(
            ClientState.INIT_READY_FOR_INITIAL_DATA
        )
        game_clients = self.state_manager.get_clients_by_state(
            ClientState.IN_GAME
        )

        self.assertEqual(len(base_clients), 1)
        self.assertIn(player1, base_clients)

        self.assertEqual(len(init_clients), 1)
        self.assertIn(player2, init_clients)

        self.assertEqual(len(game_clients), 1)
        self.assertIn(player3, game_clients)

    def test_get_all_client_states(self):
        """Test getting all client states."""
        player1 = 0x5001
        player2 = 0x5002

        self.state_manager.add_client(player1)
        self.state_manager.add_client(player2)
        self.state_manager.transition_to_init_ready(player2)

        all_states = self.state_manager.get_all_client_states()

        self.assertEqual(len(all_states), 2)
        self.assertEqual(all_states[player1], ClientState.BASE)
        self.assertEqual(
            all_states[player2], ClientState.INIT_READY_FOR_INITIAL_DATA
        )

    def test_get_client_count_by_state(self):
        """Test counting clients by state."""
        players = [0x5001, 0x5002, 0x5003, 0x5004]

        for player in players:
            self.state_manager.add_client(player)

        self.state_manager.transition_to_init_ready(players[1])
        self.state_manager.transition_to_init_ready(players[2])
        self.state_manager.transition_to_game(players[2])

        base_count = self.state_manager.get_client_count_by_state(
            ClientState.BASE
        )
        init_count = self.state_manager.get_client_count_by_state(
            ClientState.INIT_READY_FOR_INITIAL_DATA
        )
        game_count = self.state_manager.get_client_count_by_state(
            ClientState.IN_GAME
        )

        self.assertEqual(base_count, 2)  # players[0] and players[3]
        self.assertEqual(init_count, 1)  # players[1]
        self.assertEqual(game_count, 1)  # players[2]

    def test_thread_safety_concurrent_operations(self):
        """Test thread safety of concurrent state operations."""
        players = list(range(0x6000, 0x6010))  # 16 players
        results = []

        def add_and_transition_client(player_index):
            try:
                self.state_manager.add_client(player_index)
                success1 = self.state_manager.transition_to_init_ready(
                    player_index
                )
                success2 = self.state_manager.transition_to_game(player_index)
                results.append(f"success_{player_index}_{success1}_{success2}")
            except Exception as e:
                results.append(f"error_{player_index}_{e}")

        threads = []
        for player in players:
            thread = threading.Thread(
                target=add_and_transition_client, args=(player,)
            )
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        success_count = sum(
            1 for r in results
            if r.startswith("success_") and "True_True" in r
        )
        self.assertEqual(success_count, len(players))

        game_clients = self.state_manager.get_clients_by_state(
            ClientState.IN_GAME
        )
        self.assertEqual(len(game_clients), len(players))

    def test_complete_state_flow(self):
        """Test complete state flow from BASE to IN_GAME."""
        self.state_manager.add_client(self.player_index)

        current_state = self.state_manager.get_client_state(
            self.player_index
        )
        self.assertEqual(current_state, ClientState.BASE)

        result = self.state_manager.transition_to_init_ready(
            self.player_index
        )
        self.assertTrue(result)
        current_state = self.state_manager.get_client_state(
            self.player_index
        )
        expected_state = ClientState.INIT_READY_FOR_INITIAL_DATA
        self.assertEqual(current_state, expected_state)

        result = self.state_manager.transition_to_game(self.player_index)
        self.assertTrue(result)
        current_state = self.state_manager.get_client_state(
            self.player_index
        )
        self.assertEqual(current_state, ClientState.IN_GAME)


if __name__ == '__main__':
    unittest.main()
