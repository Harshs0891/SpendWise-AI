from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import pytest

from app.core import jwt as jwt_module


def test_create_access_token_contains_user_subject_and_expiry(monkeypatch):
    monkeypatch.setattr(jwt_module.settings, "secret_key", "test-secret")
    monkeypatch.setattr(jwt_module.settings, "algorithm", "HS256")
    monkeypatch.setattr(jwt_module.settings, "access_token_expire_minutes", 30)
    user_id = uuid4()

    payload = jwt_module.decode_access_token(jwt_module.create_access_token(user_id))

    assert payload["sub"] == str(user_id)
    assert payload["exp"] > payload["iat"]


def test_decode_access_token_rejects_invalid_signature(monkeypatch):
    monkeypatch.setattr(jwt_module.settings, "secret_key", "test-secret")

    token = jwt.encode(
        {"sub": str(uuid4()), "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        "different-secret",
        algorithm="HS256",
    )

    with pytest.raises(jwt.InvalidSignatureError):
        jwt_module.decode_access_token(token)


def test_decode_access_token_rejects_expired_token(monkeypatch):
    monkeypatch.setattr(jwt_module.settings, "secret_key", "test-secret")
    token = jwt.encode(
        {"sub": str(uuid4()), "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        "test-secret",
        algorithm="HS256",
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        jwt_module.decode_access_token(token)
