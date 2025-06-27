import sys
import socket
import unittest
import threading
from unittest.mock import MagicMock, patch
from server.client_pre_ingame_handler import client_pre_ingame_handler
from server.logger import server_logger
from server.player_manager import player_manager

sys.modules["py4godot"] = MagicMock()
sys.modules["py4godot.classes"] = MagicMock()
sys.modules["py4godot.classes.Node3D"] = MagicMock()


class MockNode3D:
    """Mock Node3D for testing."""

    def __init__(self):
        self.name = ""
        self.children = []
        self.freed = False

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def call_deferred(self, method, *args):
        if method == "add_child":
            self.children.append(args[0])
        elif method == "queue_free":
            self.freed = True


class MockSocket:
    """Mock socket for testing."""

    def __init__(self):
        self.sent_data = []
        self.closed = False
        self.should_fail_send = False
        self.recv_data = b""
        self.timeout_set = False

    def send(self, data):
        if self.should_fail_send:
            raise ConnectionError("Send failed")
        self.sent_data.append(data)
        return len(data)

    def recv(self, size):
        if self.recv_data:
            data = self.recv_data
            self.recv_data = b""
            return data
        return b""

    def settimeout(self, timeout):
        self.timeout_set = True

    def close(self):
        self.closed = True

    def accept(self):
        # For server socket mock
        return MockSocket(), ("127.0.0.1", 12345)


