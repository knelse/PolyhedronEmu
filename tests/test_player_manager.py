import unittest
import threading
import time
from unittest.mock import MagicMock
from server.player_manager import PlayerManager

class TestPlayerManager(unittest.TestCase):
    """Test PlayerManager functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.player_manager = PlayerManager()

    def test_initial_state(self):
        """Test initial state of PlayerManager."""
        self.assertEqual(self.player_manager.get_player_count(), 0)
        self.assertEqual(self.player_manager.get_all_players(), {})

    def test_get_next_player_index_initial(self):
        """Test getting the first player index."""
        index = self.player_manager.get_next_player_index()
        self.assertEqual(index, PlayerManager.INITIAL_PLAYER_INDEX)

    def test_get_next_player_index_sequential(self):
        """Test getting sequential player indices."""
        index1 = self.player_manager.get_next_player_index()
        index2 = self.player_manager.get_next_player_index()
        index3 = self.player_manager.get_next_player_index()
        
        self.assertEqual(index1, PlayerManager.INITIAL_PLAYER_INDEX)
        self.assertEqual(index2, PlayerManager.INITIAL_PLAYER_INDEX + 1)
        self.assertEqual(index3, PlayerManager.INITIAL_PLAYER_INDEX + 2)

    def test_add_player(self):
        """Test adding a player."""
        address = ("127.0.0.1", 12345)
        player_index = self.player_manager.get_next_player_index()
        
        self.player_manager.add_player(player_index, address)
        
        self.assertEqual(self.player_manager.get_player_count(), 1)
        player_info = self.player_manager.get_player_info(player_index)
        self.assertIsNotNone(player_info)
        self.assertEqual(player_info['address'], address)

    def test_remove_player(self):
        """Test removing a player."""
        address = ("127.0.0.1", 12345)
        player_index = self.player_manager.get_next_player_index()
        
        self.player_manager.add_player(player_index, address)
        self.assertEqual(self.player_manager.get_player_count(), 1)
        
        self.player_manager.remove_player(player_index)
        self.assertEqual(self.player_manager.get_player_count(), 0)
        self.assertIsNone(self.player_manager.get_player_info(player_index))

    def test_index_recycling(self):
        """Test that removed player indices are recycled."""
        address1 = ("127.0.0.1", 12345)
        address2 = ("127.0.0.1", 12346)
        
        # Get first index and add player
        index1 = self.player_manager.get_next_player_index()
        self.player_manager.add_player(index1, address1)
        
        # Get second index and add player
        index2 = self.player_manager.get_next_player_index()
        self.player_manager.add_player(index2, address2)
        
        # Remove first player
        self.player_manager.remove_player(index1)
        
        # Get next index - should reuse index1
        recycled_index = self.player_manager.get_next_player_index()
        self.assertEqual(recycled_index, index1)

    def test_get_player_info_nonexistent(self):
        """Test getting info for non-existent player."""
        info = self.player_manager.get_player_info(99999)
        self.assertIsNone(info)

    def test_remove_nonexistent_player(self):
        """Test removing a non-existent player doesn't cause errors."""
        initial_count = self.player_manager.get_player_count()
        self.player_manager.remove_player(99999)
        self.assertEqual(self.player_manager.get_player_count(), initial_count)

    def test_get_all_players(self):
        """Test getting all players."""
        address1 = ("127.0.0.1", 12345)
        address2 = ("127.0.0.1", 12346)
        
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

    def test_max_players_reached(self):
        """Test behavior when maximum players is reached."""
        # Temporarily set a lower max for testing
        original_max = PlayerManager.MAX_PLAYER_INDEX
        PlayerManager.MAX_PLAYER_INDEX = PlayerManager.INITIAL_PLAYER_INDEX + 2
        
        try:
            # Create new player manager with modified max
            pm = PlayerManager()
            
            index1 = pm.get_next_player_index()
            index2 = pm.get_next_player_index()
            index3 = pm.get_next_player_index()
            index4 = pm.get_next_player_index()  # Should be None
            
            self.assertIsNotNone(index1)
            self.assertIsNotNone(index2)
            self.assertIsNotNone(index3)
            self.assertIsNone(index4)
        finally:
            PlayerManager.MAX_PLAYER_INDEX = original_max

    def test_thread_safety_concurrent_index_generation(self):
        """Test thread safety of concurrent index generation."""
        indices = []
        threads = []
        
        def get_index():
            index = self.player_manager.get_next_player_index()
            indices.append(index)
        
        # Create multiple threads to get indices concurrently
        for _ in range(10):
            thread = threading.Thread(target=get_index)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all indices are unique
        self.assertEqual(len(indices), 10)
        self.assertEqual(len(set(indices)), 10)  # All unique

    def test_thread_safety_concurrent_add_remove(self):
        """Test thread safety of concurrent add/remove operations."""
        results = []
        
        def add_remove_player(player_id):
            try:
                address = ("127.0.0.1", 12345 + player_id)
                index = self.player_manager.get_next_player_index()
                
                if index is not None:
                    self.player_manager.add_player(index, address)
                    time.sleep(0.01)  # Small delay to encourage race conditions
                    self.player_manager.remove_player(index)
                    results.append(f"success_{player_id}")
                else:
                    results.append(f"no_index_{player_id}")
            except Exception as e:
                results.append(f"error_{player_id}_{e}")
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=add_remove_player, args=(i,))
            threads.append(thread)
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All operations should succeed
        success_count = sum(1 for r in results if r.startswith("success_"))
        self.assertEqual(success_count, 5)
        
        # Final state should be empty
        self.assertEqual(self.player_manager.get_player_count(), 0)

    def test_player_info_structure(self):
        """Test the structure of player info."""
        address = ("192.168.1.1", 54321)
        index = self.player_manager.get_next_player_index()
        
        self.player_manager.add_player(index, address)
        info = self.player_manager.get_player_info(index)
        
        self.assertIn('address', info)
        self.assertIn('connected_at', info)
        self.assertEqual(info['address'], address)
        self.assertIsInstance(info['connected_at'], int)

    def test_index_recycling_multiple_times(self):
        """Test that indices can be recycled multiple times."""
        address = ("127.0.0.1", 12345)
        
        # Get an index and use it
        index1 = self.player_manager.get_next_player_index()
        self.player_manager.add_player(index1, address)
        self.player_manager.remove_player(index1)
        
        # Get another index (should get a new one)
        index2 = self.player_manager.get_next_player_index()
        self.player_manager.add_player(index2, address)
        self.player_manager.remove_player(index2)
        
        # Now get an index again - should recycle one of the previous ones
        recycled_index = self.player_manager.get_next_player_index()
        self.assertIn(recycled_index, [index1, index2])

if __name__ == '__main__':
    unittest.main() 