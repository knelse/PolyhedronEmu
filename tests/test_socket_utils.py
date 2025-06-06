import socket
import unittest
from unittest.mock import Mock
from utils.socket_utils import SocketUtils


class TestSocketUtils(unittest.TestCase):
    """Test cases for SocketUtils class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_socket = Mock(spec=socket.socket)
        self.mock_logger = Mock()
        self.player_index = 0x5000
        self.test_data = b"test packet data"

    def test_send_success_with_custom_message(self):
        """Test successful send with custom message."""
        custom_message = "Custom log message"

        result = SocketUtils.send(
            self.mock_socket,
            self.test_data,
            self.player_index,
            self.mock_logger,
            custom_message,
        )

        self.assertTrue(result)
        self.mock_socket.send.assert_called_once_with(self.test_data)
        self.mock_logger.debug.assert_called_once_with(custom_message)
        self.mock_logger.log_exception.assert_not_called()

    def test_send_success_with_default_message(self):
        """Test successful send with default message format."""
        result = SocketUtils.send(
            self.mock_socket, self.test_data, self.player_index, self.mock_logger
        )

        self.assertTrue(result)
        self.mock_socket.send.assert_called_once_with(self.test_data)

        expected_message = (
            f"Sent packet to player 0x{self.player_index:04X}: "
            f"{self.test_data.hex().upper()}"
        )
        self.mock_logger.debug.assert_called_once_with(expected_message)
        self.mock_logger.log_exception.assert_not_called()

    def test_send_socket_exception(self):
        """Test send with socket exception."""
        # Mock socket.send to raise an exception
        test_exception = ConnectionResetError("Connection reset by peer")
        self.mock_socket.send.side_effect = test_exception

        result = SocketUtils.send(
            self.mock_socket, self.test_data, self.player_index, self.mock_logger
        )

        self.assertFalse(result)
        self.mock_socket.send.assert_called_once_with(self.test_data)

        expected_error_msg = (
            f"Failed to send packet to player 0x{self.player_index:04X}: "
            f"{self.test_data.hex().upper()}"
        )
        self.mock_logger.log_exception.assert_called_once_with(
            expected_error_msg, test_exception
        )
        self.mock_logger.debug.assert_not_called()

    def test_send_generic_exception(self):
        """Test send with generic exception."""
        test_exception = Exception("Generic error")
        self.mock_socket.send.side_effect = test_exception

        result = SocketUtils.send(
            self.mock_socket,
            self.test_data,
            self.player_index,
            self.mock_logger,
            "Custom message that won't be logged due to error",
        )

        self.assertFalse(result)
        self.mock_socket.send.assert_called_once_with(self.test_data)

        expected_error_msg = (
            f"Failed to send packet to player 0x{self.player_index:04X}: "
            f"{self.test_data.hex().upper()}"
        )
        self.mock_logger.log_exception.assert_called_once_with(
            expected_error_msg, test_exception
        )
        self.mock_logger.debug.assert_not_called()

    def test_send_empty_data(self):
        """Test send with empty data."""
        empty_data = b""

        result = SocketUtils.send(
            self.mock_socket, empty_data, self.player_index, self.mock_logger
        )

        self.assertTrue(result)
        self.mock_socket.send.assert_called_once_with(empty_data)

        expected_message = f"Sent packet to player 0x{self.player_index:04X}: "
        self.mock_logger.debug.assert_called_once_with(expected_message)

    def test_send_large_data(self):
        """Test send with large data packet."""
        large_data = b"x" * 1024  # 1KB of data

        result = SocketUtils.send(
            self.mock_socket, large_data, self.player_index, self.mock_logger
        )

        self.assertTrue(result)
        self.mock_socket.send.assert_called_once_with(large_data)

        expected_message = (
            f"Sent packet to player 0x{self.player_index:04X}: "
            f"{large_data.hex().upper()}"
        )
        self.mock_logger.debug.assert_called_once_with(expected_message)


if __name__ == "__main__":
    unittest.main()
