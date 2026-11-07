from uuid import uuid4

from app.models.user import User


def test_user_model_declares_expected_columns_and_defaults():
    columns = User.__table__.columns

    assert {"id", "email", "password_hash", "is_active", "created_at", "updated_at"} <= set(columns.keys())
    assert columns["email"].unique is True
    assert columns["email"].nullable is False
    assert columns["password_hash"].nullable is False
    assert columns["is_active"].default.arg is True


def test_user_model_can_be_instantiated():
    user = User(id=uuid4(), email="user@example.com", password_hash="hashed")

    assert user.email == "user@example.com"
    assert user.password_hash == "hashed"
