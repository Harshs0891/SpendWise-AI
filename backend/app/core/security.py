
from pwdlib import PasswordHash


# Create a reusable password hasher using Argon2.
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using Argon2.

    Returns:
        str: The generated password hash.
    """
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a plaintext password against its stored hash.

    Returns:
        bool: True if the password matches, otherwise False.
    """
    return password_hash.verify(plain_password, hashed_password)
