import sys
import unittest
from unittest.mock import MagicMock, patch
from server.enter_game_world_pipeline.authentication_handler import (
    authentication_handler,
)
from server.enter_game_world_pipeline.exceptions import authentication_exception
from server.logger import server_logger
from server.client_state_manager import client_state_manager

sys.modules["py4godot"] = MagicMock()
sys.modules["py4godot.classes"] = MagicMock()
sys.modules["py4godot.classes.Node3D"] = MagicMock()


class MockAuthResult:
    """Mock authentication result."""

    def __init__(
        self,
        success=True,
        is_new_user=False,
        user_login="testuser",
        login_count=1,
        message="Success",
    ):
        self.success = success
        self.is_new_user = is_new_user
        self.message = message
        if success:
            self.user = MockUser(user_login, login_count)

    @property
    def is_new_polyhedron_user(self) -> bool:
        """Alias for is_new_user to maintain compatibility."""
        return self.is_new_user


class MockUser:
    """Mock user object."""

    def __init__(self, login, login_count):
        self.login = login
        self.login_count = login_count


class TestAuthenticationHandler(unittest.TestCase):
    """Test authentication_handler functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = MagicMock(spec=server_logger)
        self.mock_state_manager = MagicMock(spec=client_state_manager)
        self.mock_socket = MagicMock()
        self.player_index = 0x5000
        self.login_packet = b"test_login_packet"

    def test_process_authentication_success_existing_user(self):
        """Test successful authentication for existing user."""
        auth_result = MockAuthResult(success=True, is_new_user=False, login_count=5)

        patch_path = (
            "server.enter_game_world_pipeline.authentication_handler."
            "get_encrypted_login_and_password"
        )

        with patch(patch_path, return_value=(b"login", b"password")):
            with patch(
                "server.enter_game_world_pipeline.authentication_handler."
                "decrypt_login_and_password"
            ) as mock_decrypt:
                mock_decrypt.return_value = ("testuser", "testpass")
                with patch(
                    "server.enter_game_world_pipeline.authentication_handler."
                    "auth_pipeline.authenticate_or_register"
                ) as mock_auth:
                    mock_auth.return_value = auth_result
                    # Should not raise an exception
                    authentication_handler.process_authentication(
                        self.login_packet,
                        self.player_index,
                        self.mock_socket,
                        self.mock_logger,
                        self.mock_state_manager,
                    )

                    self.mock_state_manager.set_user_id.assert_called_once_with(
                        self.player_index, "testuser"
                    )
                    self.mock_logger.info.assert_called()

    def test_process_authentication_success_new_user(self):
        """Test successful authentication for new user."""
        auth_result = MockAuthResult(success=True, is_new_user=True)

        patch_path = (
            "server.enter_game_world_pipeline.authentication_handler."
            "get_encrypted_login_and_password"
        )

        with patch(patch_path, return_value=(b"login", b"password")):
            with patch(
                "server.enter_game_world_pipeline.authentication_handler."
                "decrypt_login_and_password"
            ) as mock_decrypt:
                mock_decrypt.return_value = ("newuser", "newpass")
                with patch(
                    "server.enter_game_world_pipeline.authentication_handler."
                    "auth_pipeline.authenticate_or_register"
                ) as mock_auth:
                    mock_auth.return_value = auth_result
                    # Should not raise an exception
                    authentication_handler.process_authentication(
                        self.login_packet,
                        self.player_index,
                        self.mock_socket,
                        self.mock_logger,
                        self.mock_state_manager,
                    )

                    self.mock_state_manager.set_user_id.assert_called_once_with(
                        self.player_index, "testuser"
                    )
                    self.mock_logger.info.assert_called()

    def test_process_authentication_failure(self):
        """Test authentication failure."""
        auth_result = MockAuthResult(success=False, message="Invalid credentials")

        patch_path = (
            "server.enter_game_world_pipeline.authentication_handler."
            "get_encrypted_login_and_password"
        )
        with patch(patch_path, return_value=(b"login", b"password")):
            with patch(
                "server.enter_game_world_pipeline.authentication_handler."
                "decrypt_login_and_password"
            ) as mock_decrypt:
                mock_decrypt.return_value = ("testuser", "wrongpass")
                with patch(
                    "server.enter_game_world_pipeline.authentication_handler."
                    "auth_pipeline.authenticate_or_register"
                ) as mock_auth:
                    mock_auth.return_value = auth_result
                    with patch(
                        "server.enter_game_world_pipeline.authentication_handler."
                        "auth_pipeline.get_authentication_failure_packet"
                    ) as mock_failure:
                        mock_failure.return_value = b"\x01\x02\x03\x04"
                        with patch(
                            "server.enter_game_world_pipeline.authentication_handler."
                            "server_socket_utils.send_packet_with_logging"
                        ) as mock_send:
                            mock_send.return_value = True
                            with self.assertRaises(authentication_exception) as cm:
                                authentication_handler.process_authentication(
                                    self.login_packet,
                                    self.player_index,
                                    self.mock_socket,
                                    self.mock_logger,
                                    self.mock_state_manager,
                                )

                            self.assertIn("Authentication failed", str(cm.exception))
                            self.assertIn("Invalid credentials", str(cm.exception))

    def test_process_authentication_exception(self):
        """Test exception during authentication processing."""
        with patch(
            "server.enter_game_world_pipeline.authentication_handler."
            "get_encrypted_login_and_password"
        ) as mock_encrypt:
            mock_encrypt.side_effect = Exception("Test exception")
            with self.assertRaises(authentication_exception) as cm:
                authentication_handler.process_authentication(
                    self.login_packet,
                    self.player_index,
                    self.mock_socket,
                    self.mock_logger,
                    self.mock_state_manager,
                )

            self.assertIn("Failed to decode login data", str(cm.exception))
            self.assertIn("Test exception", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
