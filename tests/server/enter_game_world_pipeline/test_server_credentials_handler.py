import sys
import unittest
from unittest.mock import MagicMock, patch
from server.enter_game_world_pipeline.server_credentials_handler import (
    ServerCredentialsHandler,
)
from server.enter_game_world_pipeline.exceptions import ServerCredentialsException
from server.logger import ServerLogger
from server.packets import ServerPackets

sys.modules["py4godot"] = MagicMock()
sys.modules["py4godot.classes"] = MagicMock()
sys.modules["py4godot.classes.Node3D"] = MagicMock()


class TestServerCredentialsHandler(unittest.TestCase):
    """Test ServerCredentialsHandler functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = MagicMock(spec=ServerLogger)
        self.player_index = 0x5000
        self.mock_socket = MagicMock()

    @patch(
        "server.enter_game_world_pipeline.server_credentials_handler."
        "ServerSocketUtils.send_packet_or_cleanup"
    )
    def test_send_init_and_credentials_success(self, mock_send_packet):
        """Test successful init and credentials sending."""
        mock_send_packet.return_value = True

        # Should not raise an exception
        ServerCredentialsHandler.send_init_and_credentials(
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
        self.assertEqual(first_call[0][1], ServerPackets.INIT_PACKET)

        # Second call should be server credentials
        expected_creds = ServerPackets.get_server_credentials(self.player_index)
        self.assertEqual(second_call[0][1], expected_creds)

    @patch(
        "server.enter_game_world_pipeline.server_credentials_handler."
        "ServerSocketUtils.send_packet_or_cleanup"
    )
    def test_send_init_and_credentials_init_packet_fails(self, mock_send_packet):
        """Test when init packet sending fails."""
        mock_send_packet.return_value = False

        with self.assertRaises(ServerCredentialsException) as cm:
            ServerCredentialsHandler.send_init_and_credentials(
                self.mock_socket,
                self.player_index,
                self.mock_logger,
            )

        self.assertIn("Failed to send init packet", str(cm.exception))
        # Should only be called once since first packet failed
        self.assertEqual(mock_send_packet.call_count, 1)

    @patch(
        "server.enter_game_world_pipeline.server_credentials_handler."
        "ServerSocketUtils.send_packet_or_cleanup"
    )
    def test_send_init_and_credentials_credentials_packet_fails(self, mock_send_packet):
        """Test when credentials packet sending fails."""
        mock_send_packet.side_effect = [True, False]  # First succeeds, second fails

        with self.assertRaises(ServerCredentialsException) as cm:
            ServerCredentialsHandler.send_init_and_credentials(
                self.mock_socket,
                self.player_index,
                self.mock_logger,
            )

        self.assertIn("Failed to send credentials packet", str(cm.exception))
        # Should be called twice
        self.assertEqual(mock_send_packet.call_count, 2)


if __name__ == "__main__":
    unittest.main()
