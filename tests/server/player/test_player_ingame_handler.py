import unittest
from unittest.mock import Mock, MagicMock, patch
import socket
import sys
import os

# Must mock py4godot before importing modules that depend on it
sys.modules["py4godot"] = Mock()
sys.modules["py4godot.classes"] = Mock()


# Create proper mocks for gdclass and Node3D
def mock_gdclass(cls):
    """Mock gdclass decorator that just returns the class unchanged."""
    return cls


class MockNode3D:
    """Mock Node3D class for testing."""

    def __init__(self):
        self.children = {}

    def get_node(self, path):
        return self.children.get(path)


mock_node3d_module = Mock()
mock_node3d_module.Node3D = MockNode3D

sys.modules["py4godot.classes"].gdclass = mock_gdclass
sys.modules["py4godot.classes.Node3D"] = mock_node3d_module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# Import after mocking py4godot dependencies  # noqa: E402
from server.player.player_ingame_handler import player_ingame_handler  # noqa: E402
from server.logger import server_logger  # noqa: E402
from server.player_manager import player_manager  # noqa: E402
from server.client_state_manager import client_state_manager  # noqa: E402


class MockSocket:
    """Mock socket for testing."""

    def __init__(self):
        self.closed = False
        self.sent_data = []
        self.receive_data = []
        self.receive_index = 0

    def send(self, data):
        if self.closed:
            raise ConnectionResetError("Socket is closed")
        self.sent_data.append(data)

    def recv(self, size):
        if self.closed:
            raise ConnectionResetError("Socket is closed")
        if self.receive_index < len(self.receive_data):
            data = self.receive_data[self.receive_index]
            self.receive_index += 1
            return data
        raise socket.timeout("No more data")

    def close(self):
        self.closed = True

    def settimeout(self, timeout):
        pass


