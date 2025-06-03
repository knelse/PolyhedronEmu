import sys
import unittest
import threading
from unittest.mock import MagicMock, patch

# Mock py4godot before importing client_handler
sys.modules['py4godot'] = MagicMock()
sys.modules['py4godot.classes'] = MagicMock()
sys.modules['py4godot.classes.Node3D'] = MagicMock()

from server.client_handler import ClientHandler  # noqa: E402
from server.logger import ServerLogger  # noqa: E402
from server.player_manager import PlayerManager  # noqa: E402
from server.packets import INIT_PACKET  # noqa: E402


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

    def send(self, data):
        if self.should_fail_send:
            raise ConnectionError("Send failed")
        self.sent_data.append(data)

    def close(self):
        self.closed = True


class TestClientHandler(unittest.TestCase):
    """Test ClientHandler functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = MagicMock(spec=ServerLogger)
        self.mock_player_manager = MagicMock(spec=PlayerManager)
        self.mock_parent_node = MockNode3D()

        self.client_handler = ClientHandler(
            self.mock_logger,
            self.mock_player_manager,
            self.mock_parent_node
        )

    def test_initialization(self):
        """Test ClientHandler initialization."""
        self.assertFalse(self.client_handler.is_running)
        self.assertEqual(len(self.client_handler.client_nodes), 0)
        self.assertIsNotNone(self.client_handler.state_manager)

    @patch('socket.socket')
    def test_start_handling_accept_connection(self, mock_socket_class):
        """Test handling new client connection."""
        # Setup mocks
        mock_server_socket = MagicMock()
        mock_client_socket = MockSocket()
        address = ("127.0.0.1", 12345)
        player_index = 0x5000

        mock_server_socket.accept.return_value = (mock_client_socket, address)
        result = player_index
        self.mock_player_manager.get_next_player_index.return_value = result

        # Mock the is_running callback to stop after one iteration
        call_count = 0

        def mock_is_running():
            nonlocal call_count
            call_count += 1
            return call_count == 1

        # Start handling in a thread
        handler_thread = threading.Thread(
            target=self.client_handler.start_handling,
            args=(mock_server_socket, mock_is_running)
        )
        handler_thread.start()
        handler_thread.join(timeout=1)

        # Verify socket operations
        mock_server_socket.accept.assert_called_once()

        # Verify player management
        self.mock_player_manager.get_next_player_index.assert_called_once()
        expected_call = (player_index, address)
        self.mock_player_manager.add_player.assert_called_once_with(
            *expected_call)

        # Verify initialization packet was sent
        self.assertIn(INIT_PACKET, mock_client_socket.sent_data)

        # Verify logging
        expected_msg = (f"Sent init packet to player 0x{player_index:04X}: "
                        f"{INIT_PACKET.hex()}")
        self.mock_logger.debug.assert_any_call(expected_msg)

    def test_reject_connection_max_players(self):
        """Test rejecting connection when max players reached."""
        mock_server_socket = MagicMock()
        mock_client_socket = MockSocket()
        address = ("127.0.0.1", 12345)

        # Max players
        result = None
        self.mock_player_manager.get_next_player_index.return_value = result

        call_count = 0

        def mock_is_running():
            nonlocal call_count
            call_count += 1
            return call_count == 1

        handler_thread = threading.Thread(
            target=self.client_handler.start_handling,
            args=(mock_server_socket, mock_is_running)
        )
        handler_thread.start()
        handler_thread.join(timeout=1)

        # Verify connection was rejected
        self.assertTrue(mock_client_socket.closed)
        expected_msg = (f"Rejecting connection from {address}: "
                        f"Maximum players reached")
        self.mock_logger.warning.assert_called_with(expected_msg)

    def test_init_packet_send_failure(self):
        """Test handling of init packet send failure."""
        mock_server_socket = MagicMock()
        mock_client_socket = MockSocket()
        mock_client_socket.should_fail_send = True
        address = ("127.0.0.1", 12345)
        player_index = 0x5000

        mock_server_socket.accept.return_value = (mock_client_socket, address)
        result = player_index
        self.mock_player_manager.get_next_player_index.return_value = result

        call_count = 0

        def mock_is_running():
            nonlocal call_count
            call_count += 1
            return call_count == 1

        handler_thread = threading.Thread(
            target=self.client_handler.start_handling,
            args=(mock_server_socket, mock_is_running)
        )
        handler_thread.start()
        handler_thread.join(timeout=1)

        # Verify cleanup was performed
        self.mock_player_manager.remove_player.assert_called_with(player_index)
        self.mock_logger.log_exception.assert_called()

    def test_node_creation_and_naming(self):
        """Test that client nodes are created with correct names."""
        player_index = 0x5000
        expected_name = f"Player_{player_index:04X}"

        # Simulate connection acceptance
        with patch('server.client_handler.Node3D') as mock_node_class:
            mock_node = MockNode3D()
            mock_node_class.return_value = mock_node

            mock_server_socket = MagicMock()
            mock_client_socket = MockSocket()
            address = ("127.0.0.1", 12345)

            accept_result = (mock_client_socket, address)
            mock_server_socket.accept.return_value = accept_result
            mgr = self.mock_player_manager
            mgr.get_next_player_index.return_value = player_index

            call_count = 0

            def mock_is_running():
                nonlocal call_count
                call_count += 1
                return call_count == 1

            handler_thread = threading.Thread(
                target=self.client_handler.start_handling,
                args=(mock_server_socket, mock_is_running)
            )
            handler_thread.start()
            handler_thread.join(timeout=1)

            # Verify node was created and named correctly
            self.assertEqual(mock_node.name, expected_name)

    def test_handle_client_echo(self):
        """Test client message handling (echo functionality)."""
        mock_socket = MagicMock()
        address = ("127.0.0.1", 12345)
        player_index = 0x5000
        test_data = b"test message"

        # Mock recv to return data once, then empty (disconnect)
        mock_socket.recv.side_effect = [test_data, b""]

        def mock_is_running():
            return True

        # Handle client in thread
        client_thread = threading.Thread(
            target=self.client_handler.handle_client,
            args=(mock_socket, address, player_index, mock_is_running)
        )
        client_thread.start()
        client_thread.join(timeout=1)

        # Verify echo behavior
        mock_socket.send.assert_called_with(test_data)

        # Verify logging
        self.mock_logger.debug.assert_any_call(
            f"Received from player 0x{player_index:04X}: {test_data.hex()}"
        )

    def test_client_disconnect_cleanup(self):
        """Test cleanup when client disconnects."""
        mock_socket = MagicMock()
        address = ("127.0.0.1", 12345)
        player_index = 0x5000

        # Add a mock node to client_nodes
        mock_node = MockNode3D()
        self.client_handler.client_nodes[player_index] = mock_node

        # Mock recv to return empty (immediate disconnect)
        mock_socket.recv.return_value = b""

        def mock_is_running():
            return True

        client_thread = threading.Thread(
            target=self.client_handler.handle_client,
            args=(mock_socket, address, player_index, mock_is_running)
        )
        client_thread.start()
        client_thread.join(timeout=1)

        # Verify cleanup
        mock_socket.close.assert_called()
        self.mock_player_manager.remove_player.assert_called_with(player_index)
        self.assertTrue(mock_node.freed)
        self.assertNotIn(player_index, self.client_handler.client_nodes)

    def test_stop_handling(self):
        """Test stopping the client handler."""
        # Add some mock nodes
        player1 = 0x5001
        player2 = 0x5002
        mock_node1 = MockNode3D()
        mock_node2 = MockNode3D()

        self.client_handler.client_nodes[player1] = mock_node1
        self.client_handler.client_nodes[player2] = mock_node2

        self.client_handler.stop_handling()

        # Verify is_running is set to False
        self.assertFalse(self.client_handler.is_running)

        # Verify all nodes are cleaned up
        self.assertTrue(mock_node1.freed)
        self.assertTrue(mock_node2.freed)
        self.assertEqual(len(self.client_handler.client_nodes), 0)

    def test_get_client_node(self):
        """Test getting client node by player index."""
        player_index = 0x5000
        mock_node = MockNode3D()

        # Add node
        self.client_handler.client_nodes[player_index] = mock_node

        # Test retrieval
        retrieved_node = self.client_handler.get_client_node(player_index)
        self.assertIs(retrieved_node, mock_node)

        # Test non-existent node
        non_existent_node = self.client_handler.get_client_node(99999)
        self.assertIsNone(non_existent_node)

    def test_state_manager_integration(self):
        """Test integration with state manager."""
        player_index = 0x5000

        # Verify state manager is created
        self.assertIsNotNone(self.client_handler.state_manager)

        # Test state transitions through mocked connection
        state_mgr = self.client_handler.state_manager
        with patch.object(state_mgr, 'add_client') as mock_add:
            transition_method = 'transition_to_init_ready'
            with patch.object(state_mgr, transition_method) as mock_transition:
                mock_transition.return_value = True

                mock_server_socket = MagicMock()
                mock_client_socket = MockSocket()
                address = ("127.0.0.1", 12345)

                accept_result = (mock_client_socket, address)
                mock_server_socket.accept.return_value = accept_result
                mgr = self.mock_player_manager
                mgr.get_next_player_index.return_value = player_index

                call_count = 0

                def mock_is_running():
                    nonlocal call_count
                    call_count += 1
                    return call_count == 1

                handler_thread = threading.Thread(
                    target=self.client_handler.start_handling,
                    args=(mock_server_socket, mock_is_running)
                )
                handler_thread.start()
                handler_thread.join(timeout=1)

                # Verify state manager calls
                mock_add.assert_called_with(player_index)
                mock_transition.assert_called_with(player_index)


if __name__ == '__main__':
    unittest.main()
