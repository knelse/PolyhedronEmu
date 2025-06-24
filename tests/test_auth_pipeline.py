"""
Tests for the authorization pipeline.
"""

import unittest
from unittest.mock import Mock, patch
import tempfile
import os

from server.auth_pipeline import AuthorizationPipeline, AuthResult, AuthResultType
from data_models.user_models import User, UserDatabase
from server.auth_config import AuthConfig


class TestAuthResult(unittest.TestCase):
    """Test AuthResult class."""

    def test_auth_result_success(self):
        """Test successful auth result."""
        user = User("testuser", "hash123")
        result = AuthResult(True, AuthResultType.SUCCESS, user, False)

        self.assertTrue(result.success)
        self.assertEqual(result.message, "Authentication successful")
        self.assertEqual(result.user, user)
        self.assertFalse(result.is_new_user)

    def test_auth_result_failure(self):
        """Test failed auth result."""
        result = AuthResult(False, AuthResultType.INVALID_PASSWORD)

        self.assertFalse(result.success)
        self.assertEqual(result.message, "Invalid password")
        self.assertIsNone(result.user)
        self.assertFalse(result.is_new_user)

    def test_auth_result_str(self):
        """Test string representation."""
        user = User("testuser", "hash123")
        result = AuthResult(True, AuthResultType.REGISTRATION_SUCCESS, user, True)

        expected = "Auth SUCCESS: registration_success (user: testuser) [NEW USER]"
        self.assertEqual(str(result), expected)


