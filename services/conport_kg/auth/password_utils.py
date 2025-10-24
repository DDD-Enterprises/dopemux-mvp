#!/usr/bin/env python3
"""
ConPort-KG Password Security Utilities
Phase 1 Week 1 Day 1

Secure password hashing using Argon2id with breach detection.
Password strength validation with configurable requirements.
"""

import hashlib
import re
import secrets
from typing import Optional

import httpx
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError


class PasswordValidationError(Exception):
    """Raised when password doesn't meet strength requirements"""

    pass


class PasswordManager:
    """
    Secure password management using Argon2id hashing.

    Features:
    - Argon2id hashing (memory-hard, resistant to GPU attacks)
    - Password strength validation (configurable requirements)
    - Breach detection via HaveIBeenPwned API (k-anonymity)
    - Reset token generation

    Security:
    - Argon2id winner of Password Hashing Competition
    - OWASP recommended parameters
    - k-anonymity prevents password exposure to HIBP
    """

    # Password strength requirements (OWASP-compliant)
    MIN_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    def __init__(self):
        """
        Initialize password manager with Argon2id hasher.

        Parameters based on OWASP recommendations (2024):
        - time_cost=2: 2 iterations
        - memory_cost=65536: 64 MB memory
        - parallelism=4: 4 parallel threads
        """
        self.argon2 = PasswordHasher(
            time_cost=2,  # Iterations
            memory_cost=65536,  # 64 MB (OWASP minimum)
            parallelism=4,  # 4 threads (balance security/performance)
            hash_len=32,  # 32 bytes output
            salt_len=16,  # 16 bytes salt
        )

    def hash_password(self, password: str) -> str:
        """
        Hash password using Argon2id.

        Format: argon2id$v=19$m=65536,t=2,p=4$<salt>$<hash>

        Args:
            password: Plaintext password to hash

        Returns:
            Argon2id hash string

        Raises:
            PasswordValidationError: If password is weak

        Example:
            hashed = manager.hash_password("SecurePassword123!")
            # Returns: argon2id$v=19$m=65536,t=2,p=4$...
        """
        # Validate strength first
        self.validate_password_strength(password)

        # Hash with Argon2id
        argon2_hash = self.argon2.hash(password)

        return argon2_hash

    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify password against Argon2id hash.

        Timing-safe comparison (constant time to prevent timing attacks).

        Args:
            password: Plaintext password to verify
            hashed: Argon2id hash to check against

        Returns:
            True if password matches, False otherwise

        Example:
            is_valid = manager.verify_password("UserPassword", stored_hash)
        """
        try:
            # Verify with Argon2id (raises exception if mismatch)
            self.argon2.verify(hashed, password)

            # Check if rehashing needed (parameters changed)
            if self.argon2.check_needs_rehash(hashed):
                # Note: Caller should rehash password and update database
                pass

            return True

        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

    def validate_password_strength(self, password: str) -> None:
        """
        Validate password meets strength requirements.

        Requirements (OWASP-based):
        - Minimum 12 characters
        - At least 1 uppercase letter (A-Z)
        - At least 1 lowercase letter (a-z)
        - At least 1 digit (0-9)
        - At least 1 special character (!@#$%^&*...)

        Args:
            password: Password to validate

        Raises:
            PasswordValidationError: If password doesn't meet requirements

        Example:
            manager.validate_password_strength("Short1!")
            # Raises: PasswordValidationError("Password too short...")
        """
        errors = []

        # Length check
        if len(password) < self.MIN_LENGTH:
            errors.append(
                f"Password must be at least {self.MIN_LENGTH} characters long"
            )

        # Uppercase check
        if self.REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")

        # Lowercase check
        if self.REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")

        # Digit check
        if self.REQUIRE_DIGIT and not re.search(r"\d", password):
            errors.append("Password must contain at least one digit")

        # Special character check
        if self.REQUIRE_SPECIAL:
            if not any(char in self.SPECIAL_CHARS for char in password):
                errors.append(
                    f"Password must contain at least one special character ({self.SPECIAL_CHARS})"
                )

        # Common password patterns (additional security)
        common_patterns = [
            r"^password",  # Starts with "password"
            r"^admin",  # Starts with "admin"
            r"12345",  # Contains sequential numbers
            r"qwerty",  # Keyboard pattern
        ]

        for pattern in common_patterns:
            if re.search(pattern, password, re.IGNORECASE):
                errors.append(
                    f"Password contains common pattern ('{pattern}') and is easily guessable"
                )

        # Raise if any errors
        if errors:
            raise PasswordValidationError(". ".join(errors))

    async def check_password_breach(self, password: str) -> bool:
        """
        Check if password appears in HaveIBeenPwned breach database.

        Uses k-anonymity model:
        1. SHA-1 hash password
        2. Send first 5 characters to HIBP API
        3. Receive list of matching hashes
        4. Check locally if full hash is in list

        This prevents sending the actual password or full hash to HIBP.

        Args:
            password: Password to check

        Returns:
            True if breached (found in database), False if safe

        Example:
            is_breached = await manager.check_password_breach("password123")
            if is_breached:
                raise PasswordValidationError("Password found in breach database")

        API: https://haveibeenpwned.com/API/v3#PwnedPasswords
        """
        # SHA-1 hash of password (HIBP uses SHA-1)
        sha1_hash = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()

        # Split: first 5 chars (prefix) and rest (suffix)
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]

        # Query HIBP API with prefix only
        api_url = f"https://api.pwnedpasswords.com/range/{prefix}"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(api_url)

                if response.status_code != 200:
                    # If API fails, don't block user (availability over strict security)
                    return False

                # Parse response (format: "SUFFIX:COUNT\n...")
                hashes = response.text.splitlines()

                for line in hashes:
                    hash_suffix, count = line.split(":")
                    if hash_suffix == suffix:
                        # Password found in breach database
                        return True

                # Not found - password is safe
                return False

        except (httpx.HTTPError, httpx.TimeoutException, Exception):
            # Network error or any other failure - don't block user (availability over strict security)
            return False

    def generate_password_reset_token(self, user_id: int) -> str:
        """
        Generate secure password reset token.

        Uses cryptographically secure random bytes.
        Token should be stored in database with expiry (1 hour typical).

        Args:
            user_id: User ID for token binding

        Returns:
            Secure random token (32 bytes hex = 64 characters)

        Example:
            token = manager.generate_password_reset_token(123)
            # Store: password_reset_tokens(user_id=123, token_hash=sha256(token), expires=now+1hour)
        """
        # Generate 32 random bytes (256 bits)
        random_bytes = secrets.token_bytes(32)

        # Convert to hex string (64 characters)
        token = random_bytes.hex()

        return token

    def hash_reset_token(self, token: str) -> str:
        """
        Hash password reset token for database storage.

        Store the hash (not the token itself) to prevent theft if database compromised.

        Args:
            token: Reset token from generate_password_reset_token()

        Returns:
            SHA256 hash of token
        """
        return hashlib.sha256(token.encode()).hexdigest()

    def check_needs_rehash(self, hashed: str) -> bool:
        """
        Check if password hash needs to be updated.

        Returns True if hashing parameters have changed (e.g., increased
        memory_cost for better security).

        Args:
            hashed: Existing Argon2id hash

        Returns:
            True if rehashing recommended, False otherwise

        Usage:
            if manager.check_needs_rehash(user.password_hash):
                # User just logged in with valid password
                # Rehash with new parameters and update database
                user.password_hash = manager.hash_password(password)
        """
        try:
            return self.argon2.check_needs_rehash(hashed)
        except (InvalidHashError, ValueError):
            # Invalid hash format - definitely needs rehash
            return True


# Convenience function for FastAPI

def get_password_manager() -> PasswordManager:
    """
    FastAPI dependency for password manager.

    Usage:
        @app.post("/register")
        def register(password_manager: PasswordManager = Depends(get_password_manager)):
            hashed = password_manager.hash_password(password)
    """
    return PasswordManager()
