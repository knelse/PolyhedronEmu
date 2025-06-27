import threading
import unittest
from unittest.mock import Mock
from server.client_state_manager import client_state_manager, client_state
from server.exceptions import state_transition_exception
from unittest import TestCase
import sys
import os

sys.modules["py4godot"] = Mock()
sys.modules["py4godot.classes"] = Mock()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestClientStateManager(TestCase):
    """Test cases for client_state_manager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = Mock()
        self.state_manager = client_state_manager(self.mock_logger)
        self.player_index = 0x5000

    def test_add_client_initial_state(self):
        """Test adding a client sets initial state to BASE."""
        self.state_manager.add_client(self.player_index)

        state = self.state_manager.get_client_state(self.player_index)
        self.assertEqual(state, client_state.BASE)

        expected_msg = f"Client 0x{self.player_index:04X} added with state: base"
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
            self.player_index, client_state.IN_GAME
        )
        self.assertTrue(result)

        state = self.state_manager.get_client_state(self.player_index)
        self.assertEqual(state, client_state.IN_GAME)

        expected_msg = (
            f"Client 0x{self.player_index:04X} state changed: " f"base -> in_game"
        )
        self.mock_logger.info.assert_called_with(expected_msg)

    def test_set_client_state_same_state(self):
        """Test setting client to same state."""
        self.state_manager.add_client(self.player_index)

        result = self.state_manager.set_client_state(
            self.player_index, client_state.BASE
        )
        self.assertTrue(result)

        # Should not log a state change since it's the same state
        # Only the add_client call should have logged
        expected_msg = f"Client 0x{self.player_index:04X} added with state: base"
        self.mock_logger.info.assert_called_with(expected_msg)

    def test_set_client_state_unknown_client(self):
        """Test setting state for unknown client."""
        result = self.state_manager.set_client_state(
            self.player_index, client_state.IN_GAME
        )
        self.assertFalse(result)

        expected_msg = (
            f"Attempted to set state for unknown client " f"0x{self.player_index:04X}"
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

        # Sequential transitions: BASE -> INIT_READY -> LOGIN -> CHARACTER_SELECT
        self.state_manager.transition_state(
            player2, client_state.INIT_READY_FOR_INITIAL_DATA
        )
        self.state_manager.transition_state(
            player2, client_state.INIT_WAITING_FOR_LOGIN_DATA
        )
        self.state_manager.transition_state(
            player2, client_state.INIT_WAITING_FOR_CHARACTER_SELECT
        )

        self.state_manager.transition_state(
            player3, client_state.INIT_READY_FOR_INITIAL_DATA
        )
        self.state_manager.transition_state(
            player3, client_state.INIT_WAITING_FOR_LOGIN_DATA
        )

        base_clients = self.state_manager.get_clients_by_state(client_state.BASE)
        login_clients = self.state_manager.get_clients_by_state(
            client_state.INIT_WAITING_FOR_LOGIN_DATA
        )
        char_select_clients = self.state_manager.get_clients_by_state(
            client_state.INIT_WAITING_FOR_CHARACTER_SELECT
        )

        self.assertEqual(len(base_clients), 1)
        self.assertIn(player1, base_clients)

        self.assertEqual(len(login_clients), 1)
        self.assertIn(player3, login_clients)

        self.assertEqual(len(char_select_clients), 1)
        self.assertIn(player2, char_select_clients)

    def test_get_all_client_states(self):
        """Test getting all client states."""
        player1 = 0x5001
        player2 = 0x5002

        self.state_manager.add_client(player1)
        self.state_manager.add_client(player2)

        # Sequential transition: BASE -> INIT_READY -> LOGIN -> CHARACTER_SELECT
        self.state_manager.transition_state(
            player2, client_state.INIT_READY_FOR_INITIAL_DATA
        )
        self.state_manager.transition_state(
            player2, client_state.INIT_WAITING_FOR_LOGIN_DATA
        )
        self.state_manager.transition_state(
            player2, client_state.INIT_WAITING_FOR_CHARACTER_SELECT
        )

        all_states = self.state_manager.get_all_client_states()

        self.assertEqual(len(all_states), 2)
        self.assertEqual(all_states[player1], client_state.BASE)
        self.assertEqual(
            all_states[player2], client_state.INIT_WAITING_FOR_CHARACTER_SELECT
        )

    def test_get_client_count_by_state(self):
        """Test counting clients by state."""
        players = [0x5001, 0x5002, 0x5003, 0x5004]

        for player in players:
            self.state_manager.add_client(player)

        # Sequential transitions for different players
        self.state_manager.transition_state(
            players[1], client_state.INIT_READY_FOR_INITIAL_DATA
        )
        self.state_manager.transition_state(
            players[1], client_state.INIT_WAITING_FOR_LOGIN_DATA
        )
        self.state_manager.transition_state(
            players[1], client_state.INIT_WAITING_FOR_CHARACTER_SELECT
        )

        self.state_manager.transition_state(
            players[2], client_state.INIT_READY_FOR_INITIAL_DATA
        )
        self.state_manager.transition_state(
            players[2], client_state.INIT_WAITING_FOR_LOGIN_DATA
        )

        base_count = self.state_manager.get_client_count_by_state(client_state.BASE)
        login_count = self.state_manager.get_client_count_by_state(
            client_state.INIT_WAITING_FOR_LOGIN_DATA
        )
        char_select_count = self.state_manager.get_client_count_by_state(
            client_state.INIT_WAITING_FOR_CHARACTER_SELECT
        )

        self.assertEqual(base_count, 2)  # players[0] and players[3]
        self.assertEqual(login_count, 1)  # players[2]
        self.assertEqual(char_select_count, 1)  # players[1]

    def test_thread_safety_concurrent_operations(self):
        """Test thread safety of concurrent state operations."""
        players = list(range(0x6000, 0x6010))  # 16 players
        results = []

        def add_and_transition_client(player_index):
            try:
                self.state_manager.add_client(player_index)
                self.state_manager.transition_state(
                    player_index, client_state.INIT_READY_FOR_INITIAL_DATA
                )
                self.state_manager.transition_state(
                    player_index, client_state.INIT_WAITING_FOR_LOGIN_DATA
                )
                self.state_manager.transition_state(
                    player_index, client_state.INIT_WAITING_FOR_CHARACTER_SELECT
                )
                results.append(f"success_{player_index}")
            except Exception as e:
                results.append(f"error_{player_index}_{e}")

        threads = []
        for player in players:
            thread = threading.Thread(target=add_and_transition_client, args=(player,))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        success_count = sum(1 for r in results if r.startswith("success_"))
        self.assertEqual(success_count, len(players))

        char_select_clients = self.state_manager.get_clients_by_state(
            client_state.INIT_WAITING_FOR_CHARACTER_SELECT
        )
        self.assertEqual(len(char_select_clients), len(players))

    def test_complete_state_flow(self):
        """Test complete state flow from BASE to CHARACTER_SELECT."""
        self.state_manager.add_client(self.player_index)

        current_state = self.state_manager.get_client_state(self.player_index)
        self.assertEqual(current_state, client_state.BASE)

        # Sequential transition: BASE -> INIT_READY
        self.state_manager.transition_state(
            self.player_index, client_state.INIT_READY_FOR_INITIAL_DATA
        )
        current_state = self.state_manager.get_client_state(self.player_index)
        self.assertEqual(current_state, client_state.INIT_READY_FOR_INITIAL_DATA)

        # Sequential transition: INIT_READY -> LOGIN
        self.state_manager.transition_state(
            self.player_index, client_state.INIT_WAITING_FOR_LOGIN_DATA
        )
        current_state = self.state_manager.get_client_state(self.player_index)
        self.assertEqual(current_state, client_state.INIT_WAITING_FOR_LOGIN_DATA)

        # Sequential transition: LOGIN -> CHARACTER_SELECT
        self.state_manager.transition_state(
            self.player_index, client_state.INIT_WAITING_FOR_CHARACTER_SELECT
        )
        current_state = self.state_manager.get_client_state(self.player_index)
        self.assertEqual(current_state, client_state.INIT_WAITING_FOR_CHARACTER_SELECT)

    def test_transition_state_sequential_validation(self):
        """Test that transition_state validates sequential state progression."""
        self.state_manager.add_client(self.player_index)

        # Valid transitions: BASE(0) -> INIT_READY(1) -> LOGIN(2) -> CHARACTER_SELECT(3)

        # Test valid sequential transition: BASE -> INIT_READY
        self.state_manager.transition_state(
            self.player_index, client_state.INIT_READY_FOR_INITIAL_DATA
        )

        # Test valid sequential transition: INIT_READY -> LOGIN
        self.state_manager.transition_state(
            self.player_index, client_state.INIT_WAITING_FOR_LOGIN_DATA
        )

        # Test invalid skip ahead
        with self.assertRaises(state_transition_exception):
            self.state_manager.transition_state(self.player_index, client_state.IN_GAME)

        # Current state should still be LOGIN
        current_state = self.state_manager.get_client_state(self.player_index)
        self.assertEqual(current_state, client_state.INIT_WAITING_FOR_LOGIN_DATA)

        # Continue with valid progression
        self.state_manager.transition_state(
            self.player_index, client_state.INIT_WAITING_FOR_CHARACTER_SELECT
        )

        # Test trying to skip back
        with self.assertRaises(state_transition_exception):
            self.state_manager.transition_state(self.player_index, client_state.BASE)

    def test_transition_state_unknown_client(self):
        """Test transition for unknown client."""
        with self.assertRaises(state_transition_exception):
            self.state_manager.transition_state(self.player_index, client_state.IN_GAME)

        expected_msg = (
            f"Cannot transition unknown client " f"0x{self.player_index:04X} to in_game"
        )
        self.mock_logger.warning.assert_called_with(expected_msg)


if __name__ == "__main__":
    unittest.main()
