import unittest
from server.player_manager import player_manager


class TestPlayerManager(unittest.TestCase):
    """Test player_manager functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.player_manager = player_manager()

    def test_initial_state(self):
        """Test that player_manager starts in a clean state."""
        self.assertEqual(self.player_manager.get_player_count(), 0)
        self.assertEqual(len(self.player_manager.get_all_players()), 0)

    def test_add_player(self):
        """Test adding a player."""
        player_index = 0x5000
        address = ("192.168.1.1", 12345)

        self.player_manager.add_player(player_index, address)

        self.assertEqual(self.player_manager.get_player_count(), 1)
        player_info = self.player_manager.get_player_info(player_index)
        self.assertIsNotNone(player_info)
        self.assertEqual(player_info['address'], address)

    def test_remove_player(self):
        """Test removing a player."""
        player_index = 0x5000
        address = ("192.168.1.1", 12345)

        self.player_manager.add_player(player_index, address)
        self.assertEqual(self.player_manager.get_player_count(), 1)

        self.player_manager.remove_player(player_index)
        self.assertEqual(self.player_manager.get_player_count(), 0)
        self.assertIsNone(self.player_manager.get_player_info(player_index))

    def test_index_reuse_after_removal(self):
        """Test that indices are reused after player removal."""
        address = ("192.168.1.1", 12345)

        first_index = self.player_manager.get_next_player_index()
        self.player_manager.add_player(first_index, address)

        second_index = self.player_manager.get_next_player_index()
        self.assertEqual(second_index, first_index + 1)

        self.player_manager.remove_player(first_index)

        recycled_index = self.player_manager.get_next_player_index()
        self.assertEqual(recycled_index, first_index)

    def test_max_players_limit(self):
        """Test behavior when reaching maximum player limit."""
        original_next = self.player_manager._next_player_index
        self.player_manager._next_player_index = (
            player_manager.MAX_PLAYER_INDEX + 1)

        self.assertIsNone(self.player_manager.get_next_player_index())

        self.player_manager._next_player_index = original_next

    def test_get_player_info_nonexistent(self):
        """Test getting info for non-existent player."""
        self.assertIsNone(self.player_manager.get_player_info(99999))

    def test_remove_nonexistent_player(self):
        """Test removing a non-existent player (should not crash)."""
        self.player_manager.remove_player(99999)
        self.assertEqual(self.player_manager.get_player_count(), 0)

    def test_get_all_players(self):
        """Test getting all players information."""
        address1 = ("192.168.1.1", 12345)
        address2 = ("192.168.1.2", 12346)
        index1 = self.player_manager.get_next_player_index()
        index2 = self.player_manager.get_next_player_index()

        self.player_manager.add_player(index1, address1)
        self.player_manager.add_player(index2, address2)

        all_players = self.player_manager.get_all_players()
        self.assertEqual(len(all_players), 2)
        self.assertIn(index1, all_players)
        self.assertIn(index2, all_players)
        self.assertEqual(all_players[index1]['address'], address1)
        self.assertEqual(all_players[index2]['address'], address2)

    def test_thread_safety_get_next_index(self):
        """Test thread safety of get_next_player_index method."""
        import threading

        indices = []

        def get_index():
            index = self.player_manager.get_next_player_index()
            if index is not None:
                indices.append(index)

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=get_index)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        self.assertEqual(len(indices), len(set(indices)))


if __name__ == '__main__':
    unittest.main()