class TestAuthorizationPipeline(unittest.TestCase):
    """Test AuthorizationPipeline class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary config for testing
        self.temp_config = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        self.temp_config.write('{"password_padding": "test_padding_"}')
        self.temp_config.close()

        # Mock the auth_config
        self.mock_config = Mock()
        self.mock_config.max_login_length = 50
        self.mock_config.max_password_length = 100
        self.mock_config.min_password_length = 3

        # Mock the UserDatabase
        self.mock_user_db = Mock(spec=UserDatabase)

        # Create pipeline with mocked database
        self.pipeline = AuthorizationPipeline()
        self.pipeline.user_db = self.mock_user_db

    def tearDown(self):
        """Clean up test fixtures."""
        try:
            os.unlink(self.temp_config.name)
        except OSError:
            pass

    @patch("server.auth_pipeline.auth_config")
    def test_authenticate_existing_user_success(self, mock_config):
        """Test successful authentication of existing user."""
        mock_config.max_login_length = 50
        mock_config.max_password_length = 100
        mock_config.min_password_length = 3

        # Mock user
        mock_user = Mock()
        mock_user.login = "testuser"
        mock_user.login_count = 5

        # Mock successful authentication
        self.mock_user_db.authenticate_user.return_value = (True, "Success", mock_user)

        result = self.pipeline.authenticate_or_register("testuser", "password123")

        self.assertTrue(result.success)
        self.assertEqual(result.message, "Authentication successful")
        self.assertEqual(result.user, mock_user)
        self.assertFalse(result.is_new_user)

        self.mock_user_db.authenticate_user.assert_called_once_with(
            "testuser", "password123"
        )

    @patch("server.auth_pipeline.auth_config")
    def test_authenticate_new_user_registration(self, mock_config):
        """Test registration of new user when authentication fails."""
        mock_config.max_login_length = 50
        mock_config.max_password_length = 100
        mock_config.min_password_length = 3

        # Mock user not found
        self.mock_user_db.authenticate_user.return_value = (
            False,
            "User not found",
            None,
        )

        # Mock successful registration
        mock_user = Mock()
        mock_user.login = "newuser"
        mock_user.update_login_info = Mock()
        self.mock_user_db.create_user.return_value = (True, "User created", mock_user)
        self.mock_user_db.update_user_login_info.return_value = True

        result = self.pipeline.authenticate_or_register("newuser", "password123")

        self.assertTrue(result.success)
        self.assertEqual(result.message, "Registration successful")
        self.assertEqual(result.user, mock_user)
        self.assertTrue(result.is_new_user)

        self.mock_user_db.authenticate_user.assert_called_once_with(
            "newuser", "password123"
        )
        self.mock_user_db.create_user.assert_called_once_with("newuser", "password123")
        mock_user.update_login_info.assert_called_once()
        self.mock_user_db.update_user_login_info.assert_called_once_with(mock_user)

    @patch("server.auth_pipeline.auth_config")
    def test_authenticate_wrong_password(self, mock_config):
        """Test authentication failure with wrong password."""
        mock_config.max_login_length = 50
        mock_config.max_password_length = 100
        mock_config.min_password_length = 3

        # Mock authentication failure
        self.mock_user_db.authenticate_user.return_value = (
            False,
            "Invalid password",
            None,
        )

        result = self.pipeline.authenticate_or_register("testuser", "wrongpassword")

        self.assertFalse(result.success)
        self.assertEqual(result.message, "Invalid password: Invalid password")
        self.assertIsNone(result.user)
        self.assertFalse(result.is_new_user)

    @patch("server.auth_pipeline.auth_config")
    def test_validate_empty_login(self, mock_config):
        """Test validation with empty login."""
        mock_config.max_login_length = 50
        mock_config.max_password_length = 100
        mock_config.min_password_length = 3

        result = self.pipeline.authenticate_or_register("", "password123")

        self.assertFalse(result.success)
        self.assertEqual(result.message, "Validation error: Login cannot be empty")

    @patch("server.auth_pipeline.auth_config")
    def test_validate_empty_password(self, mock_config):
        """Test validation with empty password."""
        mock_config.max_login_length = 50
        mock_config.max_password_length = 100
        mock_config.min_password_length = 3

        result = self.pipeline.authenticate_or_register("testuser", "")

        self.assertFalse(result.success)
        self.assertEqual(result.message, "Validation error: Password cannot be empty")

    @patch("server.auth_pipeline.auth_config")
    def test_validate_login_too_long(self, mock_config):
        """Test validation with login too long."""
        mock_config.max_login_length = 5
        mock_config.max_password_length = 100
        mock_config.min_password_length = 3

        result = self.pipeline.authenticate_or_register(
            "verylongusername", "password123"
        )

        self.assertFalse(result.success)
        self.assertEqual(result.message, "Validation error: Login too long (max 5)")

    @patch("server.auth_pipeline.auth_config")
    def test_validate_password_too_long(self, mock_config):
        """Test validation with password too long."""
        mock_config.max_login_length = 50
        mock_config.max_password_length = 5
        mock_config.min_password_length = 3

        result = self.pipeline.authenticate_or_register("testuser", "verylongpassword")

        self.assertFalse(result.success)
        self.assertEqual(result.message, "Validation error: Password too long (max 5)")

    @patch("server.auth_pipeline.auth_config")
    def test_validate_password_too_short(self, mock_config):
        """Test validation with password too short."""
        mock_config.max_login_length = 50
        mock_config.max_password_length = 100
        mock_config.min_password_length = 5

        result = self.pipeline.authenticate_or_register("testuser", "123")

        self.assertFalse(result.success)
        self.assertEqual(result.message, "Validation error: Password too short (min 5)")

    @patch("server.auth_pipeline.auth_config")
    def test_authenticate_exception_handling(self, mock_config):
        """Test exception handling in authentication."""
        mock_config.max_login_length = 50
        mock_config.max_password_length = 100
        mock_config.min_password_length = 3

        # Mock exception in authentication
        self.mock_user_db.authenticate_user.side_effect = Exception("Database error")

        result = self.pipeline.authenticate_or_register("testuser", "password123")

        self.assertFalse(result.success)
        self.assertEqual(
            result.message,
            "Database error: Authentication pipeline error: Database error",
        )

    def test_get_authentication_failure_packet(self):
        """Test authentication failure packet generation."""
        packet = self.pipeline.get_authentication_failure_packet(0x1234)

        self.assertIsInstance(packet, bytes)
        self.assertEqual(len(packet), 14)  # Connection error packet length
        self.assertEqual(packet[0], 0x0E)  # Packet length
        self.assertEqual(packet[1], 0x00)  # Packet length high byte
        self.assertEqual(packet[2:7], b"\x2c\x01\x00\x00\x04")  # Packet header
        self.assertEqual(packet[7], 0x12)  # Player index high byte
        self.assertEqual(packet[8], 0x34)  # Player index low byte
        self.assertEqual(packet[9:14], b"\x08\x40\xa0\x00\x00")  # Connection error code

    def test_get_user_stats_success(self):
        """Test getting user statistics."""
        self.mock_user_db.get_user_count.return_value = 42
        self.mock_user_db.get_recent_users.return_value = [Mock(), Mock(), Mock()]

        stats = self.pipeline.get_user_stats()

        self.assertEqual(stats["total_users"], 42)
        self.assertEqual(stats["recent_users"], 3)

    def test_get_user_stats_exception(self):
        """Test getting user statistics with exception."""
        self.mock_user_db.get_user_count.side_effect = Exception("Database error")

        stats = self.pipeline.get_user_stats()

        self.assertIn("error", stats)
        self.assertEqual(stats["error"], "Database error")

    def test_close(self):
        """Test closing the pipeline."""
        self.pipeline.close()
        self.mock_user_db.close.assert_called_once()

    def test_register_new_user_failure(self):
        """Test registration failure."""
        # Mock user not found
        self.mock_user_db.authenticate_user.return_value = (
            False,
            "User not found",
            None,
        )

        # Mock registration failure
        self.mock_user_db.create_user.return_value = (
            False,
            "Registration failed",
            None,
        )

        with patch("server.auth_pipeline.auth_config") as mock_config:
            mock_config.max_login_length = 50
            mock_config.max_password_length = 100
            mock_config.min_password_length = 3

            result = self.pipeline.authenticate_or_register("newuser", "password123")

        self.assertFalse(result.success)
        self.assertEqual(
            result.message,
            "Registration failed: Registration failed: Registration failed",
        )

    def test_register_new_user_exception(self):
        """Test registration exception handling."""
        # Mock user not found
        self.mock_user_db.authenticate_user.return_value = (
            False,
            "User not found",
            None,
        )

        # Mock registration exception
        self.mock_user_db.create_user.side_effect = Exception("Database error")

        with patch("server.auth_pipeline.auth_config") as mock_config:
            mock_config.max_login_length = 50
            mock_config.max_password_length = 100
            mock_config.min_password_length = 3

            result = self.pipeline.authenticate_or_register("newuser", "password123")

        self.assertFalse(result.success)
        self.assertEqual(
            result.message, "Database error: Registration error: Database error"
        )


class TestAuthConfigIntegration(unittest.TestCase):
    """Integration tests with AuthConfig."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary config file
        self.temp_config = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        self.temp_config.write(
            """{
            "password_padding": "test_padding_",
            "hash_algorithm": "sha256",
            "max_login_length": 20,
            "max_password_length": 50,
            "min_password_length": 5,
            "case_sensitive_login": true
        }"""
        )
        self.temp_config.close()

        # Create config instance
        self.config = AuthConfig(self.temp_config.name)

    def tearDown(self):
        """Clean up test fixtures."""
        try:
            os.unlink(self.temp_config.name)
        except OSError:
            pass

    def test_config_values(self):
        """Test configuration values are loaded correctly."""
        self.assertEqual(self.config.password_padding, "test_padding_")
        self.assertEqual(self.config.hash_algorithm, "sha256")
        self.assertEqual(self.config.max_login_length, 20)
        self.assertEqual(self.config.max_password_length, 50)
        self.assertEqual(self.config.min_password_length, 5)
        self.assertTrue(self.config.case_sensitive_login)


if __name__ == "__main__":
    unittest.main()
