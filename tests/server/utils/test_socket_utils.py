import socket
import unittest
from unittest.mock import Mock
from server.utils.socket_utils import server_socket_utils


class TestServerSocketUtils(unittest.TestCase):
    """Test cases for server_socket_utils class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_socket = Mock(spec=socket.socket)
        self.mock_logger = Mock()
        self.player_index = 0x5000
        self.test_data = b"test packet data"

    def test_send_packet_with_logging_success_with_custom_message(self):
        """Test successful send with custom message."""
        custom_message = "Custom log message"

        result = server_socket_utils.send_packet_with_logging(
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

    def test_send_packet_with_logging_connection_reset_error(self):
        """Test send with ConnectionResetError."""
        test_exception = ConnectionResetError("Connection reset by peer")
        self.mock_socket.send.side_effect = test_exception

        result = server_socket_utils.send_packet_with_logging(
            self.mock_socket,
            self.test_data,
            self.player_index,
            self.mock_logger,
            "Success message",
            "test packet send",
        )

        self.assertFalse(result)
        self.mock_socket.send.assert_called_once_with(self.test_data)

        expected_error_msg = (
            f"Player 0x{self.player_index:04X} connection reset during test packet send"
        )
        self.mock_logger.info.assert_called_once_with(expected_error_msg)
        self.mock_logger.debug.assert_not_called()

    def test_send_packet_with_logging_broken_pipe_error(self):
        """Test send with BrokenPipeError."""
        test_exception = BrokenPipeError("Broken pipe")
        self.mock_socket.send.side_effect = test_exception

        result = server_socket_utils.send_packet_with_logging(
            self.mock_socket,
            self.test_data,
            self.player_index,
            self.mock_logger,
            "Success message",
            "test packet send",
        )

        self.assertFalse(result)
        self.mock_socket.send.assert_called_once_with(self.test_data)

        expected_error_msg = (
            f"Player 0x{self.player_index:04X} broken pipe during test packet send"
        )
        self.mock_logger.info.assert_called_once_with(expected_error_msg)
        self.mock_logger.debug.assert_not_called()

    def test_send_packet_with_logging_socket_error(self):
        """Test send with socket error."""
        test_exception = socket.error("Socket error")
        self.mock_socket.send.side_effect = test_exception

        result = server_socket_utils.send_packet_with_logging(
            self.mock_socket,
            self.test_data,
            self.player_index,
            self.mock_logger,
            "Success message",
            "test packet send",
        )

        self.assertFalse(result)
        self.mock_socket.send.assert_called_once_with(self.test_data)

        expected_error_msg = (
            f"Socket error sending test packet send to player "
            f"0x{self.player_index:04X}"
        )
        self.mock_logger.log_exception.assert_called_once_with(
            expected_error_msg, test_exception
        )
        self.mock_logger.debug.assert_not_called()

    def test_send_packet_with_logging_generic_exception(self):
        """Test send with generic exception."""
        test_exception = Exception("Generic error")
        self.mock_socket.send.side_effect = test_exception

        result = server_socket_utils.send_packet_with_logging(
            self.mock_socket,
            self.test_data,
            self.player_index,
            self.mock_logger,
            "Success message",
            "test packet send",
        )

        self.assertFalse(result)
        self.mock_socket.send.assert_called_once_with(self.test_data)

        expected_error_msg = (
            f"Unexpected error sending test packet send to player "
            f"0x{self.player_index:04X}"
        )
        self.mock_logger.log_exception.assert_called_once_with(
            expected_error_msg, test_exception
        )
        self.mock_logger.debug.assert_not_called()

    def test_receive_packet_with_logging_success(self):
        """Test successful packet receive."""
        test_data = b"received data"
        self.mock_socket.recv.return_value = test_data

        result = server_socket_utils.receive_packet_with_logging(
            self.mock_socket,
            self.player_index,
            self.mock_logger,
        )

        self.assertEqual(result, test_data)
        self.mock_socket.recv.assert_called_once_with(1024)

        expected_message = (
            f"Received from player 0x{self.player_index:04X}: {test_data.hex().upper()}"
        )
        self.mock_logger.debug.assert_called_once_with(expected_message)

    def test_receive_packet_with_logging_disconnection(self):
        """Test receive when client disconnects (empty data)."""
        self.mock_socket.recv.return_value = b""

        result = server_socket_utils.receive_packet_with_logging(
            self.mock_socket,
            self.player_index,
            self.mock_logger,
        )

        self.assertIsNone(result)
        expected_message = (
            f"Player 0x{self.player_index:04X} disconnected during packet receive"
        )
        self.mock_logger.info.assert_called_once_with(expected_message)

    def test_receive_packet_with_logging_timeout(self):
        """Test receive with timeout."""
        self.mock_socket.recv.side_effect = socket.timeout("Timeout")

        result = server_socket_utils.receive_packet_with_logging(
            self.mock_socket,
            self.player_index,
            self.mock_logger,
            timeout=5.0,
        )

        self.assertIsNone(result)
        self.mock_socket.settimeout.assert_called_once_with(5.0)

    def test_send_packet_or_cleanup_success(self):
        """Test send_packet_or_cleanup with successful send."""
        cleanup_callback = Mock()

        result = server_socket_utils.send_packet_or_cleanup(
            self.mock_socket,
            self.test_data,
            self.player_index,
            self.mock_logger,
            "Success message",
            cleanup_callback,
        )

        self.assertTrue(result)
        self.mock_socket.send.assert_called_once_with(self.test_data)
        cleanup_callback.assert_not_called()

    def test_send_packet_or_cleanup_failure(self):
        """Test send_packet_or_cleanup with failed send."""
        test_exception = ConnectionResetError("Connection reset")
        self.mock_socket.send.side_effect = test_exception
        cleanup_callback = Mock()

        result = server_socket_utils.send_packet_or_cleanup(
            self.mock_socket,
            self.test_data,
            self.player_index,
            self.mock_logger,
            "Success message",
            cleanup_callback,
        )

        self.assertFalse(result)
        self.mock_socket.send.assert_called_once_with(self.test_data)
        cleanup_callback.assert_called_once_with(self.mock_socket, self.player_index)


if __name__ == "__main__":
    unittest.main()
