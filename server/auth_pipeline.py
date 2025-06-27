"""
Authorization pipeline for user authentication and registration.
"""

from enum import Enum
from typing import Optional
from data_models.user_models import polyhedron_user, polyhedron_user_database
from server.auth_config import default_auth_config as auth_config


class auth_result_type(Enum):
    """Enumeration of authentication result types."""

    SUCCESS = "success"
    INVALID_PASSWORD = "invalid_password"
    REGISTRATION_SUCCESS = "registration_success"
    REGISTRATION_FAILED = "registration_failed"
    VALIDATION_ERROR = "validation_error"
    DATABASE_ERROR = "database_error"
    UNKNOWN_ERROR = "unknown_error"


class auth_result:
    """Result of an authentication attempt."""

    def __init__(
        self,
        success: bool,
        result_type: auth_result_type,
        polyhedron_user_obj: Optional[polyhedron_user] = None,
        is_new_polyhedron_user: bool = False,
        details: Optional[str] = None,
    ):
        self.success = success
        self.result_type = result_type
        self.user = polyhedron_user_obj
        self.is_new_user = is_new_polyhedron_user
        self.details = details

    @property
    def is_new_polyhedron_user(self) -> bool:
        """Alias for is_new_user to maintain compatibility."""
        return self.is_new_user

    @property
    def message(self) -> str:
        """Get human-readable message for the result."""
        messages = {
            auth_result_type.SUCCESS: "Authentication successful",
            auth_result_type.INVALID_PASSWORD: "Invalid password",
            auth_result_type.REGISTRATION_SUCCESS: "Registration successful",
            auth_result_type.REGISTRATION_FAILED: "Registration failed",
            auth_result_type.VALIDATION_ERROR: "Validation error",
            auth_result_type.DATABASE_ERROR: "Database error",
            auth_result_type.UNKNOWN_ERROR: "Unknown error",
        }
        base_message = messages.get(self.result_type, "Unknown result")
        if self.details:
            return f"{base_message}: {self.details}"
        return base_message

    def __str__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        user_info = f" (polyhedron_user: {self.user.login})" if self.user else ""
        new_user_info = " [NEW USER]" if self.is_new_user else ""
        return f"Auth {status}: {self.result_type.value}{user_info}{new_user_info}"


class authorization_pipeline:
    """Main authorization pipeline for handling user authentication."""

    def __init__(
        self,
        connection_string: str = "mongodb://localhost:27017/",
        database_name: str = "polyhedron_emu",
    ):
        self.user_db = polyhedron_user_database(connection_string, database_name)

    def authenticate_or_register(self, login: str, password: str) -> auth_result:
        """
        Authenticate existing user or register new user.

        Args:
            login: user login from decrypt_login_and_password
            password: user password from decrypt_login_and_password

        Returns:
            auth_result: Result of authentication/registration attempt
        """
        try:
            # Validate input
            if not login or not login.strip():
                return auth_result(
                    False,
                    auth_result_type.VALIDATION_ERROR,
                    None,
                    False,
                    "Login cannot be empty",
                )

            if not password or not password.strip():
                return auth_result(
                    False,
                    auth_result_type.VALIDATION_ERROR,
                    None,
                    False,
                    "Password cannot be empty",
                )

            login = login.strip()
            password = password.strip()

            # Check length limits
            if len(login) > auth_config.max_login_length:
                return auth_result(
                    False,
                    auth_result_type.VALIDATION_ERROR,
                    None,
                    False,
                    f"Login too long (max {auth_config.max_login_length})",
                )

            if len(password) > auth_config.max_password_length:
                return auth_result(
                    False,
                    auth_result_type.VALIDATION_ERROR,
                    None,
                    False,
                    f"Password too long (max {auth_config.max_password_length})",
                )

            if len(password) < auth_config.min_password_length:
                return auth_result(
                    False,
                    auth_result_type.VALIDATION_ERROR,
                    None,
                    False,
                    f"Password too short (min {auth_config.min_password_length})",
                )

            # Try to authenticate existing user first
            auth_success, auth_message, polyhedron_user_obj = (
                self.user_db.authenticate_polyhedron_user(login, password)
            )

            if auth_success and polyhedron_user_obj:
                return auth_result(
                    True, auth_result_type.SUCCESS, polyhedron_user_obj, False
                )

            # If user not found, try to register as new user
            if auth_message == "polyhedron_user not found":
                return self._register_new_user(login, password)

            # If user exists but password is wrong, return authentication failure
            return auth_result(
                False, auth_result_type.INVALID_PASSWORD, None, False, auth_message
            )

        except Exception as e:
            return auth_result(
                False,
                auth_result_type.DATABASE_ERROR,
                None,
                False,
                f"Authentication pipeline error: {e}",
            )

    def _register_new_user(self, login: str, password: str) -> auth_result:
        """
        Register a new user.

        Args:
            login: user login
            password: user password

        Returns:
            auth_result: Result of registration attempt
        """
        try:
            success, message, user = self.user_db.create_polyhedron_user(
                login, password
            )

            if success and user:
                # Update login info for new user
                user.update_login_info()
                self.user_db.update_polyhedron_user_login_info(user)
                return auth_result(
                    True, auth_result_type.REGISTRATION_SUCCESS, user, True
                )
            else:
                return auth_result(
                    False,
                    auth_result_type.REGISTRATION_FAILED,
                    None,
                    False,
                    f"Registration failed: {message}",
                )

        except Exception as e:
            return auth_result(
                False,
                auth_result_type.DATABASE_ERROR,
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
        from server.packets import server_packets

        return server_packets.connection_error(player_index)

    def get_user_stats(self) -> dict:
        """Get user statistics."""
        try:
            return {
                "total_users": self.user_db.get_polyhedron_user_count(),
                "recent_users": len(self.user_db.get_recent_polyhedron_users(10)),
            }
        except Exception as e:
            return {"error": str(e)}

    def close(self) -> None:
        """Close database connections."""
        self.user_db.close()


# Global authorization pipeline instance
auth_pipeline = authorization_pipeline()
