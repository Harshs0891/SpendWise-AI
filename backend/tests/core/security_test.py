from app.core.security import hash_password, verify_password


def test_hash_password_returns_non_plaintext_hash():
    password = "Correct-Horse-Battery-42"

    hashed = hash_password(password)

    assert hashed != password
    assert isinstance(hashed, str)
    assert hashed


def test_verify_password_accepts_matching_password():
    password = "Correct-Horse-Battery-42"

    assert verify_password(password, hash_password(password)) is True


def test_verify_password_rejects_wrong_password():
    hashed = hash_password("Correct-Horse-Battery-42")

    assert verify_password("wrong-password", hashed) is False
