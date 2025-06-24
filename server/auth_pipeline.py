"""
Authorization pipeline for user authentication and registration.
"""

from enum import Enum
from typing import Optional
from data_models.user_models import User, UserDatabase
from server.auth_config import auth_config


class AuthResultType(Enum):
    """Enumeration of authentication result types."""

    SUCCESS = "success"
    INVALID_PASSWORD = "invalid_password"
    REGISTRATION_SUCCESS = "registration_success"
    REGISTRATION_FAILED = "registration_failed"
    VALIDATION_ERROR = "validation_error"
    DATABASE_ERROR = "database_error"
    UNKNOWN_ERROR = "unknown_error"


class AuthResult:
    """Result of an authentication attempt."""

    def __init__(
        self,
        success: bool,
        result_type: AuthResultType,
        user: Optional[User] = None,
        is_new_user: bool = False,
        details: Optional[str] = None,
    ):
        self.success = success
        self.result_type = result_type
        self.user = user
        self.is_new_user = is_new_user
        self.details = details

    @property
    def message(self) -> str:
        """Get human-readable message for the result."""
        messages = {
            AuthResultType.SUCCESS: "Authentication successful",
            AuthResultType.INVALID_PASSWORD: "Invalid password",
            AuthResultType.REGISTRATION_SUCCESS: "Registration successful",
            AuthResultType.REGISTRATION_FAILED: "Registration failed",
            AuthResultType.VALIDATION_ERROR: "Validation error",
            AuthResultType.DATABASE_ERROR: "Database error",
            AuthResultType.UNKNOWN_ERROR: "Unknown error",
        }
        base_message = messages.get(self.result_type, "Unknown result")
        if self.details:
            return f"{base_message}: {self.details}"
        return base_message

    def __str__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        user_info = f" (user: {self.user.login})" if self.user else ""
        new_user_info = " [NEW USER]" if self.is_new_user else ""
        return f"Auth {status}: {self.result_type.value}{user_info}{new_user_info}"


class AuthorizationPipeline:
    """Main authorization pipeline for handling user authentication."""

    def __init__(
        self,
        connection_string: str = "mongodb://localhost:27017/",
        database_name: str = "polyhedron_emu",
    ):
        self.user_db = UserDatabase(connection_string, database_name)

    def authenticate_or_register(self, login: str, password: str) -> AuthResult:
        """
        Authenticate existing user or register new user.

        Args:
            login: User login from decrypt_login_and_password
            password: User password from decrypt_login_and_password

        Returns:
            AuthResult: Result of authentication/registration attempt
        """
        try:
            # Validate input
            if not login or not login.strip():
                return AuthResult(
                    False,
                    AuthResultType.VALIDATION_ERROR,
                    None,
                    False,
                    "Login cannot be empty",
                )

            if not password or not password.strip():
                return AuthResult(
                    False,
                    AuthResultType.VALIDATION_ERROR,
                    None,
                    False,
                    "Password cannot be empty",
                )

            login = login.strip()
            password = password.strip()

            # Check length limits
            if len(login) > auth_config.max_login_length:
                return AuthResult(
                    False,
                    AuthResultType.VALIDATION_ERROR,
                    None,
                    False,
                    f"Login too long (max {auth_config.max_login_length})",
                )

            if len(password) > auth_config.max_password_length:
                return AuthResult(
                    False,
                    AuthResultType.VALIDATION_ERROR,
                    None,
                    False,
                    f"Password too long (max {auth_config.max_password_length})",
                )

            if len(password) < auth_config.min_password_length:
                return AuthResult(
                    False,
                    AuthResultType.VALIDATION_ERROR,
                    None,
                    False,
                    f"Password too short (min {auth_config.min_password_length})",
                )

            # Try to authenticate existing user first
            auth_success, auth_message, user = self.user_db.authenticate_user(
                login, password
            )

            if auth_success and user:
                return AuthResult(True, AuthResultType.SUCCESS, user, False)

            # If user not found, try to register as new user
            if auth_message == "User not found":
                return self._register_new_user(login, password)

            # If user exists but password is wrong, return authentication failure
            return AuthResult(
                False, AuthResultType.INVALID_PASSWORD, None, False, auth_message
            )

        except Exception as e:
            return AuthResult(
                False,
                AuthResultType.DATABASE_ERROR,
                None,
                False,
                f"Authentication pipeline error: {e}",
            )

    def _register_new_user(self, login: str, password: str) -> AuthResult:
        """
        Register a new user.

        Args:
            login: User login
            password: User password

        Returns:
            AuthResult: Result of registration attempt
        """
        try:
            success, message, user = self.user_db.create_user(login, password)

            if success and user:
                # Update login info for new user
                user.update_login_info()
                self.user_db.update_user_login_info(user)
                return AuthResult(True, AuthResultType.REGISTRATION_SUCCESS, user, True)
            else:
                return AuthResult(
                    False,
                    AuthResultType.REGISTRATION_FAILED,
                    None,
                    False,
                    f"Registration failed: {message}",
                )

        except Exception as e:
            return AuthResult(
                False,
                AuthResultType.DATABASE_ERROR,
                None,
                False,
                f"Registration error: {e}",
            )

    def get_authentication_failure_packet(self, player_index: int) -> bytes:
        """
        Create a connection error packet to send when authentication fails.

        Args:
            player_index: The player's index

        Returns:
            bytes: Connection error packet data to send to client
        """
        from server.packets import ServerPackets

        return ServerPackets.connection_error(player_index)

    def get_user_stats(self) -> dict:
        """Get user statistics."""
        try:
            return {
                "total_users": self.user_db.get_user_count(),
                "recent_users": len(self.user_db.get_recent_users(10)),
            }
        except Exception as e:
            return {"error": str(e)}

    def close(self) -> None:
        """Close database connections."""
        self.user_db.close()


# Global authorization pipeline instance
auth_pipeline = AuthorizationPipeline()
