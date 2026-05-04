"""
Authentication Service
Handles user authentication and authorization
"""

import hashlib
import secrets
from typing import Optional, Dict
from datetime import datetime, timedelta
from backend.models.auth import UserRole, User
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication and authorization service"""

    def __init__(self):
        # In production, use database and proper password hashing (bcrypt, argon2)
        # This is a mock implementation for demo purposes
        self.users = {
            # Checkers
            "checker1": {
                "password": self._hash_password("checker123"),
                "user_id": "CHK001",
                "username": "checker1",
                "role": UserRole.CHECKER,
                "full_name": "John Checker",
                "email": "checker1@bank.com",
                "active": True
            },
            "checker2": {
                "password": self._hash_password("checker123"),
                "user_id": "CHK002",
                "username": "checker2",
                "role": UserRole.CHECKER,
                "full_name": "Sarah Checker",
                "email": "checker2@bank.com",
                "active": True
            },

            # Account Holders
            "priya.sharma": {
                "password": self._hash_password("priya123"),
                "user_id": "USR001",
                "username": "priya.sharma",
                "role": UserRole.ACCOUNT_HOLDER,
                "customer_id": "C001",
                "full_name": "Priya Sharma",
                "email": "priya.sharma@email.com",
                "active": True
            },
            "rahul.kumar": {
                "password": self._hash_password("rahul123"),
                "user_id": "USR002",
                "username": "rahul.kumar",
                "role": UserRole.ACCOUNT_HOLDER,
                "customer_id": "C002",
                "full_name": "Rahul Kumar",
                "email": "rahul.kumar@email.com",
                "active": True
            },

            "tanvi": {
                "password": self._hash_password("tanvi123"),
                "user_id": "USR003",
                "username": "tanvi",
                "role": UserRole.ACCOUNT_HOLDER,
                "customer_id": "C003",
                "full_name": "Tanvi Dubey",
                "email": "tanvi.dubey@email.com",
                "active": True
            },

            # Staff
            "staff1": {
                "password": self._hash_password("staff123"),
                "user_id": "STAFF001",
                "username": "staff1",
                "role": UserRole.STAFF,
                "full_name": "Staff Member 1",
                "email": "staff1@bank.com",
                "active": True
            }
        }

        # Active sessions (token -> user_info)
        # In production, use Redis or database
        self.sessions = {}

        logger.info("AuthService initialized")

    def _hash_password(self, password: str) -> str:
        """Hash password (simple SHA256 for demo, use bcrypt in production)"""
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """
        Authenticate user with username and password.

        Returns:
            User info dict if successful, None otherwise
        """
        user = self.users.get(username)

        if not user:
            logger.warning(f"Login attempt for non-existent user: {username}")
            return None

        if not user.get("active", True):
            logger.warning(f"Login attempt for inactive user: {username}")
            return None

        password_hash = self._hash_password(password)
        if password_hash != user["password"]:
            logger.warning(f"Invalid password for user: {username}")
            return None

        # Generate session token
        token = secrets.token_urlsafe(32)

        # Store session
        self.sessions[token] = {
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user["role"],
            "customer_id": user.get("customer_id"),
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=8)
        }

        logger.info(f"User authenticated successfully: {username} (Role: {user['role']})")

        return {
            "token": token,
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user["role"],
            "customer_id": user.get("customer_id"),
            "full_name": user.get("full_name")
        }

    def validate_token(self, token: str) -> Optional[Dict]:
        """
        Validate session token.

        Returns:
            User info dict if token is valid, None otherwise
        """
        session = self.sessions.get(token)

        if not session:
            return None

        # Check if session expired
        if datetime.utcnow() > session["expires_at"]:
            del self.sessions[token]
            logger.info(f"Session expired for user: {session['username']}")
            return None

        return session

    def logout(self, token: str) -> bool:
        """
        Logout user and invalidate token.

        Returns:
            True if successful, False otherwise
        """
        if token in self.sessions:
            username = self.sessions[token]["username"]
            del self.sessions[token]
            logger.info(f"User logged out: {username}")
            return True
        return False

    def authorize(self, token: str, required_role: UserRole) -> bool:
        """
        Check if user has required role.

        Returns:
            True if authorized, False otherwise
        """
        session = self.validate_token(token)
        if not session:
            return False

        user_role = session["role"]

        # Admin has access to everything
        if user_role == UserRole.ADMIN:
            return True

        # Check specific role
        return user_role == required_role

    def get_user_info(self, username: str) -> Optional[User]:
        """Get user information"""
        user_data = self.users.get(username)
        if not user_data:
            return None

        return User(
            user_id=user_data["user_id"],
            username=user_data["username"],
            role=user_data["role"],
            customer_id=user_data.get("customer_id"),
            full_name=user_data.get("full_name"),
            email=user_data.get("email"),
            active=user_data.get("active", True)
        )

    def update_user_by_customer_id(self, customer_id: str, field_name: str, new_value: str) -> bool:
        """Sync an approved change-request field onto the auth user record.

        Maps change-request field names to auth-user fields so the Users tab
        stays consistent with RPS after a checker approval.
        """
        field_map = {
            "legal_name": "full_name",
            "contact_email": "email",
        }
        target = field_map.get(field_name)
        if not target:
            return False

        for user in self.users.values():
            if user.get("customer_id") == customer_id:
                user[target] = new_value
                logger.info(f"Auth user synced: {user['username']}.{target} -> {new_value!r}")
                return True
        return False

    def get_all_users(self):
        """Get all users (without passwords)"""
        result = []
        for username, data in self.users.items():
            result.append({
                "user_id": data["user_id"],
                "username": data["username"],
                "role": data["role"].value if hasattr(data["role"], 'value') else data["role"],
                "full_name": data.get("full_name"),
                "email": data.get("email"),
                "customer_id": data.get("customer_id"),
                "active": data.get("active", True)
            })
        return result

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        user = self.users.get(username)
        if not user:
            return False

        old_password_hash = self._hash_password(old_password)
        if old_password_hash != user["password"]:
            logger.warning(f"Invalid old password for user: {username}")
            return False

        user["password"] = self._hash_password(new_password)
        logger.info(f"Password changed for user: {username}")
        return True


# Singleton instance
_auth_service = None


def get_auth_service() -> AuthService:
    """Get or create singleton auth service instance"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