class TestClientPreIngameHandler(unittest.TestCase):
    """Test client_pre_ingame_handler functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = MagicMock(spec=server_logger)
        self.mock_player_manager = MagicMock(spec=player_manager)
        self.mock_parent_node = MockNode3D()

        # Add missing methods to player manager mock
        self.mock_player_manager.get_next_player_index = MagicMock()
        self.mock_player_manager.reserve_index = MagicMock()
        self.mock_player_manager.release_index = MagicMock()
        self.mock_player_manager.release_all_indices = MagicMock()

        self.client_handler = client_pre_ingame_handler(
            self.mock_logger, self.mock_player_manager, self.mock_parent_node
        )

        # Add missing methods to state manager mock
        self.client_handler.state_manager.add_client = MagicMock()
        self.client_handler.state_manager.cleanup_client = MagicMock()
        self.client_handler.state_manager.cleanup_all_clients = MagicMock()
        self.client_handler.state_manager.transition_state = MagicMock()

    def test_initialization(self):
        """Test client_pre_ingame_handler initialization."""
        self.assertIsNotNone(self.client_handler.logger)
        self.assertIsNotNone(self.client_handler.player_manager)
        self.assertIsNotNone(self.client_handler.parent_node)
        self.assertIsNotNone(self.client_handler.state_manager)
        self.assertIsNotNone(self.client_handler.character_db)

        # Check pipeline handlers are initialized
        self.assertIsNotNone(self.client_handler.server_credentials_handler)
        self.assertIsNotNone(self.client_handler.login_handler)
        self.assertIsNotNone(self.client_handler.auth_handler)
        self.assertIsNotNone(self.client_handler.character_data_handler)
        self.assertIsNotNone(self.client_handler.enter_game_world_handler)

    def test_start_handling_no_connections(self):
        """Test start_handling when no connections come in."""
        mock_server_socket = MagicMock()
        mock_server_socket.accept.side_effect = [
            socket.timeout(),  # First call times out
            Exception("Stop test"),  # Second call raises exception to stop
        ]

        call_count = 0

        def mock_is_running():
            nonlocal call_count
            call_count += 1
            return call_count <= 2  # Run twice then stop

        # This should not hang
        try:
            self.client_handler.start_handling(mock_server_socket, mock_is_running)
        except Exception:
            pass  # Expected to stop with exception

        # Verify it logged the start message
        self.assertTrue(self.mock_logger.info.called)

    @patch(
        "server.client_pre_ingame_handler.server_credentials_handler.send_init_and_credentials"
    )
    def test_handle_new_client_no_available_slots(self, mock_send_creds):
        """Test handling new client when no player slots available."""
        mock_client_socket = MockSocket()
        address = ("127.0.0.1", 12345)

        # Mock no available slots
        self.mock_player_manager.get_next_player_index.return_value = None

        def mock_is_running():
            return True

        # This should not hang
        self.client_handler._handle_new_client(
            mock_client_socket, address, mock_is_running
        )

        # Verify socket was closed
        self.assertTrue(mock_client_socket.closed)

        # Verify warning was logged
        self.mock_logger.warning.assert_called_with(
            f"No available player slots for {address}"
        )

        # Verify credentials were not sent
        mock_send_creds.assert_not_called()

    @patch(
        "server.client_pre_ingame_handler.server_credentials_handler.send_init_and_credentials"
    )
    def test_handle_new_client_credentials_failure(self, mock_send_creds):
        """Test handling new client when credentials sending fails."""
        from server.enter_game_world_pipeline.exceptions import (
            server_credentials_exception,
        )

        mock_client_socket = MockSocket()
        address = ("127.0.0.1", 12345)
        player_index = 0x5000

        # Mock available slot
        self.mock_player_manager.get_next_player_index.return_value = player_index

        # Mock credentials failure
        mock_send_creds.side_effect = server_credentials_exception(
            "Failed to send credentials"
        )

        def mock_is_running():
            return True

        # This should not hang
        self.client_handler._handle_new_client(
            mock_client_socket, address, mock_is_running
        )

        # Verify basic setup occurred
        self.mock_player_manager.reserve_index.assert_called_with(player_index)

        # For now, just verify that the method completed without hanging
        # The actual functionality test can be more complex later
        self.mock_player_manager.release_index.assert_called_with(player_index)

    def test_cleanup_client(self):
        """Test client cleanup functionality."""
        mock_client_socket = MockSocket()
        player_index = 0x5000

        # Mock thread tracking
        thread_id = threading.current_thread().ident
        with self.client_handler._threads_lock:
            self.client_handler._client_threads[thread_id] = {
                "thread": threading.current_thread(),
                "address": ("127.0.0.1", 12345),
                "player_index": player_index,
            }

        # Call cleanup
        self.client_handler._cleanup_client(mock_client_socket, player_index)

        # Verify socket was closed
        self.assertTrue(mock_client_socket.closed)

        # Verify player manager cleanup
        self.mock_player_manager.release_index.assert_called_with(player_index)

        # Verify state manager cleanup
        self.client_handler.state_manager.cleanup_client.assert_called_with(
            player_index
        )

        # Verify thread was removed
        with self.client_handler._threads_lock:
            self.assertNotIn(thread_id, self.client_handler._client_threads)

    def test_get_client_node(self):
        """Test getting client node."""
        player_index = 0x5000

        # The current implementation just returns parent_node
        result = self.client_handler.get_client_node(player_index)
        self.assertEqual(result, self.mock_parent_node)

    def test_get_active_client_count_empty(self):
        """Test getting active client count when no clients."""
        count = self.client_handler.get_active_client_count()
        self.assertEqual(count, 0)

    def test_get_active_client_count_with_clients(self):
        """Test getting active client count with active clients."""
        # Mock some active threads
        mock_thread1 = MagicMock()
        mock_thread1.is_alive.return_value = True
        mock_thread2 = MagicMock()
        mock_thread2.is_alive.return_value = False  # Dead thread

        with self.client_handler._threads_lock:
            self.client_handler._client_threads[1] = {
                "thread": mock_thread1,
                "address": ("127.0.0.1", 12345),
                "player_index": 0x5000,
            }
            self.client_handler._client_threads[2] = {
                "thread": mock_thread2,
                "address": ("127.0.0.1", 12346),
                "player_index": 0x5001,
            }

        count = self.client_handler.get_active_client_count()
        self.assertEqual(count, 1)  # Only one alive thread

    def test_get_client_thread_info(self):
        """Test getting client thread information."""
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True

        with self.client_handler._threads_lock:
            self.client_handler._client_threads[123] = {
                "thread": mock_thread,
                "address": ("127.0.0.1", 12345),
                "player_index": 0x5000,
            }

        info = self.client_handler.get_client_thread_info()

        self.assertIn(123, info)
        self.assertEqual(info[123]["address"], ("127.0.0.1", 12345))
        self.assertEqual(info[123]["player_index"], 0x5000)
        self.assertTrue(info[123]["is_alive"])

    def test_stop_handling(self):
        """Test stopping the client handler."""
        # Mock some threads
        mock_thread1 = MagicMock()
        mock_thread2 = MagicMock()

        with self.client_handler._threads_lock:
            self.client_handler._client_threads[1] = {
                "thread": mock_thread1,
                "address": ("127.0.0.1", 12345),
                "player_index": 0x5000,
            }
            self.client_handler._client_threads[2] = {
                "thread": mock_thread2,
                "address": ("127.0.0.1", 12346),
                "player_index": 0x5001,
            }

        # Call stop_handling
        self.client_handler.stop_handling()

        # Verify threads were joined
        mock_thread1.join.assert_called_with(timeout=1.0)
        mock_thread2.join.assert_called_with(timeout=1.0)

        # Verify threads were cleared
        with self.client_handler._threads_lock:
            self.assertEqual(len(self.client_handler._client_threads), 0)

        # Verify cleanup methods were called
        self.client_handler.state_manager.cleanup_all_clients.assert_called_once()
        self.mock_player_manager.release_all_indices.assert_called_once()


if __name__ == "__main__":
    unittest.main()
