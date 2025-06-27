import sys
import socket
import unittest
from unittest.mock import MagicMock, patch
from server.enter_game_world_pipeline.login_handler import login_handler
from server.enter_game_world_pipeline.exceptions import login_exception
from server.logger import server_logger

sys.modules["py4godot"] = MagicMock()
sys.modules["py4godot.classes"] = MagicMock()
sys.modules["py4godot.classes.Node3D"] = MagicMock()


class TestLoginHandler(unittest.TestCase):
    """Test LoginHandler functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = MagicMock(spec=server_logger)
        self.player_index = 0x5000

    def test_wait_for_login_packet_success(self):
        """Test successful login packet reception."""
        mock_socket = MagicMock()
        valid_packet = b"valid_login_packet_data_longer_than_12_bytes"

        patch_path = (
            "server.enter_game_world_pipeline.login_handler."
            "server_socket_utils.receive_packet_with_logging"
        )
        with patch(patch_path, return_value=valid_packet):
            result = login_handler.wait_for_login_packet(
                mock_socket, self.player_index, self.mock_logger
            )

            self.assertEqual(result, valid_packet)
            self.mock_logger.info.assert_called_once()

    def test_wait_for_login_packet_too_short(self):
        """Test login packet that is too short."""
        mock_socket = MagicMock()
        short_packet = b"short"  # Less than 12 bytes
        valid_packet = b"valid_login_packet_data_longer_than_12_bytes"

        patch_path = (
            "server.enter_game_world_pipeline.login_handler."
            "server_socket_utils.receive_packet_with_logging"
        )
        with patch(
            patch_path, side_effect=[short_packet, valid_packet]
        ) as mock_receive:
            result = login_handler.wait_for_login_packet(
                mock_socket, self.player_index, self.mock_logger
            )

            self.assertEqual(result, valid_packet)
            self.assertEqual(mock_receive.call_count, 2)

    def test_wait_for_login_packet_no_data(self):
        """Test when no data is received."""
        mock_socket = MagicMock()

        patch_path = (
            "server.enter_game_world_pipeline.login_handler."
            "server_socket_utils.receive_packet_with_logging"
        )
        with patch(patch_path, return_value=None):
            with self.assertRaises(login_exception) as cm:
                login_handler.wait_for_login_packet(
                    mock_socket, self.player_index, self.mock_logger
                )

            self.assertIn("Failed to receive login packet", str(cm.exception))

    def test_wait_for_login_packet_timeout(self):
        """Test timeout during login packet wait."""
        mock_socket = MagicMock()

        patch_path = (
            "server.enter_game_world_pipeline.login_handler."
            "server_socket_utils.receive_packet_with_logging"
        )
        with patch(patch_path, side_effect=socket.timeout()):
            with self.assertRaises(login_exception) as cm:
                login_handler.wait_for_login_packet(
                    mock_socket, self.player_index, self.mock_logger
                )

            self.assertIn("Timeout waiting for login packet", str(cm.exception))

    def test_wait_for_login_packet_exception(self):
        """Test exception during login packet wait."""
        mock_socket = MagicMock()
        test_exception = Exception("Test exception")

        patch_path = (
            "server.enter_game_world_pipeline.login_handler."
            "server_socket_utils.receive_packet_with_logging"
        )
        with patch(patch_path, side_effect=test_exception):
            with self.assertRaises(login_exception) as cm:
                login_handler.wait_for_login_packet(
                    mock_socket, self.player_index, self.mock_logger
                )

            self.assertIn("Error waiting for login packet", str(cm.exception))
            self.assertIn("Test exception", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
