"""
user authentication models for MongoDB storage.
"""

import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from server.auth_config import default_auth_config as auth_config


@dataclass
class polyhedron_user:
    """polyhedron_user model for authentication."""

    login: str
    password_hash: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    login_count: int = 0
    is_active: bool = True

    def __post_init__(self):
        """Validate user data after initialization."""
        if not self.login:
            raise ValueError("Login cannot be empty")
        if not self.password_hash:
            raise ValueError("Password hash cannot be empty")
        if len(self.login) > auth_config.max_login_length:
            raise ValueError(f"Login too long (max {auth_config.max_login_length})")

    @classmethod
    def create_polyhedron_user(cls, login: str, password: str) -> "polyhedron_user":
        """Create a new polyhedron_user with hashed password."""
        if len(password) < auth_config.min_password_length:
            raise ValueError(
                f"Password too short (min {auth_config.min_password_length})"
            )
        if len(password) > auth_config.max_password_length:
            raise ValueError(
                f"Password too long (max {auth_config.max_password_length})"
            )

        password_hash = cls.hash_password(password)
        return cls(login=login, password_hash=password_hash)

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password with padding and configured algorithm."""
        padded_password = password + auth_config.password_padding

        if auth_config.hash_algorithm == "sha256":
            return hashlib.sha256(padded_password.encode("utf-8")).hexdigest().upper()
        elif auth_config.hash_algorithm == "sha512":
            return hashlib.sha512(padded_password.encode("utf-8")).hexdigest().upper()
        elif auth_config.hash_algorithm == "md5":
            return hashlib.md5(padded_password.encode("utf-8")).hexdigest().upper()
        else:
            raise ValueError(
                f"Unsupported hash algorithm: {auth_config.hash_algorithm}"
            )

    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        return self.password_hash == self.hash_password(password)

    def update_login_info(self) -> None:
        """Update login information when user logs in."""
        self.last_login = datetime.now(timezone.utc)
        self.login_count += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary for MongoDB storage."""
        return {
            "login": self.login,
            "password_hash": self.password_hash,
            "created_at": self.created_at,
            "last_login": self.last_login,
            "login_count": self.login_count,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "polyhedron_user":
        """Create polyhedron_user from dictionary loaded from MongoDB."""
        return cls(
            login=data["login"],
            password_hash=data["password_hash"],
            created_at=data["created_at"],
            last_login=data.get("last_login"),
            login_count=data.get("login_count", 0),
            is_active=data.get("is_active", True),
        )


class polyhedron_user_database:
    """Database manager for user authentication."""

    def __init__(
        self,
        connection_string: str = "mongodb://localhost:27017/",
        database_name: str = "polyhedron_emu",
    ):
        self.client = MongoClient(connection_string)
        self.db: Database = self.client[database_name]
        self.users: Collection = self.db.users
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        """Ensure required indexes exist."""
        try:
            # Create unique index on login (case-insensitive if configured)
            if auth_config.case_sensitive_login:
                self.users.create_index("login", unique=True)
            else:
                # Create case-insensitive unique index
                self.users.create_index(
                    [("login", ASCENDING)],
                    unique=True,
                    collation={"locale": "en", "strength": 2},
                )

            # Index for active users
            self.users.create_index("is_active")

            # Index for created_at for analytics
            self.users.create_index("created_at")

        except Exception as e:
            print(f"Warning: Failed to create indexes: {e}")

    def normalize_login(self, login: str) -> str:
        """Normalize login based on case sensitivity setting."""
        return login if auth_config.case_sensitive_login else login.lower()

    def create_polyhedron_user(
        self, login: str, password: str
    ) -> tuple[bool, str, Optional["polyhedron_user"]]:
        """
        Create a new polyhedron_user.

        Returns:
            tuple[bool, str, Optional[polyhedron_user]]: (success, message, polyhedron_user)
        """
        try:
            normalized_login = self.normalize_login(login)

            # Check if polyhedron_user already exists
            if self.get_polyhedron_user(normalized_login) is not None:
                return False, "polyhedron_user already exists", None

            polyhedron_user_obj = polyhedron_user.create_polyhedron_user(
                normalized_login, password
            )

            # Insert into database
            result = self.users.insert_one(polyhedron_user_obj.to_dict())
            if result.inserted_id:
                return True, "polyhedron_user created successfully", polyhedron_user_obj
            else:
                return False, "Failed to create polyhedron_user", None

        except DuplicateKeyError:
            return False, "polyhedron_user already exists", None
        except ValueError as e:
            return False, str(e), None
        except Exception as e:
            return False, f"Database error: {e}", None

    def get_polyhedron_user(self, login: str) -> Optional["polyhedron_user"]:
        """Get polyhedron_user by login."""
        try:
            normalized_login = self.normalize_login(login)

            if auth_config.case_sensitive_login:
                user_data = self.users.find_one(
                    {"login": normalized_login, "is_active": True}
                )
            else:
                user_data = self.users.find_one(
                    {"login": normalized_login, "is_active": True},
                    collation={"locale": "en", "strength": 2},
                )

            if user_data:
                return polyhedron_user.from_dict(user_data)
            return None

        except Exception as e:
            print(f"Error getting user {login}: {e}")
            return None

    def authenticate_polyhedron_user(
        self, login: str, password: str
    ) -> tuple[bool, str, Optional["polyhedron_user"]]:
        """
        Authenticate a polyhedron_user with login and password.

        Returns:
            tuple[bool, str, Optional[polyhedron_user]]: (success, message, polyhedron_user)
        """
        try:
            polyhedron_user_obj = self.get_polyhedron_user(login)
            if polyhedron_user_obj is None:
                return False, "polyhedron_user not found", None

            if not polyhedron_user_obj.verify_password(password):
                return False, "Invalid password", None

            # Update login info
            polyhedron_user_obj.update_login_info()
            self.update_polyhedron_user_login_info(polyhedron_user_obj)

            return True, "Authentication successful", polyhedron_user_obj

        except Exception as e:
            return False, f"Authentication error: {e}", None

    def update_polyhedron_user_login_info(
        self, polyhedron_user_obj: "polyhedron_user"
    ) -> bool:
        """Update polyhedron_user's login information in database."""
        try:
            result = self.users.update_one(
                {"login": polyhedron_user_obj.login},
                {
                    "$set": {
                        "last_login": polyhedron_user_obj.last_login,
                        "login_count": polyhedron_user_obj.login_count,
                    }
                },
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating user login info: {e}")
            return False

    def deactivate_polyhedron_user(self, login: str) -> bool:
        """Deactivate a polyhedron_user (soft delete)."""
        try:
            normalized_login = self.normalize_login(login)
            result = self.users.update_one(
                {"login": normalized_login}, {"$set": {"is_active": False}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error deactivating user {login}: {e}")
            return False

    def get_polyhedron_user_count(self) -> int:
        """Get total number of active polyhedron_users."""
        try:
            return self.users.count_documents({"is_active": True})
        except Exception as e:
            print(f"Error getting user count: {e}")
            return 0

    def get_recent_polyhedron_users(self, limit: int = 10) -> List["polyhedron_user"]:
        """Get recently created users."""
        try:
            cursor = (
                self.users.find({"is_active": True}).sort("created_at", -1).limit(limit)
            )

            return [polyhedron_user.from_dict(doc) for doc in cursor]
        except Exception as e:
            print(f"Error getting recent users: {e}")
            return []

    def close(self) -> None:
        """Close database connection."""
        try:
            self.client.close()
        except Exception as e:
            print(f"Error closing database connection: {e}")
