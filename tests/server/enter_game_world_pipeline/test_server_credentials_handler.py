import sys
import unittest
from unittest.mock import MagicMock, patch
from server.enter_game_world_pipeline.server_credentials_handler import (
    server_credentials_handler,
)
from server.enter_game_world_pipeline.exceptions import server_credentials_exception
from server.logger import server_logger
from server.packets import server_packets

sys.modules["py4godot"] = MagicMock()
sys.modules["py4godot.classes"] = MagicMock()
sys.modules["py4godot.classes.Node3D"] = MagicMock()


class TestServerCredentialsHandler(unittest.TestCase):
    """Test ServerCredentialsHandler functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = MagicMock(spec=server_logger)
        self.player_index = 0x5000
        self.mock_socket = MagicMock()

    @patch("server.packets.encode_ingame_time")
    @patch(
        "server.enter_game_world_pipeline.server_credentials_handler."
        "server_socket_utils.send_packet_or_cleanup"
    )
    def test_send_init_and_credentials_success(
        self, mock_send_packet, mock_encode_time
    ):
        """Test successful init and credentials sending."""
        mock_send_packet.return_value = True
        # Mock the time encoding to return a fixed value for deterministic testing
        mock_encode_time.return_value = bytes([0x43, 0xD7, 0x43, 0x50, 0xF4])

        # Should not raise an exception
        server_credentials_handler.send_init_and_credentials(
            self.mock_socket,
            self.player_index,
            self.mock_logger,
        )

        # Verify both packets were sent
        self.assertEqual(mock_send_packet.call_count, 2)

        # Verify the actual packets sent are the expected ones
        first_call = mock_send_packet.call_args_list[0]
        second_call = mock_send_packet.call_args_list[1]

        # First call should be INIT_PACKET
        self.assertEqual(first_call[0][1], server_packets.INIT_PACKET)

        # Second call should be server credentials
        # Generate expected credentials with the same mocked time
        expected_creds = server_packets.get_server_credentials(self.player_index)
        self.assertEqual(second_call[0][1], expected_creds)

    @patch(
        "server.enter_game_world_pipeline.server_credentials_handler."
        "server_socket_utils.send_packet_or_cleanup"
    )
    def test_send_init_and_credentials_init_packet_fails(self, mock_send_packet):
        """Test when init packet sending fails."""
        mock_send_packet.return_value = False

        with self.assertRaises(server_credentials_exception) as cm:
            server_credentials_handler.send_init_and_credentials(
                self.mock_socket,
                self.player_index,
                self.mock_logger,
            )

        self.assertIn("Failed to send init packet", str(cm.exception))
        # Should only be called once since first packet failed
        self.assertEqual(mock_send_packet.call_count, 1)

    @patch(
        "server.enter_game_world_pipeline.server_credentials_handler."
        "server_socket_utils.send_packet_or_cleanup"
    )
    def test_send_init_and_credentials_credentials_packet_fails(self, mock_send_packet):
        """Test when credentials packet sending fails."""
        mock_send_packet.side_effect = [True, False]  # First succeeds, second fails

        with self.assertRaises(server_credentials_exception) as cm:
            server_credentials_handler.send_init_and_credentials(
                self.mock_socket,
                self.player_index,
                self.mock_logger,
            )

        self.assertIn("Failed to send credentials packet", str(cm.exception))
        # Should be called twice
        self.assertEqual(mock_send_packet.call_count, 2)


if __name__ == "__main__":
    unittest.main()