class TestPlayerIngameHandler(unittest.TestCase):
    """Test cases for player_ingame_handler class."""

    def setUp(self):
        """Set up test fixtures."""
        self.handler = player_ingame_handler()
        # Set up children dict for get_node functionality
        self.handler.children = {}
        self.mock_logger = MagicMock(spec=server_logger)
        self.mock_player_manager = MagicMock(spec=player_manager)
        self.mock_state_manager = MagicMock(spec=client_state_manager)
        self.mock_socket = MockSocket()
        self.player_index = 0x5000
        self.user_id = "testuser"
        self.is_running_flag = True

        def mock_is_running():
            return self.is_running_flag

        self.mock_is_running = mock_is_running

    def test_initialization(self):
        """Test player_ingame_handler initialization."""
        self.assertIsNotNone(self.handler)
        self.assertIsNone(self.handler.client_socket)
        self.assertIsNone(self.handler.player_index)
        self.assertIsNone(self.handler.logger)
        self.assertIsNone(self.handler.state_manager)
        self.assertIsNone(self.handler.user_id)
        self.assertIsNone(self.handler.player_manager)
        self.assertIsNone(self.handler.is_running)
        self.assertIsNone(self.handler.client_thread)
        self.assertFalse(self.handler._cleanup_done)

    def test_field_assignment(self):
        """Test direct field assignment."""
        # Assign fields directly
        self.handler.client_socket = self.mock_socket
        self.handler.player_index = self.player_index
        self.handler.logger = self.mock_logger
        self.handler.state_manager = self.mock_state_manager
        self.handler.user_id = self.user_id
        self.handler.player_manager = self.mock_player_manager
        self.handler.is_running = self.mock_is_running

        # Verify assignments
        self.assertEqual(self.handler.client_socket, self.mock_socket)
        self.assertEqual(self.handler.player_index, self.player_index)
        self.assertEqual(self.handler.logger, self.mock_logger)
        self.assertEqual(self.handler.state_manager, self.mock_state_manager)
        self.assertEqual(self.handler.user_id, self.user_id)
        self.assertEqual(self.handler.player_manager, self.mock_player_manager)
        self.assertEqual(self.handler.is_running, self.mock_is_running)

    def test_ready_with_character_sheet(self):
        """Test _ready method with character sheet setup."""
        # Assign fields first
        self.handler.client_socket = self.mock_socket
        self.handler.player_index = self.player_index
        self.handler.logger = self.mock_logger
        self.handler.state_manager = self.mock_state_manager
        self.handler.user_id = self.user_id
        self.handler.player_manager = self.mock_player_manager
        self.handler.is_running = self.mock_is_running

        # Create a mock character sheet
        mock_character_sheet = Mock()
        mock_character_sheet.set_character_data = Mock()
        self.handler.children["character_sheet"] = mock_character_sheet

        # Mock the get_character_data method on the state manager
        mock_character_data = Mock()
        self.mock_state_manager.get_character_data = Mock(
            return_value=mock_character_data
        )

        # Mock start_ingame_handling to avoid threading in test
        with patch.object(self.handler, "start_ingame_handling"):
            self.handler._ready()

        # Verify character data was set
        self.mock_state_manager.get_character_data.assert_called_with(self.player_index)
        mock_character_sheet.set_character_data.assert_called_with(mock_character_data)

        # Verify ready message was logged
        expected_msg = f"Player 0x{self.player_index:04X} ingame handler ready"
        self.mock_logger.info.assert_called_with(expected_msg)

    def test_start_ingame_handling_not_initialized(self):
        """Test starting ingame handling without proper initialization."""
        with self.assertRaises(RuntimeError) as context:
            self.handler.start_ingame_handling()

        self.assertIn("Player not properly initialized", str(context.exception))

    def test_start_ingame_handling_success(self):
        """Test successful start of ingame handling."""
        # Assign fields first
        self.handler.client_socket = self.mock_socket
        self.handler.player_index = self.player_index
        self.handler.logger = self.mock_logger
        self.handler.state_manager = self.mock_state_manager
        self.handler.user_id = self.user_id
        self.handler.player_manager = self.mock_player_manager
        self.handler.is_running = self.mock_is_running

        with patch("threading.Thread") as mock_thread_class:
            mock_thread = Mock()
            mock_thread_class.return_value = mock_thread

            self.handler.start_ingame_handling()

            # Verify thread was created and started
            mock_thread_class.assert_called_once_with(
                target=self.handler._handle_ingame_communication, daemon=True
            )
            mock_thread.start.assert_called_once()
            self.assertEqual(self.handler.client_thread, mock_thread)

    def test_send_data_success(self):
        """Test successful data sending."""
        self.handler.client_socket = self.mock_socket
        self.handler.player_index = self.player_index
        self.handler.logger = self.mock_logger

        test_data = b"test data"
        result = self.handler.send_data(test_data)

        self.assertTrue(result)
        self.assertIn(test_data, self.mock_socket.sent_data)

    def test_send_data_no_socket(self):
        """Test sending data when no socket is available."""
        self.handler.client_socket = None

        test_data = b"test data"
        result = self.handler.send_data(test_data)

        self.assertFalse(result)

    def test_send_data_socket_error(self):
        """Test sending data when socket raises an error."""
        self.handler.client_socket = self.mock_socket
        self.handler.player_index = self.player_index
        self.handler.logger = self.mock_logger

        # Make socket raise an exception
        self.mock_socket.close()

        test_data = b"test data"
        result = self.handler.send_data(test_data)

        self.assertFalse(result)
        self.mock_logger.log_exception.assert_called()

    @patch("server.utils.socket_utils.server_socket_utils.receive_packet_with_logging")
    def test_handle_ingame_communication_success(self, mock_receive):
        """Test successful ingame communication handling."""
        # Assign fields directly
        self.handler.client_socket = self.mock_socket
        self.handler.player_index = self.player_index
        self.handler.logger = self.mock_logger
        self.handler.state_manager = self.mock_state_manager
        self.handler.user_id = self.user_id
        self.handler.player_manager = self.mock_player_manager
        self.handler.is_running = self.mock_is_running

        # Setup mock to return data once then None
        test_data = b"\x2a\x01\x02\x03"
        mock_receive.side_effect = [test_data, None]

        # Run the communication handler
        self.handler._handle_ingame_communication()

        # Verify logging
        expected_msg = (
            f"Player 0x{self.player_index:04X} sent ingame packet: "
            f"{test_data.hex().upper()}"
        )
        self.mock_logger.debug.assert_any_call(expected_msg)

    def test_stop_handling_no_thread(self):
        """Test stopping handling when no thread exists."""
        self.handler.logger = self.mock_logger
        self.handler.player_index = self.player_index

        # Should not raise any exceptions
        self.handler.stop_handling()

    def test_stop_handling_with_thread(self):
        """Test stopping handling with active thread."""
        self.handler.logger = self.mock_logger
        self.handler.player_index = self.player_index

        # Create a mock thread
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        self.handler.client_thread = mock_thread

        self.handler.stop_handling()

        # Verify thread was joined
        mock_thread.join.assert_called_with(timeout=5.0)

    def test_cleanup_player_once(self):
        """Test that cleanup only runs once."""
        self.handler.client_socket = self.mock_socket
        self.handler.player_index = self.player_index
        self.handler.logger = self.mock_logger
        self.handler.player_manager = self.mock_player_manager
        self.handler.state_manager = self.mock_state_manager

        # Call cleanup twice
        self.handler._cleanup_player()
        self.handler._cleanup_player()

        # Verify cleanup methods were only called once
        self.mock_player_manager.release_index.assert_called_once_with(
            self.player_index
        )
        self.mock_state_manager.cleanup_client.assert_called_once_with(
            self.player_index
        )
        self.assertTrue(self.handler._cleanup_done)

    def test_cleanup_player_socket_close_error(self):
        """Test cleanup when socket close raises an error."""
        # Create a socket that raises an error on close
        mock_socket = Mock()
        mock_socket.close.side_effect = Exception("Close error")

        self.handler.client_socket = mock_socket
        self.handler.player_index = self.player_index
        self.handler.logger = self.mock_logger
        self.handler.player_manager = self.mock_player_manager
        self.handler.state_manager = self.mock_state_manager

        # Should not raise an exception
        self.handler._cleanup_player()

        # Verify other cleanup still happened
        self.mock_player_manager.release_index.assert_called_with(self.player_index)
        self.mock_state_manager.cleanup_client.assert_called_with(self.player_index)

    def test_ready_method(self):
        """Test the _ready method doesn't raise errors."""
        # Mock start_ingame_handling to avoid threading in test
        with patch.object(self.handler, "start_ingame_handling"):
            # Should not raise any exceptions
            self.handler._ready()

    def test_process_method(self):
        """Test the _process method doesn't raise errors."""
        # Should not raise any exceptions
        self.handler._process(0.016)

    def test_exit_tree_method(self):
        """Test the _exit_tree method calls stop_handling."""
        self.handler.logger = self.mock_logger
        self.handler.player_index = self.player_index

        with patch.object(self.handler, "stop_handling") as mock_stop:
            self.handler._exit_tree()
            mock_stop.assert_called_once()

    @patch("time.time")
    @patch("server.utils.socket_utils.server_socket_utils.receive_packet_with_logging")
    def test_timer_based_packets(self, mock_receive, mock_time):
        """Test that timer-based packets are sent at correct intervals."""
        # Assign fields first
        self.handler.client_socket = self.mock_socket
        self.handler.player_index = self.player_index
        self.handler.logger = self.mock_logger
        self.handler.state_manager = self.mock_state_manager
        self.handler.user_id = self.user_id
        self.handler.player_manager = self.mock_player_manager

        # Mock time progression
        time_values = [0, 1, 2, 3, 4, 5, 6, 7, 14, 15, 16]
        mock_time.side_effect = time_values

        # Mock receive to return None (no data) to break the loop
        mock_receive.return_value = None

        # Mock is_running to return True a few times then False
        call_count = 0

        def mock_is_running():
            nonlocal call_count
            call_count += 1
            return call_count <= len(time_values) - 1

        self.handler.is_running = mock_is_running

        # Mock send_data to track what was sent
        sent_packets = []

        def mock_send_data(data):
            sent_packets.append(data)
            return True

        with patch.object(self.handler, "send_data", side_effect=mock_send_data):
            self.handler._handle_ingame_communication()

        # Verify packets were sent at correct times
        # Should have sent TRANSMISSION_END_PACKET at time 3
        # Should have sent 6s keepalive at time 6
        # Should have sent 15s keepalive at time 15
        self.assertGreater(len(sent_packets), 0)

        # Verify we have the expected packet types
        from server.packets import server_packets

        transmission_end_packets = [
            p for p in sent_packets if p == server_packets.TRANSMISSION_END_PACKET
        ]
        self.assertGreater(len(transmission_end_packets), 0)

    def test_handle_client_ping(self):
        """Test handling of client ping packets."""
        # Assign fields first
        self.handler.client_socket = self.mock_socket
        self.handler.player_index = self.player_index
        self.handler.logger = self.mock_logger

        # Create a mock ping packet (starting with 0x26, at least 30 bytes)
        ping_data = bytearray(35)
        ping_data[0] = 0x26  # Ping identifier
        # Fill bytes 9-30 with test data
        for i in range(9, 30):
            ping_data[i] = i - 9  # Fill with 0, 1, 2, ... 20

        # Test the ping handler
        result = self.handler.handle_client_ping(bytes(ping_data))

        # Should return True for successful handling
        self.assertTrue(result)

        # Should have sent a response
        self.assertEqual(len(self.mock_socket.sent_data), 1)

        # Check that ping state was updated
        self.assertTrue(self.handler.ping_should_xor_top_bit)  # Should toggle
        self.assertGreater(self.handler.ping_counter, 0)  # Should increment

    def test_handle_client_ping_short_packet(self):
        """Test handling of short ping packets."""
        self.handler.client_socket = self.mock_socket
        self.handler.player_index = self.player_index
        self.handler.logger = self.mock_logger

        # Create a short packet (less than 30 bytes)
        short_data = bytes([0x26] + [0] * 20)  # Only 21 bytes

        result = self.handler.handle_client_ping(short_data)

        # Should return False for short packets
        self.assertFalse(result)

        # Should not have sent anything
        self.assertEqual(len(self.mock_socket.sent_data), 0)

    @patch("server.utils.socket_utils.server_socket_utils.receive_packet_with_logging")
    def test_ingame_communication_with_ping(self, mock_receive):
        """Test that ping packets are handled in the communication loop."""
        # Assign fields first
        self.handler.client_socket = self.mock_socket
        self.handler.player_index = self.player_index
        self.handler.logger = self.mock_logger
        self.handler.state_manager = self.mock_state_manager
        self.handler.user_id = self.user_id
        self.handler.player_manager = self.mock_player_manager

        # Create a ping packet
        ping_data = bytearray(35)
        ping_data[0] = 0x26
        for i in range(9, 30):
            ping_data[i] = i - 9

        # Mock is_running to return True once then False
        call_count = 0

        def mock_is_running():
            nonlocal call_count
            call_count += 1
            return call_count <= 1

        self.handler.is_running = mock_is_running

        # Mock the receive function to return ping data once, then None
        mock_receive.side_effect = [bytes(ping_data), None]

        self.handler._handle_ingame_communication()

        # Should have sent a pong response
        self.assertGreater(len(self.mock_socket.sent_data), 0)


if __name__ == "__main__":
    unittest.main()
